"""Reconnect monitoring/backup transport without launching experiments."""
import errno
import getpass
import json
import os
from pathlib import Path
import socket
import time

import paramiko


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def acquire_local_lock(path):
    path = Path(path)
    lock = path.open('a+b')
    if path.stat().st_size == 0:
        lock.write(b'0'); lock.flush()
    lock.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BaseException:
        lock.close()
        raise
    return lock


def is_network_error(error):
    if isinstance(error, (paramiko.AuthenticationException, paramiko.BadHostKeyException)):
        return False
    if isinstance(error, (EOFError, TimeoutError, ConnectionError, paramiko.SSHException)):
        return True
    codes = {errno.ECONNRESET, errno.ECONNABORTED, errno.ECONNREFUSED, errno.ENETDOWN,
             errno.EADDRNOTAVAIL,
             errno.ENETUNREACH, errno.EHOSTUNREACH, errno.ETIMEDOUT, errno.EPIPE}
    return isinstance(error, OSError) and (error.errno in codes or
        getattr(error, 'winerror', None) in {10049, 10050, 10051, 10053, 10054, 10060, 10061, 10065} or
        str(error).lower() in {'socket is closed', 'server connection dropped'})


class SSHRecovery:
    def __init__(self, connector, state_path, identity, *, sleep=time.sleep, now=time.time):
        self._connector = connector
        self._client = None
        self._sleep = sleep
        self._now = now
        self.state_path = Path(state_path)
        self.events_path = self.state_path.with_suffix('.events.jsonl')
        self.state = json.loads(self.state_path.read_text(encoding='utf-8')) if self.state_path.exists() else {}
        if self.state and self.state.get('identity') != identity:
            raise ValueError('Recovery state belongs to a different task/attempt/role')
        self.state.update(identity=identity)

    @classmethod
    def interactive(cls, state_path, identity):
        # Credential stays only in this process: reconnects never prompt again.
        password = os.environ.get('ASPIRE_SSH_PASSWORD') or getpass.getpass('SSH password: ')
        host = os.environ.get('ASPIRE_SSH_HOST')
        if not host:
            raise RuntimeError('Set ASPIRE_SSH_HOST for your own server')
        port = int(os.environ.get('ASPIRE_SSH_PORT', '22'))
        user = os.environ.get('ASPIRE_SSH_USER', 'root')
        known = Path(os.environ.get('ASPIRE_SSH_KNOWN_HOSTS', str(Path(__file__).with_name('aspire_ssh_knownhosts'))))
        if not known.is_file():
            raise RuntimeError('Existing pinned ASPIRE host key is required')

        def connector():
            client = paramiko.SSHClient()
            client.load_host_keys(str(known))
            if not client.get_host_keys().lookup(host if port == 22 else f'[{host}]:{port}'):
                raise RuntimeError('ASPIRE endpoint is missing from pinned host keys')
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(20)
            try:
                if os.name == 'nt':
                    interface = int(os.environ.get('ASPIRE_SSH_INTERFACE_INDEX', '0'))
                    if interface > 0:
                        connection.setsockopt(socket.IPPROTO_IP, 31, socket.htonl(interface))
                    # Keep the task-scoped interface, but let Windows select its
                    # current source address after DHCP/WLAN reconnection.
                    connection.bind(('0.0.0.0', 0))
                connection.connect((host, port))
                client.connect(host, port=port, username=user, password=password,
                               sock=connection, look_for_keys=False, allow_agent=False,
                               timeout=20, auth_timeout=20, banner_timeout=20)
                client.get_transport().set_keepalive(10)
                return client
            except BaseException:
                client.close()
                connection.close()
                raise
        return cls(connector, state_path, identity)

    def connection(self):
        if self._client is None:
            self._client = self._connector()
        return self._client

    def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def sftp(self):
        handle = self.connection().open_sftp()
        handle.get_channel().settimeout(30)
        return handle

    def _event(self, event, **fields):
        record = dict(event=event, time=self._now(), identity=self.state['identity'], **fields)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record) + '\n')
        print(json.dumps(record), flush=True)

    def run(self, operation, label, *, max_failures=None):
        """Retry only caller-approved, idempotent transport operations."""
        failures = 0
        snapshot_failures = 0
        while True:
            try:
                value = operation()
            except Exception as error:
                if isinstance(error, json.JSONDecodeError) and snapshot_failures < 3:
                    snapshot_failures += 1
                    self._event('incomplete_snapshot_retry', operation=label, attempt=snapshot_failures)
                    self._sleep(2)
                    continue
                if not is_network_error(error):
                    self.state.update(connection='requires_attention', error_type=type(error).__name__,
                                      operation=label, updated_at=self._now())
                    atomic_json(self.state_path, self.state)
                    self._event('requires_attention', operation=label, error_type=type(error).__name__)
                    raise
                self.close()
                failures += 1
                delay = min(30, 2 ** min(failures, 5))
                self.state.setdefault('outage_started_at', self._now())
                self.state.update(connection='offline', error_type=type(error).__name__,
                                  operation=label, consecutive_failures=failures,
                                  next_retry_seconds=delay, updated_at=self._now())
                atomic_json(self.state_path, self.state)
                self._event('disconnected', operation=label, error_type=type(error).__name__, retry_seconds=delay)
                if max_failures is not None and failures >= max_failures:
                    raise
                self._sleep(delay)
                continue
            recovered = self.state.pop('outage_started_at', None)
            self.state.pop('error_type', None)
            self.state.update(connection='online', operation=label, last_success_at=self._now(),
                              consecutive_failures=0, next_retry_seconds=0)
            atomic_json(self.state_path, self.state)
            if recovered is not None:
                self._event('recovered', operation=label, outage_seconds=max(0, self._now()-recovered))
            return value

    def python(self, code, *, timeout=30):
        """One bounded command; only run() decides whether it is safe to retry."""
        stdin, stdout, stderr = self.connection().exec_command('python3 -u -', timeout=timeout)
        channel = stdout.channel
        try:
            channel.settimeout(timeout)
            stdin.write(code)
            stdin.flush()
            channel.shutdown_write()
            output, errors = bytearray(), bytearray()
            deadline = time.monotonic() + timeout
            while True:
                if channel.recv_ready():
                    output.extend(channel.recv(65536))
                if channel.recv_stderr_ready():
                    errors.extend(channel.recv_stderr(65536))
                if channel.exit_status_ready() and not channel.recv_ready() and not channel.recv_stderr_ready():
                    break
                if not self.connection().get_transport().is_active():
                    raise EOFError('Monitoring transport disconnected')
                if time.monotonic() > deadline:
                    raise TimeoutError('Monitoring transport command timed out')
                time.sleep(.05)
            status = channel.recv_exit_status()
            if status == -1:
                raise EOFError('Remote command ended without an exit status')
            if status != 0:
                raise RuntimeError(f'Remote infrastructure command exited {status}')
            return output.decode('utf-8')
        finally:
            channel.close()

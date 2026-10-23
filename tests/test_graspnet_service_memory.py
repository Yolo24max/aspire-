"""Inference must share CUDA memory without retaining training graphs or cache."""
import asyncio

import numpy as np
import pytest

torch = pytest.importorskip("torch")
service = pytest.importorskip("cap_harness.providers.graspnet.service")


def test_grasp_prediction_disables_gradients_in_inference_thread(monkeypatch):
    class Estimator:
        def predict_scene_grasps(self, full, **kwargs):
            assert not torch.is_grad_enabled()
            assert torch.is_inference_mode_enabled()
            return {1: np.eye(4)[None]}, {1: np.array([0.9])}, {1: full[:1]}, {}

    monkeypatch.setattr(service, "_ESTIMATOR", Estimator())
    points = np.array([[0.1, 0.2, 0.3]])
    request = service.PlanPointCloudsRequest(pc_full_base64="", pc_segment_base64="")
    with torch.enable_grad():
        grasps, scores, contacts = service._predict(points, points, request)
        assert torch.is_grad_enabled()
    assert grasps.shape == (1, 4, 4)
    np.testing.assert_array_equal(scores, [0.9])
    np.testing.assert_array_equal(contacts, points)


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("cuda_available", [False, True])
def test_serialized_inference_releases_cuda_cache_even_after_error(monkeypatch, fail, cuda_available):
    calls = []
    monkeypatch.setattr(service.torch.cuda, "is_available", lambda: cuda_available)
    monkeypatch.setattr(service.torch.cuda, "empty_cache", lambda: calls.append("released"))

    def inference():
        if fail:
            raise RuntimeError("inference failed")
        return "prediction"

    async def run():
        if fail:
            with pytest.raises(RuntimeError, match="inference failed"):
                await service._run_serialized(inference)
        else:
            assert await service._run_serialized(inference) == "prediction"

    asyncio.run(run())
    assert calls == (["released"] if cuda_available else [])

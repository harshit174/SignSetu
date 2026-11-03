"""End-to-end model checks on the shipped ONNX model and held-out demo clips (no GPU, camera or dataset needed)."""
import numpy as np
import pytest

import isl_core
from conftest import ROOT


@pytest.fixture(scope="module")
def predictor():
    return isl_core.Predictor(str(ROOT / "models" / "signsetu_transformer.pt"), engine="onnx-cpu",
                              onnx_path=str(ROOT / "models" / "signsetu_transformer.onnx"))


@pytest.fixture(scope="module")
def demo():
    d = np.load(ROOT / "models" / "demo_samples.npz")
    return d["labels"].astype(int), d["base"].astype(np.float32)


def test_probabilities_are_a_distribution(predictor, demo):
    probs = predictor.predict(demo[1][0])
    assert probs.shape == (301,)
    assert np.isclose(probs.sum(), 1.0, atol=1e-3) and (probs >= 0).all()


def test_accuracy_on_held_out_clips(predictor, demo):
    labels, base = demo
    idx = np.random.default_rng(0).choice(len(labels), 120, replace=False)
    acc = np.mean([int(np.argmax(predictor.predict(base[i]))) == labels[i] for i in idx])
    assert acc >= 0.9, f"accuracy on held-out demo clips dropped to {acc:.2%}"


def test_segmenter_emits_one_segment_per_sign():
    seg, hand = isl_core.Segmenter(idle_end=10), np.ones(252, np.float32)
    out = [seg.update(hand if 5 <= t < 35 else np.zeros(252, np.float32), 5 <= t < 35) for t in range(80)]
    segments = [o for o in out if o is not None]
    assert len(segments) == 1 and segments[0].shape[1] == 252


def test_camera_backend_matches_the_os():
    class FakeCv2:
        CAP_DSHOW, CAP_AVFOUNDATION, CAP_V4L2 = 700, 1200, 200

    assert isl_core.camera_backend(FakeCv2, "win32") == 700
    assert isl_core.camera_backend(FakeCv2, "darwin") == 1200   # regression: macOS used to get V4L2 and never opened
    assert isl_core.camera_backend(FakeCv2, "linux") == 200


def test_early_commit_does_not_read_the_same_sign_twice():
    hand, rest = np.ones(252, np.float32), np.zeros(252, np.float32)
    seg, out = isl_core.Segmenter(idle_end=8), []
    for t in range(120):
        active = 5 <= t < 60                                     # one long sign
        o = seg.update(hand if active else rest, active)
        if o is None and seg.state == "SIGNING" and len(seg.buf) >= 14 and not out:
            o = seg.commit_early()                              # the classifier was sure after 14 frames
        if o is not None:
            out.append(o)
    assert len(out) == 1, "the tail of an early-committed sign must not start a second segment"


def test_latest_frame_reader_drops_stale_frames():
    import time

    class SlowCam:                       # produces numbered frames faster than the consumer reads them
        def __init__(self):
            self.i = 0

        def isOpened(self):
            return True

        def read(self):
            time.sleep(0.005)
            self.i += 1
            return True, self.i

        def release(self):
            pass

    cam = isl_core.LatestFrame(SlowCam())
    ok, first = cam.read()
    time.sleep(0.3)                      # consumer stalls: ~60 frames pile up on a naive reader
    ok2, second = cam.read()
    cam.release()
    assert ok and ok2 and second - first > 20, "must skip ahead to the newest frame, not replay the backlog"

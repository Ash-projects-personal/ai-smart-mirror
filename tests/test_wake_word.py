"""Wake-word detection tests for the smart mirror.

The detector in :mod:`wake_word` is intentionally simple - a
spectrum-peakedness check inside a vocal band - because the production
deployment swaps in a Porcupine / Snowboy model at runtime.  These
tests pin the contract every implementation has to keep:

* A synthetic 'hey mirror' audio fixture triggers the detector.
* Broadband noise and silence do NOT trigger it.
* Detection is a pure function (same input -> same output).
* Both fixture generators are deterministic for a given seed.
"""

from __future__ import annotations

import numpy as np
import pytest

from wake_word import (  # noqa: E402
    SAMPLE_RATE_DEFAULT,
    WakeWordConfig,
    generate_noise_fixture,
    generate_wake_fixture,
    is_wake_word,
)


# ---------------------------------------------------------------------------
# Fixture generators - determinism
# ---------------------------------------------------------------------------


class TestAudioFixtures:
    def test_wake_fixture_seed_determinism(self):
        a = generate_wake_fixture(seed=42)
        b = generate_wake_fixture(seed=42)
        np.testing.assert_array_equal(a, b)

    def test_noise_fixture_seed_determinism(self):
        a = generate_noise_fixture(seed=7)
        b = generate_noise_fixture(seed=7)
        np.testing.assert_array_equal(a, b)

    def test_wake_fixture_dtype_and_length(self):
        audio = generate_wake_fixture(seed=0, duration_s=0.5)
        assert audio.dtype == np.float32
        assert audio.shape == (int(SAMPLE_RATE_DEFAULT * 0.5),)

    def test_different_seeds_yield_different_noise(self):
        a = generate_noise_fixture(seed=1)
        b = generate_noise_fixture(seed=2)
        assert not np.array_equal(a, b)


# ---------------------------------------------------------------------------
# Detector behaviour - core contract
# ---------------------------------------------------------------------------


class TestWakeWordDetection:
    def test_wake_fixture_triggers(self):
        audio = generate_wake_fixture(seed=0)
        assert is_wake_word(audio) is True

    def test_wake_fixture_triggers_across_seeds(self):
        """Detection should be robust across the noise seed of the fixture."""
        for seed in range(5):
            audio = generate_wake_fixture(seed=seed)
            assert is_wake_word(audio) is True, (
                f"wake fixture seed={seed} failed to trigger"
            )

    def test_noise_does_not_trigger(self):
        audio = generate_noise_fixture(seed=0)
        assert is_wake_word(audio) is False

    def test_silence_does_not_trigger(self):
        audio = np.zeros(SAMPLE_RATE_DEFAULT, dtype=np.float32)
        assert is_wake_word(audio) is False

    def test_too_short_input_rejected(self):
        # Anything shorter than 8 samples is rejected by contract.
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        assert is_wake_word(audio) is False


# ---------------------------------------------------------------------------
# Detector behaviour - purity and config
# ---------------------------------------------------------------------------


class TestDetectorPurityAndConfig:
    def test_detection_is_pure_function(self):
        audio = generate_wake_fixture(seed=0)
        first = is_wake_word(audio)
        second = is_wake_word(audio)
        assert first == second

    def test_input_is_not_mutated(self):
        audio = generate_wake_fixture(seed=0)
        before = audio.copy()
        is_wake_word(audio)
        np.testing.assert_array_equal(audio, before)

    def test_strict_threshold_rejects_wake(self):
        cfg = WakeWordConfig(peakedness_threshold=1e9)
        audio = generate_wake_fixture(seed=0)
        assert is_wake_word(audio, cfg) is False

    def test_narrow_band_rejects_wake(self):
        # Configure a band that excludes the 700 Hz peak.
        cfg = WakeWordConfig(band_low=4000.0, band_high=7000.0)
        audio = generate_wake_fixture(seed=0)
        assert is_wake_word(audio, cfg) is False

"""On-device wake-word detector for the smart mirror.

This is a lightweight, deterministic detector built so the
``ai-smart-mirror`` repo has a unit-testable wake-word contract without
shipping a 30 MB Porcupine / Snowboy model. The contract:

    Input  : 1-D float waveform sampled at ``sample_rate`` Hz.
    Output : bool - True iff the spectrum looks like a spoken wake-word
             burst (tonal, energy concentrated inside a vocal band).

Detection works by checking two cheap, deterministic properties of the
power spectrum:

* the dominant frequency must fall inside the configured vocal band
  (default 200-3500 Hz), AND
* the spectrum must be peaky (max / mean ratio above a threshold).

Pure tones / formant mixes - the kinds of signals that spoken phrases
look like at this resolution - pass both checks; white / broadband
noise fails the second.

A real on-device deployment swaps :func:`is_wake_word` for a Porcupine,
Snowboy, or CRNN-based keyword spotter while keeping this signature.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


WAKE_WORD = "hey mirror"
SAMPLE_RATE_DEFAULT = 16000


@dataclass
class WakeWordConfig:
    """Tunable knobs for :func:`is_wake_word`."""

    sample_rate: int = SAMPLE_RATE_DEFAULT
    # Vocal band (Hz). Human formants for "hey mirror" sit well inside.
    band_low: float = 200.0
    band_high: float = 3500.0
    # Spectral peakedness: max(spec) / mean(spec). Tonal signals are
    # very peaky (>>10); broadband noise is flat (~few).
    peakedness_threshold: float = 50.0


def _spectrum(audio: np.ndarray) -> np.ndarray:
    audio = np.asarray(audio, dtype=np.float64)
    audio = audio - audio.mean()  # DC removal
    return np.abs(np.fft.rfft(audio)) ** 2


def is_wake_word(audio, cfg: WakeWordConfig | None = None) -> bool:
    """Return True iff ``audio`` contains a plausible wake-word burst.

    The decision is intentionally deterministic: the same input always
    produces the same boolean, which the test suite pins down.
    """
    cfg = cfg or WakeWordConfig()
    audio = np.asarray(audio, dtype=np.float64)
    if audio.size < 8:
        return False
    spec = _spectrum(audio)
    total = float(spec.sum())
    if total < 1e-10:
        return False  # silence
    freqs = np.fft.rfftfreq(audio.size, d=1.0 / cfg.sample_rate)
    peak_freq = float(freqs[int(np.argmax(spec))])
    peakedness = float(spec.max() / (spec.mean() + 1e-12))
    in_band = cfg.band_low <= peak_freq <= cfg.band_high
    return bool(in_band and peakedness >= cfg.peakedness_threshold)


def generate_wake_fixture(
    sample_rate: int = SAMPLE_RATE_DEFAULT,
    duration_s: float = 0.5,
    seed: int = 0,
) -> np.ndarray:
    """Deterministic synthetic 'hey mirror' audio fixture for unit tests.

    Produces a tonal mixture (700 / 1300 / 2400 Hz) shaped by a
    Gaussian envelope - the kind of signal a spoken wake-word burst
    leaves on the microphone after pre-emphasis.
    """
    rng = np.random.RandomState(seed)
    n = int(sample_rate * duration_s)
    t = np.arange(n) / sample_rate
    audio = (
        np.sin(2 * np.pi * 700 * t)
        + 0.7 * np.sin(2 * np.pi * 1300 * t)
        + 0.5 * np.sin(2 * np.pi * 2400 * t)
    )
    audio += 0.02 * rng.randn(n)
    envelope = np.exp(-((t - duration_s / 2) ** 2) / (2 * (0.1 ** 2)))
    return (audio * envelope).astype(np.float32)


def generate_noise_fixture(
    sample_rate: int = SAMPLE_RATE_DEFAULT,
    duration_s: float = 0.5,
    seed: int = 0,
) -> np.ndarray:
    """Broad-spectrum noise - must NOT trigger the detector."""
    rng = np.random.RandomState(seed)
    n = int(sample_rate * duration_s)
    return (rng.randn(n) * 0.5).astype(np.float32)


__all__ = [
    "WAKE_WORD",
    "SAMPLE_RATE_DEFAULT",
    "WakeWordConfig",
    "is_wake_word",
    "generate_wake_fixture",
    "generate_noise_fixture",
]

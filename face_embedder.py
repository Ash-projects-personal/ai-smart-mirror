"""Deterministic face-embedding stub for the smart mirror.

A production deployment swaps this for FaceNet / ArcFace.  For
portfolio + unit-test purposes the smart mirror exposes a tiny, fully
deterministic embedding so the suite can pin a hard guarantee:

    Same input image  ==>  byte-identical 128-dim embedding.

That property is the foundation of every downstream face-recognition
flow (gallery enrolment, threshold-based match, anti-spoof gating), so
locking it in protects the rest of the pipeline from silent
non-determinism in preprocessing or projection.
"""

from __future__ import annotations

import numpy as np


EMBEDDING_DIM = 128
PROJECTION_SEED = 20251101


def _preprocess(image: np.ndarray) -> np.ndarray:
    """Centre-crop, resize to 112x112, normalize to float32 in [0, 1]."""
    img = np.asarray(image)
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    if img.shape[-1] == 4:
        img = img[..., :3]  # drop alpha

    h, w = img.shape[:2]
    s = min(h, w)
    top = (h - s) // 2
    left = (w - s) // 2
    img = img[top : top + s, left : left + s]

    # Nearest-neighbour resize so we have no scipy dependency
    target = 112
    ys = np.linspace(0, img.shape[0] - 1, target).astype(np.int64)
    xs = np.linspace(0, img.shape[1] - 1, target).astype(np.int64)
    img = img[ys][:, xs]

    return img.astype(np.float32) / 255.0


def face_embedding(image: np.ndarray) -> np.ndarray:
    """Return a deterministic, L2-normalized 128-dim embedding.

    The embedding is built by projecting the preprocessed pixels
    through a fixed pseudo-random matrix (seeded with a module-level
    constant) and L2-normalizing the result.  Cosine similarity
    therefore reduces to a dot product, matching the contract real
    face-recognition backbones expose.
    """
    pre = _preprocess(image)
    rng = np.random.RandomState(PROJECTION_SEED)
    proj = (rng.randn(pre.size, EMBEDDING_DIM).astype(np.float32)
            / np.sqrt(pre.size))
    vec = pre.flatten() @ proj
    norm = float(np.linalg.norm(vec)) + 1e-12
    return (vec / norm).astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embeddings (both must be L2-normed)."""
    return float(np.dot(a, b))


__all__ = [
    "EMBEDDING_DIM",
    "PROJECTION_SEED",
    "face_embedding",
    "cosine_similarity",
]

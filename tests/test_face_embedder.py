"""Face-embedding determinism tests for the smart mirror.

The :mod:`face_embedder` module is the contract the rest of the
recognition pipeline (gallery enrolment, threshold-based match,
anti-spoof gating) leans on.  These tests pin three properties every
implementation must keep:

* **Determinism.**  Same input image -> byte-identical 128-dim vector.
* **Shape + dtype.**  ``(128,)`` float32, L2-normalized.
* **Discriminability.**  Different inputs must produce vectors that
  are not (numerically) identical on the unit sphere.
"""

from __future__ import annotations

import numpy as np
import pytest

from face_embedder import (  # noqa: E402
    EMBEDDING_DIM,
    cosine_similarity,
    face_embedding,
)


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------


def _fake_face(seed=0, size=(160, 160)):
    rng = np.random.RandomState(seed)
    return (rng.rand(size[0], size[1], 3) * 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Shape + dtype + normalization
# ---------------------------------------------------------------------------


class TestEmbeddingShape:
    def test_shape_and_dtype(self):
        emb = face_embedding(_fake_face(seed=0))
        assert emb.shape == (EMBEDDING_DIM,)
        assert emb.dtype == np.float32

    def test_embedding_is_l2_normalized(self):
        emb = face_embedding(_fake_face(seed=1))
        np.testing.assert_allclose(np.linalg.norm(emb), 1.0, atol=1e-5)

    def test_grayscale_input_supported(self):
        gray = (np.ones((140, 140), dtype=np.uint8) * 128)
        emb = face_embedding(gray)
        assert emb.shape == (EMBEDDING_DIM,)

    def test_rgba_input_supported(self):
        rgba = (np.random.RandomState(0).rand(120, 120, 4) * 255).astype(
            np.uint8
        )
        emb = face_embedding(rgba)
        assert emb.shape == (EMBEDDING_DIM,)
        np.testing.assert_allclose(np.linalg.norm(emb), 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Determinism - core property
# ---------------------------------------------------------------------------


class TestEmbeddingDeterminism:
    def test_same_image_byte_identical(self):
        img = _fake_face(seed=0)
        emb_a = face_embedding(img)
        emb_b = face_embedding(img)
        np.testing.assert_allclose(emb_a, emb_b, rtol=0, atol=0)

    def test_same_image_via_copy(self):
        """Copying the input must not change the embedding."""
        img = _fake_face(seed=2)
        emb_a = face_embedding(img)
        emb_b = face_embedding(img.copy())
        np.testing.assert_allclose(emb_a, emb_b, rtol=0, atol=0)

    def test_input_is_not_mutated(self):
        img = _fake_face(seed=3)
        before = img.copy()
        face_embedding(img)
        np.testing.assert_array_equal(img, before)


# ---------------------------------------------------------------------------
# Discriminability + cosine similarity contract
# ---------------------------------------------------------------------------


class TestEmbeddingDiscriminability:
    def test_different_images_differ(self):
        img_a = _fake_face(seed=0)
        img_b = _fake_face(seed=1)
        emb_a = face_embedding(img_a)
        emb_b = face_embedding(img_b)
        cos = cosine_similarity(emb_a, emb_b)
        # Different random faces shouldn't land on top of each other
        assert cos < 0.99, f"expected dissimilar inputs to differ, cos={cos}"

    def test_self_cosine_is_one(self):
        emb = face_embedding(_fake_face(seed=4))
        assert cosine_similarity(emb, emb) == pytest.approx(1.0, abs=1e-5)

    def test_cosine_is_symmetric(self):
        emb_a = face_embedding(_fake_face(seed=5))
        emb_b = face_embedding(_fake_face(seed=6))
        ab = cosine_similarity(emb_a, emb_b)
        ba = cosine_similarity(emb_b, emb_a)
        assert ab == pytest.approx(ba, abs=1e-7)

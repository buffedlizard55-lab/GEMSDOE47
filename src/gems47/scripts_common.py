"""Small helpers shared by the scripts."""
from __future__ import annotations
import numpy as np


def rank_u8_inplace(x: np.ndarray) -> np.ndarray:
    """Rank percentile 0..255 of a 1-D array (ties keep insertion order)."""
    x = np.asarray(x, np.float64)
    order = np.argsort(x, kind="stable")
    r = np.empty(x.size)
    r[order] = np.arange(x.size, dtype=np.float64)
    return np.clip(np.rint(r / max(x.size - 1, 1) * 255.0), 0, 255).astype(np.uint8)

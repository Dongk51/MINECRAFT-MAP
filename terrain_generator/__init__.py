"""
Shared utilities for terrain generation modules.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

from amulet.api.block import Block
from amulet.api.chunk import Chunk as AmuletChunk
from amulet.api.errors import ChunkDoesNotExist, ChunkLoadError

from block_replacer.core import DIMENSIONS, _parse_block  # re-export for consumers

__all__ = ["DIMENSIONS", "_parse_block", "Region", "chunk_range", "local_bounds", "get_or_create_chunk"]

logger = logging.getLogger(__name__)

# (x1, z1, x2, z2) in block coordinates — defines the working area
Region = Optional[Tuple[int, int, int, int]]


def chunk_range(level, dim_key: str, region: Region):
    """
    Yield (cx, cz) pairs to process.
    - region=None  → all existing chunks
    - region given → every chunk that overlaps the region (creates missing ones)
    """
    if region is None:
        yield from level.all_chunk_coords(dim_key)
        return

    x1, z1, x2, z2 = region
    cx1, cz1 = min(x1, x2) >> 4, min(z1, z2) >> 4
    cx2, cz2 = max(x1, x2) >> 4, max(z1, z2) >> 4
    for cx in range(cx1, cx2 + 1):
        for cz in range(cz1, cz2 + 1):
            yield cx, cz


def local_bounds(cx: int, cz: int, region: Region) -> tuple[int, int, int, int]:
    """Return (lx_start, lx_end, lz_start, lz_end) within this chunk (0–16 exclusive end)."""
    if region is None:
        return 0, 16, 0, 16

    x1, z1, x2, z2 = region
    bx1, bx2 = min(x1, x2), max(x1, x2)
    bz1, bz2 = min(z1, z2), max(z1, z2)
    lx1 = max(0, bx1 - cx * 16)
    lx2 = min(16, bx2 - cx * 16 + 1)
    lz1 = max(0, bz1 - cz * 16)
    lz2 = min(16, bz2 - cz * 16 + 1)
    return lx1, lx2, lz1, lz2


def get_or_create_chunk(level, cx: int, cz: int, dim_key: str, region: Region):
    """
    Return the chunk at (cx, cz), creating it if it doesn't exist and a region is active.
    Returns None when the chunk is missing and no region was specified (read-only mode).
    """
    try:
        return level.get_chunk(cx, cz, dim_key)
    except ChunkDoesNotExist:
        if region is not None:
            chunk = AmuletChunk(cx, cz)
            level.put_chunk(chunk, dim_key)
            return chunk
        return None
    except (ChunkLoadError, Exception) as exc:
        logger.warning("Skipping chunk (%d, %d): %s", cx, cz, exc)
        return None

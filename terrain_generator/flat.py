"""
Flat terrain generator: fill every column in a region from world min_y up to a fixed height.

chunk.blocks is a numpy array shaped (16, 16, world_height) indexed as [lx, lz, array_y],
where array_y = world_y - world_y_min  (so array_y=0 is always the bottom of the world).
"""
from __future__ import annotations

import logging

import amulet
from amulet.api.block import Block

from terrain_generator import Region, chunk_range, get_or_create_chunk, local_bounds, _parse_block, DIMENSIONS

logger = logging.getLogger(__name__)


def generate_flat(
    world_path: str,
    block_str: str,
    height: int,
    region: Region = None,
    dimension: str = "overworld",
    dry_run: bool = False,
    progress: bool = True,
) -> int:
    """
    Fill every column in the region/world from world_min_y up to `height` (exclusive)
    with `block`, and clear everything above it to air.

    Returns the total number of blocks that would be / were written.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)
    fill_block = _parse_block(block_str)
    air_block = Block("minecraft", "air")

    level = amulet.load_level(world_path)
    try:
        bounds = level.bounds(dim_key)
        world_y_min: int = bounds.min[1]   # 0 for pre-1.18, -64 for 1.18+
        world_y_max: int = bounds.max[1]   # 256 or 320
    except Exception as exc:
        level.close()
        raise RuntimeError(f"Cannot read world bounds: {exc}") from exc

    coords = list(chunk_range(level, dim_key, region))
    total_chunks = len(coords)

    # Clamp requested height to valid world range and convert to array index
    clamped_height = max(world_y_min, min(height, world_y_max))
    arr_fill_top = clamped_height - world_y_min  # number of filled layers from bottom

    logger.info(
        "Flat generation: block=%s height=%d arr_top=%d chunks=%d dry_run=%s",
        fill_block.namespaced_name, height, arr_fill_top, total_chunks, dry_run,
    )

    total_written = 0

    for i, (cx, cz) in enumerate(coords, 1):
        if progress and i % 100 == 0:
            print(f"  [{i}/{total_chunks}] chunks, {total_written} blocks written so far...")

        chunk = get_or_create_chunk(level, cx, cz, dim_key, region)
        if chunk is None:
            continue

        lx1, lx2, lz1, lz2 = local_bounds(cx, cz, region)
        if lx1 >= lx2 or lz1 >= lz2:
            continue

        col_count = (lx2 - lx1) * (lz2 - lz1)
        total_written += col_count * arr_fill_top

        if not dry_run:
            fill_idx = chunk.block_palette.get_add_block(fill_block)
            air_idx = chunk.block_palette.get_add_block(air_block)
            # Fill from array bottom up to clamped height, clear the rest
            chunk.blocks[lx1:lx2, lz1:lz2, :arr_fill_top] = fill_idx
            chunk.blocks[lx1:lx2, lz1:lz2, arr_fill_top:] = air_idx
            chunk.changed = True

    if not dry_run:
        logger.info("Saving…")
        level.save()

    level.close()
    return total_written

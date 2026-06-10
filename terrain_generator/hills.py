"""
Hills terrain generator: OpenSimplex-noise-based height map applied to an existing world region.

Height formula per column (world x, z):
    col_height = base_height + round(amplitude * opensimplex.noise2(x/scale, z/scale))

chunk.blocks is indexed as [lx, lz, array_y] where array_y = world_y - world_y_min.
"""
from __future__ import annotations

import logging

import opensimplex

import amulet
from amulet.api.block import Block

from terrain_generator import Region, chunk_range, get_or_create_chunk, local_bounds, _parse_block, DIMENSIONS

logger = logging.getLogger(__name__)


def generate_hills(
    world_path: str,
    block_str: str,
    base_height: int = 64,
    amplitude: float = 20.0,
    scale: float = 100.0,
    region: Region = None,
    dimension: str = "overworld",
    dry_run: bool = False,
    progress: bool = True,
) -> int:
    """
    Apply Perlin-noise-based hillscape to every column in the region/world.
    Each column is filled from world_min_y to a noise-derived height, cleared above.

    Args:
        base_height: median terrain height in world y coordinates.
        amplitude:   max deviation from base_height in blocks.
        scale:       horizontal "zoom" — larger = smoother hills.

    Returns the total number of blocks that would be / were written.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)
    fill_block = _parse_block(block_str)
    air_block = Block("minecraft", "air")

    level = amulet.load_level(world_path)
    try:
        bounds = level.bounds(dim_key)
        world_y_min: int = bounds.min[1]
        world_y_max: int = bounds.max[1]
    except Exception as exc:
        level.close()
        raise RuntimeError(f"Cannot read world bounds: {exc}") from exc

    coords = list(chunk_range(level, dim_key, region))
    total_chunks = len(coords)

    logger.info(
        "Hills generation: block=%s base=%d amp=%.1f scale=%.1f chunks=%d dry_run=%s",
        fill_block.namespaced_name, base_height, amplitude, scale, total_chunks, dry_run,
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

        if not dry_run:
            fill_idx = chunk.block_palette.get_add_block(fill_block)
            air_idx = chunk.block_palette.get_add_block(air_block)

        for lx in range(lx1, lx2):
            world_x = cx * 16 + lx
            for lz in range(lz1, lz2):
                world_z = cz * 16 + lz

                # noise2 returns roughly [-1, 1]; clamp result to world bounds
                noise_val = opensimplex.noise2(world_x / scale, world_z / scale)
                col_height = int(round(base_height + amplitude * noise_val))
                col_height = max(world_y_min, min(col_height, world_y_max))
                arr_h = col_height - world_y_min

                total_written += arr_h

                if not dry_run:
                    chunk.blocks[lx, lz, :arr_h] = fill_idx
                    chunk.blocks[lx, lz, arr_h:] = air_idx

        if not dry_run:
            chunk.changed = True

    if not dry_run:
        logger.info("Saving…")
        level.save()

    level.close()
    return total_written

"""
Ocean terrain generator: stone base → sand/gravel floor → water fill → air.
"""
from __future__ import annotations

import logging

import amulet
from amulet.api.block import Block

from terrain_generator import Region, chunk_range, get_or_create_chunk, local_bounds, DIMENSIONS

logger = logging.getLogger(__name__)


def generate_ocean(
    world_path: str,
    sea_level: int = 62,
    floor_height: int = 45,
    region: Region = None,
    dimension: str = "overworld",
    dry_run: bool = False,
    progress: bool = True,
) -> int:
    """
    Fill every column with:
      - stone  from world_min_y to floor_height - 2
      - sand   2 layers on top of stone (the ocean floor)
      - water  from sand surface up to sea_level (exclusive)
      - air    above sea_level

    Returns total non-air blocks that would be / were written.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)

    stone_block = Block("minecraft", "stone")
    sand_block  = Block("minecraft", "sand")
    water_block = Block("minecraft", "water")
    air_block   = Block("minecraft", "air")

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

    clamped_sea   = max(world_y_min + 3, min(sea_level, world_y_max))
    clamped_floor = max(world_y_min,     min(floor_height, clamped_sea - 3))

    # Array-space indices (array_y = world_y - world_y_min)
    arr_stone_top = max(0, clamped_floor - world_y_min)       # stone fill end
    arr_sand_top  = arr_stone_top + 2                          # 2-block sand layer
    arr_sea_top   = max(arr_sand_top + 1, clamped_sea - world_y_min)  # water fill end

    logger.info(
        "Ocean: sea=%d floor=%d arr_stone=%d arr_sand=%d arr_sea=%d chunks=%d dry=%s",
        clamped_sea, clamped_floor, arr_stone_top, arr_sand_top, arr_sea_top,
        total_chunks, dry_run,
    )

    total_written = 0

    for i, (cx, cz) in enumerate(coords, 1):
        if progress and i % 100 == 0:
            print(f"  [{i}/{total_chunks}] chunks, {total_written} blocks so far…")

        chunk = get_or_create_chunk(level, cx, cz, dim_key, region)
        if chunk is None:
            continue

        lx1, lx2, lz1, lz2 = local_bounds(cx, cz, region)
        if lx1 >= lx2 or lz1 >= lz2:
            continue

        col_count = (lx2 - lx1) * (lz2 - lz1)
        total_written += col_count * arr_sea_top  # non-air blocks written

        if not dry_run:
            stone_idx = chunk.block_palette.get_add_block(stone_block)
            sand_idx  = chunk.block_palette.get_add_block(sand_block)
            water_idx = chunk.block_palette.get_add_block(water_block)
            air_idx   = chunk.block_palette.get_add_block(air_block)

            chunk.blocks[lx1:lx2, lz1:lz2, :arr_stone_top]          = stone_idx
            chunk.blocks[lx1:lx2, lz1:lz2, arr_stone_top:arr_sand_top] = sand_idx
            chunk.blocks[lx1:lx2, lz1:lz2, arr_sand_top:arr_sea_top]   = water_idx
            chunk.blocks[lx1:lx2, lz1:lz2, arr_sea_top:]               = air_idx
            chunk.changed = True

    if not dry_run:
        logger.info("Saving…")
        level.save()

    level.close()
    return total_written

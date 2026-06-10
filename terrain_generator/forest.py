"""
Forest terrain generator: flat grass base with randomly placed oak trees.

Tree structure (trunk_height ∈ {4, 5, 6}):
  y = ground+0 … ground+trunk_height-1 : oak_log  (trunk)
  y = trunk_top-1, trunk_top            : 5×5 leaves (no corners)
  y = trunk_top+1, trunk_top+2          : 3×3 leaves (no corners)

Leaves that would land outside [0, 15] in the current chunk are clipped
(trees near chunk edges will have partial canopies — acceptable for a generator).
"""
from __future__ import annotations

import logging
import random

import amulet
from amulet.api.block import Block

from terrain_generator import Region, chunk_range, get_or_create_chunk, local_bounds, DIMENSIONS

logger = logging.getLogger(__name__)

# Leaf offsets relative to (lx, lz) of the trunk
# lower canopy layers (trunk_top-1, trunk_top): 5×5 minus four corners
_LOWER_LEAF_OFFSETS = [
    (dx, dz)
    for dx in range(-2, 3)
    for dz in range(-2, 3)
    if not (abs(dx) == 2 and abs(dz) == 2)
]
# upper canopy layers (trunk_top+1, trunk_top+2): 3×3 minus four corners
_UPPER_LEAF_OFFSETS = [
    (dx, dz)
    for dx in range(-1, 2)
    for dz in range(-1, 2)
    if not (abs(dx) == 1 and abs(dz) == 1)
]


def generate_forest(
    world_path: str,
    ground_height: int = 64,
    tree_density: float = 0.05,
    region: Region = None,
    dimension: str = "overworld",
    dry_run: bool = False,
    progress: bool = True,
) -> int:
    """
    Generate a flat grass terrain with randomly placed oak trees.

    Args:
        ground_height: World-y of the grass surface block.
        tree_density:  Probability [0, 1] that any given column spawns a tree.

    Returns total non-air blocks that would be / were written.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)

    stone_block  = Block("minecraft", "stone")
    dirt_block   = Block("minecraft", "dirt")
    grass_block  = Block("minecraft", "grass_block")
    log_block    = Block("minecraft", "oak_log")
    leaves_block = Block("minecraft", "oak_leaves")
    air_block    = Block("minecraft", "air")

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

    clamped_ground = max(world_y_min + 4, min(ground_height, world_y_max - 10))

    # Array-space indices
    arr_ground    = clamped_ground - world_y_min   # index of the grass block
    arr_dirt_bot  = max(0, arr_ground - 3)          # 3 dirt layers below grass
    arr_stone_top = arr_dirt_bot                    # stone fills 0 .. arr_stone_top

    logger.info(
        "Forest: ground=%d arr_ground=%d density=%.3f chunks=%d dry=%s",
        clamped_ground, arr_ground, tree_density, total_chunks, dry_run,
    )

    world_height = world_y_max - world_y_min
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
        # Base terrain counts (stone + dirt + 1 grass per column)
        total_written += col_count * (arr_ground + 1)

        if dry_run:
            continue

        stone_idx  = chunk.block_palette.get_add_block(stone_block)
        dirt_idx   = chunk.block_palette.get_add_block(dirt_block)
        grass_idx  = chunk.block_palette.get_add_block(grass_block)
        log_idx    = chunk.block_palette.get_add_block(log_block)
        leaves_idx = chunk.block_palette.get_add_block(leaves_block)
        air_idx    = chunk.block_palette.get_add_block(air_block)

        # ── base terrain ──────────────────────────────────────────────
        chunk.blocks[lx1:lx2, lz1:lz2, :arr_stone_top]         = stone_idx
        chunk.blocks[lx1:lx2, lz1:lz2, arr_stone_top:arr_ground - 1] = dirt_idx
        chunk.blocks[lx1:lx2, lz1:lz2, arr_ground - 1:arr_ground]    = dirt_idx
        chunk.blocks[lx1:lx2, lz1:lz2, arr_ground:arr_ground + 1]    = grass_idx
        chunk.blocks[lx1:lx2, lz1:lz2, arr_ground + 1:]               = air_idx

        # ── trees ─────────────────────────────────────────────────────
        rng = random.Random(cx * 31337 + cz * 7919)

        for lx in range(lx1, lx2):
            for lz in range(lz1, lz2):
                if rng.random() >= tree_density:
                    continue

                trunk_h = rng.randint(4, 6)
                trunk_top_arr = arr_ground + trunk_h  # array_y of top log

                # trunk
                for ty in range(trunk_h):
                    ay = arr_ground + 1 + ty
                    if ay < world_height:
                        chunk.blocks[lx, lz, ay] = log_idx
                        total_written += 1

                # lower canopy (trunk_top-1 and trunk_top)
                for dy in (-1, 0):
                    ay = trunk_top_arr + dy
                    if ay < 0 or ay >= world_height:
                        continue
                    for dx, dz in _LOWER_LEAF_OFFSETS:
                        nx, nz = lx + dx, lz + dz
                        if 0 <= nx < 16 and 0 <= nz < 16:
                            if chunk.blocks[nx, nz, ay] == air_idx:
                                chunk.blocks[nx, nz, ay] = leaves_idx
                                total_written += 1

                # upper canopy (trunk_top+1 and trunk_top+2)
                for dy in (1, 2):
                    ay = trunk_top_arr + dy
                    if ay < 0 or ay >= world_height:
                        continue
                    for dx, dz in _UPPER_LEAF_OFFSETS:
                        nx, nz = lx + dx, lz + dz
                        if 0 <= nx < 16 and 0 <= nz < 16:
                            if chunk.blocks[nx, nz, ay] == air_idx:
                                chunk.blocks[nx, nz, ay] = leaves_idx
                                total_written += 1

        chunk.changed = True

    if not dry_run:
        logger.info("Saving…")
        level.save()

    level.close()
    return total_written

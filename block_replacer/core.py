"""
Minecraft world block replacement logic using amulet-core.
"""
from __future__ import annotations

import logging
from typing import Optional

import amulet
from amulet.api.block import Block
from amulet.api.errors import ChunkDoesNotExist, ChunkLoadError

logger = logging.getLogger(__name__)

# Supported dimensions
DIMENSIONS = {
    "overworld": "minecraft:overworld",
    "nether": "minecraft:the_nether",
    "end": "minecraft:the_end",
}


def _parse_block(block_str: str) -> Block:
    """
    Parse "namespace:block_name[prop=val,...]" into a Block object.
    e.g. "minecraft:stone" or "minecraft:oak_log[axis=y]"
    """
    if "[" in block_str:
        namespaced, props_str = block_str.rstrip("]").split("[", 1)
        properties = dict(p.split("=") for p in props_str.split(",") if "=" in p)
    else:
        namespaced = block_str
        properties = {}

    if ":" not in namespaced:
        namespaced = f"minecraft:{namespaced}"

    namespace, base_name = namespaced.split(":", 1)
    return Block(namespace, base_name, properties)


def replace_blocks(
    world_path: str,
    source_block: str,
    target_block: str,
    dimension: str = "overworld",
    dry_run: bool = False,
    progress: bool = True,
) -> int:
    """
    Replace all occurrences of `source_block` with `target_block` in the world.

    Returns the total number of blocks replaced.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)

    src = _parse_block(source_block)
    dst = _parse_block(target_block)

    logger.info("Loading world: %s", world_path)
    level = amulet.load_level(world_path)

    try:
        chunk_coords = list(level.all_chunk_coords(dim_key))
    except Exception as exc:
        level.close()
        raise RuntimeError(f"Failed to list chunks for dimension '{dim_key}': {exc}") from exc

    total_chunks = len(chunk_coords)
    total_replaced = 0

    logger.info(
        "Scanning %d chunks in %s  (dry_run=%s)",
        total_chunks,
        dim_key,
        dry_run,
    )

    for i, (cx, cz) in enumerate(chunk_coords, 1):
        if progress and i % 100 == 0:
            print(f"  [{i}/{total_chunks}] chunks processed, {total_replaced} blocks replaced so far...")

        try:
            chunk = level.get_chunk(cx, cz, dim_key)
        except (ChunkDoesNotExist, ChunkLoadError):
            continue
        except Exception as exc:
            logger.warning("Skipping chunk (%d, %d): %s", cx, cz, exc)
            continue

        # Scan the chunk's block palette for any entry matching the source block.
        # Replacing at palette level is O(palette_size) per chunk instead of O(volume).
        indices_to_replace: list[int] = []
        for idx in range(len(chunk.block_palette)):
            palette_block = chunk.block_palette.get_block_from_bin_id(idx)
            if (
                palette_block.namespaced_name == src.namespaced_name
                and (not src.properties or palette_block.properties == src.properties)
            ):
                indices_to_replace.append(idx)

        if not indices_to_replace:
            continue

        # Count replacements in this chunk
        import numpy as np  # lazy import – amulet depends on numpy anyway

        blocks_array = chunk.blocks
        chunk_count = sum(
            int(np.count_nonzero(blocks_array == idx)) for idx in indices_to_replace
        )
        total_replaced += chunk_count

        if not dry_run and chunk_count > 0:
            dst_idx = chunk.block_palette.get_add_block(dst)
            for old_idx in indices_to_replace:
                blocks_array[blocks_array == old_idx] = dst_idx
            chunk.changed = True

    if not dry_run:
        logger.info("Saving world...")
        level.save()

    level.close()
    return total_replaced

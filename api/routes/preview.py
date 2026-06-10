"""
GET /api/preview — 2-D top-view block colour sampler.

Returns a JSON payload:
  { "grid": [[colour, ...], ...], "size": N, "y": Y }

Each element of `grid` is a hex colour string (#RRGGBB) representing
the block found at the given Y level in the centre (lx=8, lz=8) of
each scanned chunk.  The grid covers a (size × size) chunk region
centred on chunk (0, 0): rows = z, columns = x.

When amulet-core is not installed (production deployment) the endpoint
returns HTTP 501 — identical behaviour to /api/generate and /api/replace.
"""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException, Query

try:
    import amulet
    from block_replacer.core import DIMENSIONS
    _AMULET_AVAILABLE = True
except ImportError:
    _AMULET_AVAILABLE = False

router = APIRouter()

_LOCAL_ONLY_MSG = "이 기능은 로컬 환경에서만 사용 가능합니다. (amulet-core not installed)"

# ── Block → hex colour mapping ────────────────────────────────────────────────
BLOCK_COLOURS: dict[str, str] = {
    # terrain
    "minecraft:grass_block":    "#5D9C3C",
    "minecraft:grass":          "#5D9C3C",
    "minecraft:tall_grass":     "#5D9C3C",
    "minecraft:dirt":           "#8B5A2B",
    "minecraft:coarse_dirt":    "#7A4E22",
    "minecraft:rooted_dirt":    "#7A4E22",
    "minecraft:podzol":         "#6B3A1F",
    "minecraft:stone":          "#7F7F7F",
    "minecraft:deepslate":      "#5A5A5A",
    "minecraft:cobblestone":    "#8A8A8A",
    "minecraft:andesite":       "#8C8C8C",
    "minecraft:diorite":        "#C0BFBE",
    "minecraft:granite":        "#9C6B4E",
    # water / ocean
    "minecraft:water":          "#3D5BDE",
    "minecraft:kelp":           "#2D7A3A",
    "minecraft:seagrass":       "#3A8A4A",
    "minecraft:coral_block":    "#E05050",
    # sand / desert
    "minecraft:sand":           "#DDD074",
    "minecraft:red_sand":       "#B85A30",
    "minecraft:sandstone":      "#D4C85A",
    "minecraft:gravel":         "#8A8A8A",
    "minecraft:clay":           "#8C8C9C",
    # forest / wood
    "minecraft:oak_log":        "#7D5A2B",
    "minecraft:oak_leaves":     "#3B7A2B",
    "minecraft:birch_log":      "#C8C8A9",
    "minecraft:birch_leaves":   "#80A755",
    "minecraft:spruce_log":     "#5C3A1E",
    "minecraft:spruce_leaves":  "#3B5A3B",
    "minecraft:jungle_log":     "#6B4A1E",
    "minecraft:jungle_leaves":  "#2E7A1E",
    "minecraft:dark_oak_log":   "#3A2A0E",
    "minecraft:dark_oak_leaves":"#2A5A1A",
    "minecraft:acacia_log":     "#8B4A2B",
    "minecraft:acacia_leaves":  "#6A9A3A",
    # snow / ice
    "minecraft:snow_block":     "#FFFFFF",
    "minecraft:snow":           "#EAEAEA",
    "minecraft:ice":            "#A0C4FF",
    "minecraft:packed_ice":     "#7AB8FF",
    "minecraft:blue_ice":       "#5A9AEE",
    # nether
    "minecraft:netherrack":     "#8B2500",
    "minecraft:nether_bricks":  "#2D0D0D",
    "minecraft:soul_sand":      "#5C4430",
    "minecraft:soul_soil":      "#4A3520",
    "minecraft:magma_block":    "#B84000",
    "minecraft:lava":           "#FF6600",
    "minecraft:basalt":         "#3A3A46",
    "minecraft:blackstone":     "#1A1A22",
    "minecraft:crimson_nylium":  "#8A0000",
    "minecraft:warped_nylium":   "#007A6B",
    # end
    "minecraft:end_stone":      "#D4D090",
    "minecraft:obsidian":       "#2D1B5A",
    # misc
    "minecraft:bedrock":        "#1A1A1A",
    "minecraft:mossy_cobblestone": "#6A8A4A",
    "minecraft:air":            "#87CEEB",
    "minecraft:cave_air":       "#87CEEB",
    "minecraft:void_air":       "#000000",
}

_DEFAULT_COLOUR = "#404040"   # unknown blocks
_MISSING_COLOUR = "#0A0A0A"  # unexplored / missing chunks


def _colour_for(name: str) -> str:
    return BLOCK_COLOURS.get(name, _DEFAULT_COLOUR)


def _sample_preview(world_path: str, y: int, dimension: str, size: int) -> dict:
    """
    Load `size×size` chunks centred on (0,0) and sample the block at
    (lx=8, lz=8, array_y) in each chunk.  Returns a row-major colour grid.
    """
    dim_key = DIMENSIONS.get(dimension, dimension)
    half = size // 2

    level = amulet.load_level(world_path)
    try:
        bounds = level.bounds(dim_key)
        world_y_min: int = bounds.min[1]
        world_y_max: int = bounds.max[1]
    except Exception as exc:
        level.close()
        raise RuntimeError(f"Cannot read world bounds: {exc}") from exc

    arr_y = max(0, min(y - world_y_min, world_y_max - world_y_min - 1))

    grid: list[list[str]] = []
    for cz in range(-half, size - half):
        row: list[str] = []
        for cx in range(-half, size - half):
            try:
                chunk = level.get_chunk(cx, cz, dim_key)
                block_id = int(chunk.blocks[8, 8, arr_y])
                block = chunk.block_palette[block_id]
                colour = _colour_for(block.namespaced_name)
            except Exception:
                colour = _MISSING_COLOUR
            row.append(colour)
        grid.append(row)

    level.close()
    return {"grid": grid, "size": size, "y": y}


@router.get("/preview")
async def preview(
    world: str = Query(..., description="Absolute path to the Minecraft world folder"),
    y: int = Query(64, description="Y level to sample"),
    dimension: str = Query("overworld", description="Dimension"),
    size: int = Query(64, ge=4, le=128, description="Grid dimension in chunks (NxN)"),
):
    if not _AMULET_AVAILABLE:
        raise HTTPException(status_code=501, detail=_LOCAL_ONLY_MSG)

    from api._executor import executor
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            executor,
            lambda: _sample_preview(world, y, dimension, size),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result

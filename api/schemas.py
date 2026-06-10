from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class RegionModel(BaseModel):
    x1: int
    z1: int
    x2: int
    z2: int


class ReplaceRequest(BaseModel):
    world_path: str = Field(..., description="Absolute path to the Minecraft world folder")
    source: str = Field(..., examples=["minecraft:stone"])
    target: str = Field(..., examples=["minecraft:diamond_block"])
    dimension: Literal["overworld", "nether", "end"] = "overworld"
    dry_run: bool = False


class GenerateRequest(BaseModel):
    world_path: str = Field(..., description="Absolute path to the Minecraft world folder")
    type: Literal["flat", "hills", "ocean", "forest"]
    block: Optional[str] = Field(None, examples=["minecraft:grass_block"])
    # flat
    height: Optional[int] = Field(64, description="Fill height (flat only)")
    # hills
    base_height: Optional[int] = Field(64, description="Median height (hills only)")
    amplitude: Optional[float] = Field(20.0, description="Height deviation in blocks (hills only)")
    scale: Optional[float] = Field(100.0, description="Horizontal noise zoom (hills only)")
    # ocean
    sea_level: Optional[int] = Field(62, description="Water surface height (ocean only)")
    floor_height: Optional[int] = Field(45, description="Ocean floor height (ocean only)")
    # forest
    ground_height: Optional[int] = Field(64, description="Grass surface height (forest only)")
    tree_density: Optional[float] = Field(0.05, description="Tree probability per column 0–1 (forest only)")
    # shared
    dimension: Literal["overworld", "nether", "end"] = "overworld"
    region: Optional[RegionModel] = None
    dry_run: bool = False


class OperationResult(BaseModel):
    count: int
    message: str
    dry_run: bool

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
    type: Literal["flat", "hills"]
    block: str = Field(..., examples=["minecraft:grass_block"])
    # flat
    height: Optional[int] = Field(64, description="Fill height (flat only)")
    # hills
    base_height: Optional[int] = Field(64, description="Median height (hills only)")
    amplitude: Optional[float] = Field(20.0, description="Height deviation in blocks (hills only)")
    scale: Optional[float] = Field(100.0, description="Horizontal noise zoom (hills only)")
    # shared
    dimension: Literal["overworld", "nether", "end"] = "overworld"
    region: Optional[RegionModel] = None
    dry_run: bool = False


class OperationResult(BaseModel):
    count: int
    message: str
    dry_run: bool

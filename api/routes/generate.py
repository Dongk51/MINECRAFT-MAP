import asyncio
from fastapi import APIRouter, HTTPException
from api.schemas import GenerateRequest, OperationResult
from api._executor import executor
from terrain_generator.flat import generate_flat
from terrain_generator.hills import generate_hills

router = APIRouter()


@router.post("/generate", response_model=OperationResult)
async def generate(req: GenerateRequest):
    region = (req.region.x1, req.region.z1, req.region.x2, req.region.z2) if req.region else None

    loop = asyncio.get_running_loop()
    try:
        if req.type == "flat":
            count: int = await loop.run_in_executor(
                executor,
                lambda: generate_flat(
                    world_path=req.world_path,
                    block_str=req.block,
                    height=req.height or 64,
                    region=region,
                    dimension=req.dimension,
                    dry_run=req.dry_run,
                    progress=False,
                ),
            )
        else:
            count = await loop.run_in_executor(
                executor,
                lambda: generate_hills(
                    world_path=req.world_path,
                    block_str=req.block,
                    base_height=req.base_height or 64,
                    amplitude=req.amplitude or 20.0,
                    scale=req.scale or 100.0,
                    region=region,
                    dimension=req.dimension,
                    dry_run=req.dry_run,
                    progress=False,
                ),
            )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    verb = "Would write" if req.dry_run else "Wrote"
    return OperationResult(count=count, message=f"{verb} {count:,} block(s)", dry_run=req.dry_run)

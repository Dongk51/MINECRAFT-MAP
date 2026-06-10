import asyncio
from fastapi import APIRouter, HTTPException
from api.schemas import ReplaceRequest, OperationResult
from api._executor import executor
from block_replacer.core import replace_blocks

router = APIRouter()


@router.post("/replace", response_model=OperationResult)
async def replace(req: ReplaceRequest):
    loop = asyncio.get_running_loop()
    try:
        count: int = await loop.run_in_executor(
            executor,
            lambda: replace_blocks(
                world_path=req.world_path,
                source_block=req.source,
                target_block=req.target,
                dimension=req.dimension,
                dry_run=req.dry_run,
                progress=False,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    verb = "Would replace" if req.dry_run else "Replaced"
    return OperationResult(count=count, message=f"{verb} {count:,} block(s)", dry_run=req.dry_run)

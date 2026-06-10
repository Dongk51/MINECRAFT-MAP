import asyncio
from fastapi import APIRouter, HTTPException
from api.schemas import ReplaceRequest, OperationResult
from api._executor import executor

try:
    from block_replacer.core import replace_blocks
    _AMULET_AVAILABLE = True
except ImportError:
    _AMULET_AVAILABLE = False

router = APIRouter()

_LOCAL_ONLY_MSG = "이 기능은 로컬 환경에서만 사용 가능합니다. (amulet-core not installed)"


@router.post("/replace", response_model=OperationResult)
async def replace(req: ReplaceRequest):
    if not _AMULET_AVAILABLE:
        raise HTTPException(status_code=501, detail=_LOCAL_ONLY_MSG)

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

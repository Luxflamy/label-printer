"""健康检查 — 前端用来判断本地 API 是否已启动。"""

from __future__ import annotations

from fastapi import APIRouter

from services.api.schemas import Envelope, HealthData

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Envelope[HealthData])
def health() -> Envelope[HealthData]:
    return Envelope(ok=True, data=HealthData())

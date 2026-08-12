"""
Reports controller — Task 1.4
GET /reports       : Danh sách tất cả test runs từ DB
GET /reports/{id}  : Chi tiết 1 report theo run_id hoặc task_id
"""
import os
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.serializers.models import DataResponse
from app.utils.globals import BACKGROUND_TASKS
from app.db.database import get_all_test_runs, get_test_run_by_id

router = APIRouter()


@router.get("", response_model=DataResponse[dict])
async def list_reports(page: int = 1, limit: int = 20):
    """GET /reports — Danh sách tất cả test reports"""
    runs = get_all_test_runs(limit=limit)

    # Enrich với live status từ BACKGROUND_TASKS nếu task còn trong memory
    for run in runs:
        task_id = run.get("task_id")
        if task_id and task_id in BACKGROUND_TASKS:
            run["live_status"] = BACKGROUND_TASKS[task_id].get("status")

    return DataResponse(
        data={"reports": runs, "page": page, "limit": limit, "total": len(runs)},
        message="Reports retrieved successfully"
    )


@router.get("/{report_id}", response_model=DataResponse[Dict[str, Any]])
async def get_report_detail(report_id: str):
    """GET /reports/{id} — Chi tiết 1 report theo run_id hoặc task_id"""
    # 1. Thử tìm trong BACKGROUND_TASKS (task còn mới, chưa expire)
    task_data = BACKGROUND_TASKS.get(report_id)
    if task_data:
        report_path = task_data.get("report_path")
        content = None
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
        return DataResponse(
            data={
                "report_id": report_id,
                "status": task_data.get("status"),
                "results": task_data.get("results", []),
                "content": content,
            },
            message="Report retrieved from memory"
        )

    # 2. Thử tìm trong DB (theo run_id hoặc task_id)
    run = get_test_run_by_id(report_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")

    # Đọc nội dung file report nếu có
    report_path = run.get("report_path")
    if report_path and os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            run["content"] = f.read()

    return DataResponse(data={"report_id": report_id, **run}, message="Report retrieved from database")

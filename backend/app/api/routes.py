from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models.pipeline import (
    ExportResponse,
    GeneratePipelineRequest,
    HistoryListResponse,
    PipelineRecord,
)
from app.services.bedrock_service import BedrockPipelineGenerator, PipelineGenerationError
from app.services.export_service import ExportService
from app.services.history_repository import create_history_repository

router = APIRouter(prefix="/api", tags=["pipelines"])
settings = get_settings()
history_repository = create_history_repository(settings)
generator = BedrockPipelineGenerator(settings)
export_service = ExportService(settings)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


@router.post(
    "/pipelines/generate",
    response_model=PipelineRecord,
    status_code=status.HTTP_201_CREATED,
)
def generate_pipeline(request: GeneratePipelineRequest) -> PipelineRecord:
    try:
        spec = generator.generate(request)
    except PipelineGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Pipeline generation failed: {exc}",
        ) from exc

    record = PipelineRecord(
        user_id=request.user_id,
        title=request.title or spec.title,
        description=request.description,
        tags=request.tags,
        spec=spec,
    )
    return history_repository.save(record)


@router.get("/pipelines/history", response_model=HistoryListResponse)
def list_history(
    user_id: str = Query(default="anonymous", min_length=1, max_length=128),
    limit: int = Query(default=25, ge=1, le=100),
) -> HistoryListResponse:
    return HistoryListResponse(items=history_repository.list(user_id=user_id, limit=limit))


@router.get("/pipelines/{pipeline_id}", response_model=PipelineRecord)
def get_pipeline(pipeline_id: str) -> PipelineRecord:
    record = history_repository.get(pipeline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return record


@router.delete("/pipelines/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: str) -> Response:
    history_repository.delete(pipeline_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/pipelines/{pipeline_id}/export/markdown", response_model=ExportResponse)
def export_markdown(pipeline_id: str) -> ExportResponse:
    record = history_repository.get(pipeline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    content, s3_key = export_service.markdown(record)
    return ExportResponse(
        filename=f"{record.id}.md",
        content_type="text/markdown",
        content=content,
        s3_key=s3_key,
    )


@router.get("/pipelines/{pipeline_id}/export/markdown/download")
def download_markdown(pipeline_id: str) -> Response:
    record = history_repository.get(pipeline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    content, _ = export_service.markdown(record)
    return Response(
        content=content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{record.id}.md"'},
    )


@router.get("/pipelines/{pipeline_id}/export/json", response_model=ExportResponse)
def export_json(pipeline_id: str) -> ExportResponse:
    record = history_repository.get(pipeline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    content, s3_key = export_service.json_spec(record)
    return ExportResponse(
        filename=f"{record.id}.json",
        content_type="application/json",
        content=content,
        s3_key=s3_key,
    )


@router.get("/pipelines/{pipeline_id}/export/json/download")
def download_json(pipeline_id: str) -> JSONResponse:
    record = history_repository.get(pipeline_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    content, _ = export_service.json_spec(record)
    return JSONResponse(
        content=content,
        headers={"Content-Disposition": f'attachment; filename="{record.id}.json"'},
    )

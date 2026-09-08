from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


LayerCategory = Literal[
    "source",
    "ingestion",
    "storage",
    "transformation",
    "orchestration",
    "serving",
    "analytics",
    "monitoring",
    "security",
]


class GeneratePipelineRequest(BaseModel):
    description: str = Field(..., min_length=20, max_length=8000)
    user_id: str = Field(default="anonymous", min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=120)
    tags: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return " ".join(value.strip().split())


class WorkflowStep(BaseModel):
    order: int = Field(..., ge=1)
    name: str
    description: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    owner: str | None = None


class ServiceRecommendation(BaseModel):
    name: str
    category: LayerCategory | str
    purpose: str
    why_selected: str
    alternatives: list[str] = Field(default_factory=list)


class LayerRecommendation(BaseModel):
    name: str
    services: list[str] = Field(default_factory=list)
    rationale: str


class DiagramNode(BaseModel):
    id: str
    label: str
    category: LayerCategory | str
    service: str | None = None
    description: str | None = None
    icon: str | None = None
    x: int = 0
    y: int = 0


class DiagramEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str | None = None


class DiagramSpec(BaseModel):
    nodes: list[DiagramNode]
    edges: list[DiagramEdge]


class PipelineSpec(BaseModel):
    title: str
    summary: str
    architecture: str
    workflow: list[WorkflowStep]
    aws_services: list[ServiceRecommendation]
    ingestion_strategy: LayerRecommendation
    storage_layer: LayerRecommendation
    transformation_layer: LayerRecommendation
    orchestration_strategy: LayerRecommendation
    monitoring_strategy: LayerRecommendation
    security_best_practices: list[str]
    cost_optimization: list[str]
    folder_structure: str
    deployment_recommendations: list[str]
    diagram: DiagramSpec
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    generated_by: str = "amazon-bedrock"
    generation_warnings: list[str] = Field(default_factory=list)


class PipelineRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = "anonymous"
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    spec: PipelineSpec
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dynamodb_item(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "spec": self.spec.model_dump(mode="json"),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "PipelineRecord":
        return cls(
            id=item["id"],
            user_id=item.get("userId", "anonymous"),
            title=item["title"],
            description=item["description"],
            tags=item.get("tags", []),
            spec=PipelineSpec.model_validate(item["spec"]),
            created_at=item["createdAt"],
            updated_at=item.get("updatedAt", item["createdAt"]),
        )


class HistoryListResponse(BaseModel):
    items: list[PipelineRecord]


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    content: str | dict[str, Any]
    s3_key: str | None = None

from __future__ import annotations

import json
import re
from typing import Any

import boto3
from botocore.config import Config

from app.core.config import Settings
from app.models.pipeline import PipelineRecord


class ExportService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.s3 = (
            boto3.client(
                "s3",
                region_name=settings.aws_region,
                config=Config(retries={"max_attempts": 5, "mode": "adaptive"}),
            )
            if settings.export_bucket_name
            else None
        )

    def markdown(self, record: PipelineRecord) -> tuple[str, str | None]:
        content = self._markdown_content(record)
        key = self._persist(record, "md", content, "text/markdown")
        return content, key

    def json_spec(self, record: PipelineRecord) -> tuple[dict[str, Any], str | None]:
        content = record.model_dump(mode="json")
        key = self._persist(
            record,
            "json",
            json.dumps(content, indent=2),
            "application/json",
        )
        return content, key

    def _persist(
        self,
        record: PipelineRecord,
        extension: str,
        content: str,
        content_type: str,
    ) -> str | None:
        if not self.s3 or not self.settings.export_bucket_name:
            return None
        key = f"exports/{record.user_id}/{record.id}/{self._slug(record.title)}.{extension}"
        self.s3.put_object(
            Bucket=self.settings.export_bucket_name,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )
        return key

    def _markdown_content(self, record: PipelineRecord) -> str:
        spec = record.spec
        services = "\n".join(
            f"| {item.name} | {item.category} | {item.purpose} | {item.why_selected} |"
            for item in spec.aws_services
        )
        workflow = "\n".join(
            f"{step.order}. **{step.name}** - {step.description}"
            for step in sorted(spec.workflow, key=lambda item: item.order)
        )
        security = "\n".join(f"- {item}" for item in spec.security_best_practices)
        cost = "\n".join(f"- {item}" for item in spec.cost_optimization)
        deployment = "\n".join(f"- {item}" for item in spec.deployment_recommendations)
        assumptions = "\n".join(f"- {item}" for item in spec.assumptions)
        risks = "\n".join(f"- {item}" for item in spec.risks)

        return f"""# {spec.title}

Generated: {record.created_at}

## Summary

{spec.summary}

## Architecture

{spec.architecture}

## ETL Workflow

{workflow}

## Recommended AWS Services

| Service | Category | Purpose | Why selected |
| --- | --- | --- | --- |
{services}

## Ingestion Strategy

{spec.ingestion_strategy.rationale}

## Storage Layer

{spec.storage_layer.rationale}

## Transformation Layer

{spec.transformation_layer.rationale}

## Orchestration Strategy

{spec.orchestration_strategy.rationale}

## Monitoring Strategy

{spec.monitoring_strategy.rationale}

## Security Best Practices

{security}

## Cost Optimization

{cost}

## Project Structure

```text
{spec.folder_structure}
```

## Deployment Recommendations

{deployment}

## Assumptions

{assumptions or "- None"}

## Risks

{risks or "- None"}
"""

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
        return slug or "pipeline-design"

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config

from app.core.config import Settings
from app.models.pipeline import PipelineRecord


class HistoryRepository(Protocol):
    def save(self, record: PipelineRecord) -> PipelineRecord:
        ...

    def list(self, user_id: str, limit: int = 25) -> list[PipelineRecord]:
        ...

    def get(self, pipeline_id: str) -> PipelineRecord | None:
        ...

    def delete(self, pipeline_id: str) -> None:
        ...


class DynamoHistoryRepository:
    def __init__(self, table_name: str, region_name: str):
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
            config=Config(retries={"max_attempts": 5, "mode": "adaptive"}),
        )
        self.table = dynamodb.Table(table_name)

    def save(self, record: PipelineRecord) -> PipelineRecord:
        record.updated_at = datetime.now(timezone.utc).isoformat()
        self.table.put_item(Item=record.to_dynamodb_item())
        return record

    def list(self, user_id: str, limit: int = 25) -> list[PipelineRecord]:
        response = self.table.query(
            IndexName="userIdCreatedAtIndex",
            KeyConditionExpression=Key("userId").eq(user_id),
            ScanIndexForward=False,
            Limit=limit,
        )
        return [
            PipelineRecord.from_dynamodb_item(item)
            for item in response.get("Items", [])
        ]

    def get(self, pipeline_id: str) -> PipelineRecord | None:
        item = self.table.get_item(Key={"id": pipeline_id}).get("Item")
        if not item:
            return None
        return PipelineRecord.from_dynamodb_item(item)

    def delete(self, pipeline_id: str) -> None:
        self.table.delete_item(Key={"id": pipeline_id})


class LocalHistoryRepository:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.path = data_dir / "history.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def save(self, record: PipelineRecord) -> PipelineRecord:
        records = self._read()
        record.updated_at = datetime.now(timezone.utc).isoformat()
        records = [item for item in records if item.id != record.id]
        records.append(record)
        self._write(records)
        return record

    def list(self, user_id: str, limit: int = 25) -> list[PipelineRecord]:
        records = [record for record in self._read() if record.user_id == user_id]
        return sorted(records, key=lambda item: item.created_at, reverse=True)[:limit]

    def get(self, pipeline_id: str) -> PipelineRecord | None:
        return next((item for item in self._read() if item.id == pipeline_id), None)

    def delete(self, pipeline_id: str) -> None:
        self._write([item for item in self._read() if item.id != pipeline_id])

    def _read(self) -> list[PipelineRecord]:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [PipelineRecord.model_validate(item) for item in raw]

    def _write(self, records: list[PipelineRecord]) -> None:
        payload = [record.model_dump(mode="json") for record in records]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def create_history_repository(settings: Settings) -> HistoryRepository:
    if settings.history_table_name:
        return DynamoHistoryRepository(settings.history_table_name, settings.aws_region)
    return LocalHistoryRepository(settings.local_data_dir)

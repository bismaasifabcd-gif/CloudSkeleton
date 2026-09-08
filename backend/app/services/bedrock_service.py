from __future__ import annotations

import json
import logging
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import ValidationError

from app.core.config import Settings
from app.models.pipeline import GeneratePipelineRequest, PipelineSpec
from app.services.fallback_generator import FallbackPipelineGenerator
from app.services.spec_normalizer import coerce_pipeline_payload, normalize_pipeline_spec
from app.utils.json_tools import JsonExtractionError, extract_json_object

logger = logging.getLogger(__name__)


class PipelineGenerationError(RuntimeError):
    pass


class BedrockPipelineGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.fallback = FallbackPipelineGenerator()
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            config=Config(
                retries={"max_attempts": 5, "mode": "adaptive"},
                connect_timeout=5,
                read_timeout=25,
                max_pool_connections=25,
            ),
        )

    def generate(self, request: GeneratePipelineRequest) -> PipelineSpec:
        if self.settings.use_mock_ai:
            return normalize_pipeline_spec(
                self.fallback.generate(request.description, request.title)
            )

        try:
            raw_text = self._call_bedrock(request)
            parsed = coerce_pipeline_payload(extract_json_object(raw_text))
            spec = PipelineSpec.model_validate(parsed)
            spec.generated_by = f"amazon-bedrock:{self.settings.bedrock_model_id}"
            return normalize_pipeline_spec(spec)
        except (ClientError, ValidationError, JsonExtractionError, KeyError) as exc:
            logger.exception("Pipeline generation failed")
            if self.settings.enable_fallback:
                spec = self.fallback.generate(request.description, request.title)
                spec.generation_warnings.append(
                    f"Bedrock generation failed and deterministic fallback was used: {exc}"
                )
                return normalize_pipeline_spec(spec)
            raise PipelineGenerationError(str(exc)) from exc

    def _call_bedrock(self, request: GeneratePipelineRequest) -> str:
        response = self.client.converse(
            modelId=self.settings.bedrock_model_id,
            system=[{"text": self._system_prompt()}],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": (
                                "Design a production-ready AWS-native data pipeline "
                                "for this natural language requirement:\n\n"
                                f"{request.description}\n\n"
                                f"User supplied title: {request.title or 'None'}"
                            )
                        }
                    ],
                }
            ],
            inferenceConfig={
                "maxTokens": self.settings.bedrock_max_tokens,
                "temperature": self.settings.bedrock_temperature,
            },
            requestMetadata={
                "application": "ai-data-pipeline-generator",
                "environment": self.settings.environment,
            },
        )
        content = response["output"]["message"]["content"]
        return "".join(block.get("text", "") for block in content)

    def _system_prompt(self) -> str:
        schema = self._schema_hint()
        return (
            "You are an expert AWS Solutions Architect specializing in Data Engineering "
            "and MLOps. Your task is to analyze user requirements, whether provided as "
            "plain English or structured bullet points, and generate a complete, "
            "production-grade AWS Data Pipeline Architecture in strict JSON format.\n\n"
            "CRITICAL ARCHITECTURE AND STRUCTURAL RULES:\n"
            "1. COMPREHENSIVE SERVICE MAPPING: Every AWS service mentioned or utilized "
            "anywhere in the architecture MUST be explicitly listed in the services "
            "array, etl_workflow, and diagram.nodes. Do not omit tools like AWS Lambda, "
            "Amazon Athena, AWS Glue, Amazon Kinesis, AWS KMS, or IAM if they are part "
            "of the pipeline.\n"
            "2. GIT REPOSITORY FOLDER STRUCTURE: The folder_structure field MUST contain "
            "a realistic developer codebase directory layout with IaC scripts, dbt "
            "models, Lambda handlers, orchestration code, tests, and docs when relevant. "
            "Do NOT output S3 bucket URIs such as s3://bucket/path.\n"
            "3. BEGINNER-FRIENDLY AND ACCURATE: If the user provides a vague prompt "
            "without specifying AWS tools, automatically select standard, cost-effective "
            "AWS services best suited for the latency, scale, and storage goals.\n"
            "4. DIAGRAM CONTRACT: Do not invent x/y coordinates. Return semantic nodes "
            "and edges only. The frontend will apply deterministic layout.\n\n"
            "Return ONLY valid, parseable JSON with no markdown code block wrappers. "
            "The JSON object must match this shape:\n"
            f"{json.dumps(schema, indent=2)}"
        )

    def _schema_hint(self) -> dict[str, Any]:
        return {
            "title": "Short descriptive pipeline title, max 5 words",
            "summary": "Clear 2-sentence summary of the architecture.",
            "architecture_overview": (
                "Detailed explanation of data flow across source, ingestion, storage, "
                "transformation, serving, orchestration, monitoring, and security."
            ),
            "diagram": {
                "nodes": [
                    {
                        "id": "node_1",
                        "type": "customNode",
                        "data": {
                            "label": "Source",
                            "service": "External Data",
                            "description": "Incoming CSV files",
                        },
                    },
                    {
                        "id": "node_2",
                        "type": "customNode",
                        "data": {
                            "label": "Ingestion",
                            "service": "AWS Lambda / Amazon S3",
                            "description": "Automated ingestion and landing.",
                        },
                    },
                ],
                "edges": [
                    {
                        "id": "e1-2",
                        "source": "node_1",
                        "target": "node_2",
                        "animated": True,
                    }
                ],
            },
            "etl_workflow": [
                {
                    "step": 1,
                    "title": "Ingestion",
                    "description": "Detailed step description including all services used.",
                }
            ],
            "services": [
                {
                    "name": "Amazon S3",
                    "category": "storage",
                    "description": "Raw and curated data storage.",
                }
            ],
            "security_best_practices": ["string"],
            "cost_optimization": ["string"],
            "folder_structure": (
                "project-root/\n"
                "  terraform/\n"
                "    main.tf\n"
                "    variables.tf\n"
                "  src/\n"
                "    lambda/\n"
                "      ingest_handler.py\n"
                "    glue/\n"
                "      transform_job.py\n"
                "  dbt/\n"
                "    models/\n"
                "  README.md"
            ),
            "deployment_recommendations": ["string"],
            "risks": ["string"],
        }

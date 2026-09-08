from app.models.pipeline import PipelineSpec
from app.services.spec_normalizer import coerce_pipeline_payload, normalize_pipeline_spec


def test_external_bedrock_schema_is_coerced_and_completed() -> None:
    payload = {
        "title": "CSV Sales Lake",
        "summary": "Daily CSV sales files are ingested and cleaned. Curated data is queried with Athena.",
        "architecture_overview": (
            "AWS Lambda validates inbound files, Amazon S3 stores bronze data, "
            "AWS Glue transforms the dataset, and Amazon Athena serves analysts."
        ),
        "diagram": {
            "nodes": [
                {
                    "id": "node_1",
                    "type": "customNode",
                    "data": {
                        "label": "Source",
                        "service": "FTP CSV",
                        "description": "Daily sales files.",
                    },
                },
                {
                    "id": "node_2",
                    "type": "customNode",
                    "data": {
                        "label": "Ingestion",
                        "service": "AWS Lambda / S3",
                        "description": "Validate and land files.",
                    },
                },
                {
                    "id": "node_3",
                    "type": "customNode",
                    "data": {
                        "label": "Serving",
                        "service": "Amazon Athena",
                        "description": "Query curated data.",
                    },
                },
            ],
            "edges": [
                {"id": "e1-2", "source": "node_1", "target": "node_2"},
                {"id": "e2-3", "source": "node_2", "target": "node_3"},
            ],
        },
        "etl_workflow": [
            {
                "step": 1,
                "title": "Ingestion",
                "description": "AWS Lambda validates files before landing them in S3.",
            },
            {
                "step": 2,
                "title": "Transform",
                "description": "AWS Glue cleans and writes curated data.",
            },
        ],
        "services": [
            {
                "name": "Amazon S3",
                "category": "storage",
                "description": "Bronze and curated data storage.",
            },
            {
                "name": "AWS Glue",
                "category": "transformation",
                "description": "ETL processing.",
            },
            {
                "name": "AWS Glue",
                "category": "transformation",
                "description": "Duplicate model output.",
            },
            {
                "name": "AWS CloudWatch",
                "category": "monitoring",
                "description": "Logs and alarms.",
            },
        ],
        "security_best_practices": ["Encrypt with AWS KMS."],
        "cost_optimization": ["Partition data for Athena."],
        "folder_structure": "s3://example/raw\ns3://example/curated",
        "deployment_recommendations": ["Deploy with Terraform."],
        "risks": ["CSV schema drift."],
    }

    spec = normalize_pipeline_spec(
        PipelineSpec.model_validate(coerce_pipeline_payload(payload))
    )

    service_names = {service.name for service in spec.aws_services}
    assert {
        "Amazon S3",
        "AWS Glue",
        "AWS Lambda",
        "Amazon Athena",
        "Amazon CloudWatch",
    } <= service_names
    assert "AWS CloudWatch" not in service_names
    assert len(service_names) == len(spec.aws_services)
    assert "s3://" not in spec.folder_structure.lower()
    assert "src/" in spec.folder_structure
    assert "terraform/" in spec.folder_structure

    workflow_text = " ".join(step.description for step in spec.workflow)
    assert "AWS Lambda" in workflow_text
    assert "Amazon Athena" in workflow_text

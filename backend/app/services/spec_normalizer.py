from __future__ import annotations

import re
from typing import Any

from app.models.pipeline import DiagramEdge, DiagramNode, PipelineSpec, ServiceRecommendation


CORE_FLOW_CATEGORIES = [
    "source",
    "ingestion",
    "storage",
    "transformation",
    "serving",
    "analytics",
]

SUPPORT_CATEGORIES = {"orchestration", "monitoring", "security"}

SERVICE_CATEGORY_HINTS = {
    "AWS Transfer Family": "ingestion",
    "AWS Lambda": "ingestion",
    "Amazon EventBridge": "orchestration",
    "AWS Step Functions": "orchestration",
    "AWS Glue": "transformation",
    "AWS Glue Data Catalog": "storage",
    "AWS Glue Data Quality": "transformation",
    "Amazon S3": "storage",
    "Amazon Athena": "serving",
    "Amazon Redshift": "serving",
    "Amazon QuickSight": "analytics",
    "Amazon CloudWatch": "monitoring",
    "AWS CloudTrail": "monitoring",
    "AWS KMS": "security",
    "AWS IAM": "security",
    "AWS Secrets Manager": "security",
    "AWS Lake Formation": "security",
    "Amazon DynamoDB": "storage",
    "Amazon API Gateway": "serving",
    "Amazon Kinesis Data Streams": "ingestion",
    "Amazon Data Firehose": "ingestion",
    "Amazon ECS Fargate": "orchestration",
    "Amazon MWAA": "orchestration",
    "dbt": "transformation",
    "Dagster": "orchestration",
    "Snowflake": "serving",
}

SERVICE_ALIASES = {
    "s3": "Amazon S3",
    "aws s3": "Amazon S3",
    "amazon s3 bronze": "Amazon S3",
    "s3 bronze": "Amazon S3",
    "lambda": "AWS Lambda",
    "aws lambda": "AWS Lambda",
    "glue": "AWS Glue",
    "aws glue": "AWS Glue",
    "glue data catalog": "AWS Glue Data Catalog",
    "athena": "Amazon Athena",
    "aws athena": "Amazon Athena",
    "amazon athena": "Amazon Athena",
    "transfer family": "AWS Transfer Family",
    "aws transfer family": "AWS Transfer Family",
    "cloudwatch": "Amazon CloudWatch",
    "aws cloudwatch": "Amazon CloudWatch",
    "amazon cloudwatch": "Amazon CloudWatch",
    "kms": "AWS KMS",
    "aws kms": "AWS KMS",
    "iam": "AWS IAM",
    "aws iam": "AWS IAM",
    "eventbridge": "Amazon EventBridge",
    "aws eventbridge": "Amazon EventBridge",
    "amazon eventbridge": "Amazon EventBridge",
    "step functions": "AWS Step Functions",
    "aws step functions": "AWS Step Functions",
    "dynamodb": "Amazon DynamoDB",
    "aws dynamodb": "Amazon DynamoDB",
    "amazon dynamodb": "Amazon DynamoDB",
    "api gateway": "Amazon API Gateway",
    "aws api gateway": "Amazon API Gateway",
    "amazon api gateway": "Amazon API Gateway",
    "kinesis": "Amazon Kinesis Data Streams",
    "aws kinesis": "Amazon Kinesis Data Streams",
    "amazon kinesis": "Amazon Kinesis Data Streams",
    "data firehose": "Amazon Data Firehose",
    "aws data firehose": "Amazon Data Firehose",
    "amazon data firehose": "Amazon Data Firehose",
    "redshift": "Amazon Redshift",
    "aws redshift": "Amazon Redshift",
    "amazon redshift": "Amazon Redshift",
    "quicksight": "Amazon QuickSight",
    "aws quicksight": "Amazon QuickSight",
    "amazon quicksight": "Amazon QuickSight",
    "secrets manager": "AWS Secrets Manager",
    "aws secrets manager": "AWS Secrets Manager",
    "lake formation": "AWS Lake Formation",
    "aws lake formation": "AWS Lake Formation",
    "ecs fargate": "Amazon ECS Fargate",
    "amazon ecs fargate": "Amazon ECS Fargate",
    "mwaa": "Amazon MWAA",
    "amazon mwaa": "Amazon MWAA",
    "dbt": "dbt",
    "dagster": "Dagster",
    "snowflake": "Snowflake",
}


def coerce_pipeline_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Convert the strict Bedrock contract into the app's internal model shape."""
    if not _uses_external_contract(payload):
        return payload

    services = [_coerce_service(item) for item in _as_list(payload.get("services"))]
    diagram = _coerce_diagram(payload.get("diagram"))
    workflow = [
        _coerce_workflow_step(item, index)
        for index, item in enumerate(_as_list(payload.get("etl_workflow")), start=1)
    ]
    architecture = _string(
        payload.get("architecture_overview") or payload.get("architecture")
    )

    return {
        "title": _string(payload.get("title") or "Modern AWS Data Pipeline")[:120],
        "summary": _string(payload.get("summary") or architecture),
        "architecture": architecture,
        "workflow": workflow,
        "aws_services": services,
        "ingestion_strategy": _layer_from_services("ingestion", services),
        "storage_layer": _layer_from_services("storage", services),
        "transformation_layer": _layer_from_services("transformation", services),
        "orchestration_strategy": _layer_from_services("orchestration", services),
        "monitoring_strategy": _layer_from_services("monitoring", services),
        "security_best_practices": _string_list(
            payload.get("security_best_practices")
        ),
        "cost_optimization": _string_list(payload.get("cost_optimization")),
        "folder_structure": _string(payload.get("folder_structure")),
        "deployment_recommendations": _string_list(
            payload.get("deployment_recommendations")
        ),
        "diagram": diagram,
        "assumptions": _string_list(payload.get("assumptions")),
        "risks": _string_list(payload.get("risks")),
        "generated_by": _string(payload.get("generated_by") or "amazon-bedrock"),
        "generation_warnings": _string_list(payload.get("generation_warnings")),
    }


def normalize_pipeline_spec(spec: PipelineSpec) -> PipelineSpec:
    """Fill gaps that models commonly leave in otherwise valid specs."""
    _normalize_folder_structure(spec)
    _normalize_diagram_shape(spec)
    _ensure_service_mapping(spec)
    _dedupe_service_recommendations(spec)
    _ensure_workflow_service_mentions(spec)
    _ensure_diagram_service_coverage(spec)
    return spec


def default_project_structure() -> str:
    return """project-root/
  terraform/
    main.tf
    variables.tf
    outputs.tf
  src/
    lambda/
      ingest_handler.py
    glue/
      transform_job.py
    shared/
      validation.py
  dbt/
    dbt_project.yml
    models/
      staging/
      marts/
    tests/
  orchestration/
    dagster/
      definitions.py
      schedules.py
  monitoring/
    dashboards/
    alarms/
  docs/
    architecture.md
    runbook.md
  README.md"""


def _uses_external_contract(payload: dict[str, Any]) -> bool:
    return any(
        key in payload for key in ("architecture_overview", "etl_workflow", "services")
    )


def _coerce_service(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        name = canonical_service_name(item.get("name"))
        category = _normalize_category(item.get("category"), service=name)
        description = _string(
            item.get("description") or item.get("purpose") or _purpose_for(name, category)
        )
        return {
            "name": name,
            "category": category,
            "purpose": description,
            "why_selected": _string(
                item.get("why_selected")
                or item.get("why")
                or f"{name} is a strong fit for the {category} layer in this pipeline."
            ),
            "alternatives": _string_list(item.get("alternatives")),
        }

    name = canonical_service_name(item)
    category = _normalize_category(None, service=name)
    return {
        "name": name,
        "category": category,
        "purpose": _purpose_for(name, category),
        "why_selected": f"{name} is a managed option that fits the {category} requirement.",
        "alternatives": [],
    }


def _coerce_workflow_step(item: Any, fallback_order: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {
            "order": fallback_order,
            "name": f"Step {fallback_order}",
            "description": _string(item),
            "inputs": [],
            "outputs": [],
            "owner": None,
        }

    order = item.get("step") or item.get("order") or fallback_order
    try:
        parsed_order = int(order)
    except (TypeError, ValueError):
        parsed_order = fallback_order

    return {
        "order": parsed_order,
        "name": _string(item.get("title") or item.get("name") or f"Step {parsed_order}"),
        "description": _string(item.get("description")),
        "inputs": _string_list(item.get("inputs")),
        "outputs": _string_list(item.get("outputs")),
        "owner": item.get("owner"),
    }


def _coerce_diagram(raw_diagram: Any) -> dict[str, Any]:
    diagram = raw_diagram if isinstance(raw_diagram, dict) else {}
    nodes = [
        _coerce_diagram_node(item, index)
        for index, item in enumerate(_as_list(diagram.get("nodes")), start=1)
    ]
    edges = [
        _coerce_diagram_edge(item, index)
        for index, item in enumerate(_as_list(diagram.get("edges")), start=1)
    ]
    return {"nodes": nodes, "edges": edges}


def _coerce_diagram_node(item: Any, index: int) -> dict[str, Any]:
    node = item if isinstance(item, dict) else {}
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    position = node.get("position") if isinstance(node.get("position"), dict) else {}
    label = _string(node.get("label") or data.get("label") or f"Node {index}")
    service = _string(node.get("service") or data.get("service") or label)
    category = _normalize_category(node.get("category") or data.get("category") or label, service=service)

    return {
        "id": _node_id(_string(node.get("id") or f"node_{index}")),
        "label": label,
        "category": category,
        "service": service,
        "description": _string(node.get("description") or data.get("description")),
        "icon": node.get("icon"),
        "x": _int(node.get("x") or position.get("x"), 0),
        "y": _int(node.get("y") or position.get("y"), 0),
    }


def _coerce_diagram_edge(item: Any, index: int) -> dict[str, Any]:
    edge = item if isinstance(item, dict) else {}
    source = _node_id(_string(edge.get("source")))
    target = _node_id(_string(edge.get("target")))
    return {
        "id": _string(edge.get("id") or f"edge_{index}"),
        "source": source,
        "target": target,
        "label": edge.get("label"),
    }


def _layer_from_services(category: str, services: list[dict[str, Any]]) -> dict[str, Any]:
    names = [
        service["name"]
        for service in services
        if _normalize_category(service.get("category"), service=service.get("name"))
        == category
    ]
    return {
        "name": category.replace("_", " ").title(),
        "services": names,
        "rationale": (
            f"Use {', '.join(names) if names else 'managed AWS services'} to implement "
            f"the {category.replace('_', ' ')} layer with automation, reliability, "
            "and operational controls."
        ),
    }


def _normalize_folder_structure(spec: PipelineSpec) -> None:
    folder_structure = spec.folder_structure.strip()
    if not folder_structure or "s3://" in folder_structure.lower():
        spec.folder_structure = default_project_structure()


def _normalize_diagram_shape(spec: PipelineSpec) -> None:
    x_by_category = {
        category: index * 260 for index, category in enumerate(CORE_FLOW_CATEGORIES)
    }

    for node in spec.diagram.nodes:
        node.category = _normalize_category(node.category, service=node.service)
        if node.x == 0 and node.category in x_by_category and node.category != "source":
            node.x = x_by_category[node.category]
        if node.y == 0 and node.category in SUPPORT_CATEGORIES:
            node.y = 190

    existing = {node.category for node in spec.diagram.nodes}
    missing = [category for category in CORE_FLOW_CATEGORIES if category not in existing]
    for category in missing:
        spec.diagram.nodes.append(
            DiagramNode(
                id=category,
                label=category.title(),
                category=category,
                service=_default_service_for_category(category),
                x=x_by_category[category],
                y=0,
            )
        )

    edge_keys = {(edge.source, edge.target) for edge in spec.diagram.edges}
    ordered_node_ids = [
        node.id for node in spec.diagram.nodes if node.category in CORE_FLOW_CATEGORIES
    ]
    for source, target in zip(ordered_node_ids, ordered_node_ids[1:]):
        if (source, target) not in edge_keys:
            spec.diagram.edges.append(
                DiagramEdge(id=f"{source}-{target}", source=source, target=target)
            )


def _ensure_service_mapping(spec: PipelineSpec) -> None:
    candidates = []
    for layer in (
        spec.ingestion_strategy,
        spec.storage_layer,
        spec.transformation_layer,
        spec.orchestration_strategy,
        spec.monitoring_strategy,
    ):
        candidates.extend(layer.services)
    candidates.extend(node.service for node in spec.diagram.nodes if node.service)
    candidates.extend(_services_mentioned_in_text(_pipeline_text(spec)))

    for name in _unique_services(candidates):
        if not _is_recommendable_service(name):
            continue
        if _service_already_listed(spec.aws_services, name):
            continue
        category = _normalize_category(None, service=name)
        spec.aws_services.append(
            ServiceRecommendation(
                name=name,
                category=category,
                purpose=_purpose_for(name, category),
                why_selected=(
                    f"{name} is referenced in the generated architecture and is required "
                    f"for the {category} capability."
                ),
                alternatives=[],
            )
        )


def _dedupe_service_recommendations(spec: PipelineSpec) -> None:
    seen = set()
    unique_services = []
    for service in spec.aws_services:
        key = canonical_service_name(service.name).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_services.append(service)
    spec.aws_services = unique_services


def _ensure_workflow_service_mentions(spec: PipelineSpec) -> None:
    if not spec.workflow:
        return

    workflow_text = " ".join(
        f"{step.name} {step.description} {' '.join(step.inputs)} {' '.join(step.outputs)}"
        for step in spec.workflow
    ).lower()

    missing_by_category: dict[str, list[str]] = {}
    for service in spec.aws_services:
        if service.name.lower() in workflow_text:
            continue
        category = _normalize_category(service.category, service=service.name)
        missing_by_category.setdefault(category, []).append(service.name)

    if not missing_by_category:
        return

    for category, service_names in missing_by_category.items():
        target = _workflow_target_for_category(spec, category)
        if not target:
            continue
        target.description = (
            f"{target.description.rstrip()} Services used: "
            f"{', '.join(_dedupe(service_names))}."
        )


def _ensure_diagram_service_coverage(spec: PipelineSpec) -> None:
    nodes_by_category: dict[str, DiagramNode] = {}
    for node in spec.diagram.nodes:
        nodes_by_category.setdefault(_normalize_category(node.category, service=node.service), node)

    for service in spec.aws_services:
        category = _normalize_category(service.category, service=service.name)
        node = nodes_by_category.get(category)
        if not node:
            continue
        current = node.service or ""
        if service.name.lower() in current.lower():
            continue
        services = _dedupe([*split_service_names(current), service.name])
        node.service = " / ".join(services[:3])
        if len(services) > 3:
            node.description = (
                f"{node.description.rstrip() + ' ' if node.description else ''}"
                f"Additional services: {', '.join(services[3:])}."
            )


def _workflow_target_for_category(spec: PipelineSpec, category: str):
    keywords_by_category = {
        "source": ("source", "detect", "receive"),
        "ingestion": ("ingest", "detect", "land", "load"),
        "storage": ("storage", "land", "store", "raw"),
        "transformation": ("transform", "clean", "quality", "model"),
        "orchestration": ("orchestrat", "schedule", "coordinate"),
        "serving": ("publish", "serve", "serving", "query"),
        "analytics": ("analytics", "bi", "publish"),
        "monitoring": ("monitor", "observe", "publish", "alert"),
        "security": ("security", "encrypt", "govern", "publish"),
    }
    keywords = keywords_by_category.get(category, ())
    for step in spec.workflow:
        haystack = f"{step.name} {step.description}".lower()
        if any(keyword in haystack for keyword in keywords):
            return step
    return spec.workflow[-1]


def _pipeline_text(spec: PipelineSpec) -> str:
    parts = [
        spec.summary,
        spec.architecture,
        spec.folder_structure,
        *spec.security_best_practices,
        *spec.cost_optimization,
        *spec.deployment_recommendations,
    ]
    for step in spec.workflow:
        parts.extend([step.name, step.description, *step.inputs, *step.outputs])
    return " ".join(parts)


def _services_mentioned_in_text(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for alias, canonical in SERVICE_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            found.append(canonical)
    return found


def split_service_names(value: Any) -> list[str]:
    text = _string(value)
    if not text:
        return []
    separators = r"\s*(?:/|,|\+|\band\b|\bwith\b)\s*"
    parts = [part.strip(" .") for part in re.split(separators, text, flags=re.IGNORECASE)]
    return [canonical_service_name(part) for part in parts if part.strip()]


def _unique_services(values: list[Any]) -> list[str]:
    result = []
    for value in values:
        for service in split_service_names(value):
            if service and service not in result:
                result.append(service)
    return result


def canonical_service_name(value: Any) -> str:
    text = _string(value).strip()
    normalized = re.sub(r"\s+", " ", text.lower())
    return SERVICE_ALIASES.get(normalized, text)


def _service_already_listed(services: list[ServiceRecommendation], candidate: str) -> bool:
    candidate_key = canonical_service_name(candidate).lower()
    existing = set()
    for service in services:
        existing.add(canonical_service_name(service.name).lower())
        for service_part in split_service_names(service.name):
            existing.add(canonical_service_name(service_part).lower())
    return candidate_key in existing


def _is_recommendable_service(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered.startswith(("aws ", "amazon "))
        or lowered in {"dbt", "dagster", "snowflake"}
    )


def _normalize_category(value: Any, service: Any = None) -> str:
    text = _string(value).strip().lower().replace(" layer", "")
    value_canonical = canonical_service_name(value)
    if value_canonical in SERVICE_CATEGORY_HINTS:
        return SERVICE_CATEGORY_HINTS[value_canonical]
    canonical = canonical_service_name(service)
    if canonical in SERVICE_CATEGORY_HINTS:
        return SERVICE_CATEGORY_HINTS[canonical]
    if "source" in text:
        return "source"
    if any(word in text for word in ("ingest", "transfer", "load")):
        return "ingestion"
    if any(word in text for word in ("storage", "store", "bronze", "lake")):
        return "storage"
    if any(word in text for word in ("transform", "clean", "dbt", "glue")):
        return "transformation"
    if any(word in text for word in ("orchestrat", "dagster", "airflow", "schedule")):
        return "orchestration"
    if any(word in text for word in ("serving", "serve", "athena", "warehouse")):
        return "serving"
    if any(word in text for word in ("analytics", "bi", "dashboard")):
        return "analytics"
    if any(word in text for word in ("monitor", "alert", "cloudwatch")):
        return "monitoring"
    if any(word in text for word in ("security", "iam", "kms", "encrypt")):
        return "security"
    return "serving" if canonical == "Snowflake" else text or "serving"


def _default_service_for_category(category: str) -> str:
    return {
        "source": "External Data",
        "ingestion": "AWS Lambda",
        "storage": "Amazon S3",
        "transformation": "AWS Glue",
        "serving": "Amazon Athena",
        "analytics": "Amazon QuickSight",
    }.get(category, "AWS Service")


def _purpose_for(name: str, category: str) -> str:
    return {
        "AWS Transfer Family": "Managed file transfer endpoint for FTP, FTPS, and SFTP ingestion.",
        "AWS Lambda": "Serverless compute for lightweight ingestion, validation, and event handlers.",
        "Amazon S3": "Durable object storage for raw, curated, and published datasets.",
        "AWS Glue": "Serverless ETL and data catalog integration for lake transformations.",
        "AWS Glue Data Catalog": "Shared metadata catalog for S3 tables, partitions, and schemas.",
        "Amazon Athena": "Serverless SQL query layer over S3 data lake tables.",
        "Amazon CloudWatch": "Operational logs, metrics, dashboards, and alarms.",
        "AWS KMS": "Managed encryption keys for data at rest.",
        "AWS IAM": "Least-privilege service roles and access policies.",
        "dbt": "Versioned SQL modeling, tests, and analytics engineering workflows.",
        "Dagster": "Asset-aware orchestration, lineage, and schedule management.",
        "Snowflake": "Cloud data warehouse serving layer for analytics workloads.",
    }.get(name, f"Supports the {category} layer of the data pipeline.")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string_list(value: Any) -> list[str]:
    return [_string(item) for item in _as_list(value) if _string(item)]


def _string(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _node_id(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return normalized.strip("_") or "node"


def _dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result

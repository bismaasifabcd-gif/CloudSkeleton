from __future__ import annotations

from app.models.pipeline import (
    DiagramEdge,
    DiagramNode,
    DiagramSpec,
    LayerRecommendation,
    PipelineSpec,
    ServiceRecommendation,
    WorkflowStep,
)


def _contains(description: str, *needles: str) -> bool:
    lowered = description.lower()
    return any(needle in lowered for needle in needles)


class FallbackPipelineGenerator:
    """Deterministic generator for local development and Bedrock outages."""

    def generate(self, description: str, title: str | None = None) -> PipelineSpec:
        source = self._source(description)
        ingestion = self._ingestion(description)
        transformation = self._transformation(description)
        orchestration = self._orchestration(description)
        serving = self._serving(description)

        nodes = [
            DiagramNode(
                id="source",
                label=source["label"],
                category="source",
                service=source["service"],
                icon="file-input",
                x=0,
                y=0,
            ),
            DiagramNode(
                id="ingestion",
                label="Ingestion",
                category="ingestion",
                service=ingestion["service"],
                icon="upload-cloud",
                x=260,
                y=0,
            ),
            DiagramNode(
                id="storage",
                label="Storage",
                category="storage",
                service="Amazon S3",
                icon="database",
                x=520,
                y=0,
            ),
            DiagramNode(
                id="transformation",
                label="Transformation",
                category="transformation",
                service=transformation["service"],
                icon="workflow",
                x=780,
                y=0,
            ),
            DiagramNode(
                id="orchestration",
                label="Orchestration",
                category="orchestration",
                service=orchestration["service"],
                icon="git-branch",
                x=520,
                y=190,
            ),
            DiagramNode(
                id="serving",
                label="Serving Layer",
                category="serving",
                service=serving["service"],
                icon="table",
                x=1040,
                y=0,
            ),
            DiagramNode(
                id="analytics",
                label="Analytics",
                category="analytics",
                service=serving["analytics"],
                icon="bar-chart",
                x=1300,
                y=0,
            ),
            DiagramNode(
                id="monitoring",
                label="Monitoring",
                category="monitoring",
                service="Amazon CloudWatch",
                icon="activity",
                x=780,
                y=190,
            ),
        ]

        edges = [
            DiagramEdge(id="source-ingestion", source="source", target="ingestion"),
            DiagramEdge(id="ingestion-storage", source="ingestion", target="storage"),
            DiagramEdge(
                id="storage-transformation",
                source="storage",
                target="transformation",
            ),
            DiagramEdge(
                id="transformation-serving",
                source="transformation",
                target="serving",
            ),
            DiagramEdge(id="serving-analytics", source="serving", target="analytics"),
            DiagramEdge(
                id="orchestration-ingestion",
                source="orchestration",
                target="ingestion",
                label="schedule",
            ),
            DiagramEdge(
                id="orchestration-transform",
                source="orchestration",
                target="transformation",
                label="run",
            ),
            DiagramEdge(
                id="monitoring-orchestration",
                source="monitoring",
                target="orchestration",
                label="alerts",
            ),
        ]

        return PipelineSpec(
            title=title or self._title(description),
            summary=(
                "A cloud-native batch data pipeline that ingests external data, "
                "lands raw files in Amazon S3, transforms curated datasets, and "
                "publishes governed data products for analytics."
            ),
            architecture=(
                f"{source['service']} feeds {ingestion['service']}. Raw data lands "
                "in Amazon S3 using bronze/silver/gold prefixes, then "
                f"{transformation['service']} prepares modeled datasets for "
                f"{serving['service']}. {orchestration['service']} coordinates "
                "the workflow and Amazon CloudWatch centralizes logs, metrics, "
                "alarms, and operational dashboards."
            ),
            workflow=[
                WorkflowStep(
                    order=1,
                    name="Detect and validate source arrivals",
                    description=(
                        "Watch the upstream source for new files or batches, "
                        "validate naming conventions, file freshness, checksums, "
                        "and schema expectations before accepting data. Services used: "
                        f"{ingestion['service']}, AWS Lambda."
                    ),
                    inputs=[source["label"]],
                    outputs=["validated batch manifest"],
                    owner="data platform",
                ),
                WorkflowStep(
                    order=2,
                    name="Land raw data",
                    description=(
                        "Copy immutable raw objects into Amazon S3 with partitioned "
                        "keys, metadata tags, versioning, and encryption enabled."
                    ),
                    inputs=["validated batch manifest"],
                    outputs=["s3://raw/bronze objects"],
                    owner="data engineering",
                ),
                WorkflowStep(
                    order=3,
                    name="Profile and clean",
                    description=(
                        "Run quality checks for nulls, duplicates, schema drift, "
                        "and referential integrity. Quarantine rejected records "
                        f"for review. Services used: {transformation['service']}."
                    ),
                    inputs=["s3://raw/bronze objects"],
                    outputs=["s3://curated/silver datasets"],
                    owner="analytics engineering",
                ),
                WorkflowStep(
                    order=4,
                    name="Transform business models",
                    description=(
                        "Apply reusable transformations, dimensional models, "
                        "incremental loads, and tests before publishing serving "
                        "tables."
                    ),
                    inputs=["s3://curated/silver datasets"],
                    outputs=["gold data products"],
                    owner="analytics engineering",
                ),
                WorkflowStep(
                    order=5,
                    name="Publish and observe",
                    description=(
                        "Load or expose curated outputs to the serving layer, "
                        "emit lineage and run metrics, and alert on failures or "
                        "freshness breaches. Services used: "
                        f"{serving['service']}, Amazon CloudWatch."
                    ),
                    inputs=["gold data products"],
                    outputs=[serving["service"]],
                    owner="data operations",
                ),
            ],
            aws_services=[
                ServiceRecommendation(
                    name=ingestion["service"],
                    category="ingestion",
                    purpose=ingestion["purpose"],
                    why_selected=ingestion["why"],
                    alternatives=ingestion["alternatives"],
                ),
                ServiceRecommendation(
                    name="AWS Lambda",
                    category="ingestion",
                    purpose="Serverless ingestion handlers for source polling, validation, and event routing.",
                    why_selected=(
                        "Lambda is cost-effective for lightweight automation around "
                        "file arrivals and validation before landing data in S3."
                    ),
                    alternatives=["AWS Glue", "Amazon ECS Fargate", "AWS Step Functions"],
                ),
                ServiceRecommendation(
                    name="Amazon S3",
                    category="storage",
                    purpose="Durable data lake storage for raw, curated, and published datasets.",
                    why_selected=(
                        "S3 is cost-effective, highly durable, integrates with "
                        "AWS analytics services, and supports lifecycle policies."
                    ),
                    alternatives=["Amazon EFS", "Amazon FSx", "Amazon Redshift"],
                ),
                ServiceRecommendation(
                    name="AWS Glue Data Catalog",
                    category="storage",
                    purpose="Central metadata catalog for tables, schemas, and partitions.",
                    why_selected=(
                        "It gives query engines and transformation jobs a shared "
                        "metadata layer over S3 datasets."
                    ),
                    alternatives=["Apache Hive Metastore", "DataHub"],
                ),
                ServiceRecommendation(
                    name=transformation["service"],
                    category="transformation",
                    purpose=transformation["purpose"],
                    why_selected=transformation["why"],
                    alternatives=transformation["alternatives"],
                ),
                ServiceRecommendation(
                    name=orchestration["service"],
                    category="orchestration",
                    purpose=orchestration["purpose"],
                    why_selected=orchestration["why"],
                    alternatives=orchestration["alternatives"],
                ),
                ServiceRecommendation(
                    name="Amazon EventBridge",
                    category="orchestration",
                    purpose="Schedule pipeline runs and route operational events between services.",
                    why_selected=(
                        "EventBridge gives simple managed scheduling and event delivery "
                        "without maintaining a message broker."
                    ),
                    alternatives=["Amazon SQS", "AWS Step Functions"],
                ),
                ServiceRecommendation(
                    name=serving["service"],
                    category="serving",
                    purpose="Expose curated data products to analysts and downstream consumers.",
                    why_selected=(
                        f"{serving['service']} matches the serving requirement while "
                        "keeping curated data accessible through SQL-based workflows."
                    ),
                    alternatives=["Amazon Redshift", "Snowflake", "Amazon Athena"],
                ),
                ServiceRecommendation(
                    name="Amazon CloudWatch",
                    category="monitoring",
                    purpose="Collect logs, metrics, alarms, and dashboards for pipeline health.",
                    why_selected=(
                        "It is the native operational telemetry surface for "
                        "Lambda, Glue, Step Functions, API Gateway, and DynamoDB."
                    ),
                    alternatives=["Datadog", "Grafana Cloud", "OpenTelemetry Collector"],
                ),
                ServiceRecommendation(
                    name="AWS IAM",
                    category="security",
                    purpose="Least-privilege service roles and policies for AWS services.",
                    why_selected=(
                        "Service-to-service IAM permissions keep pipeline access scoped "
                        "without embedding credentials in code."
                    ),
                    alternatives=["AWS Lake Formation permissions"],
                ),
                ServiceRecommendation(
                    name="AWS KMS",
                    category="security",
                    purpose="Encrypt data at rest in S3, DynamoDB, logs, and secrets.",
                    why_selected="Managed keys keep encryption auditable without custom crypto code.",
                    alternatives=["CloudHSM"],
                ),
            ],
            ingestion_strategy=LayerRecommendation(
                name="Ingestion",
                services=[ingestion["service"], "Amazon EventBridge", "AWS Lambda"],
                rationale=ingestion["rationale"],
            ),
            storage_layer=LayerRecommendation(
                name="Storage",
                services=["Amazon S3", "AWS Glue Data Catalog", "AWS Lake Formation"],
                rationale=(
                    "Use a lakehouse-style S3 layout with immutable bronze data, "
                    "clean silver datasets, and governed gold outputs. Catalog "
                    "datasets for query and apply table-level governance where needed."
                ),
            ),
            transformation_layer=LayerRecommendation(
                name="Transformation",
                services=[transformation["service"], "AWS Glue Data Quality"],
                rationale=transformation["rationale"],
            ),
            orchestration_strategy=LayerRecommendation(
                name="Orchestration",
                services=[orchestration["service"], "Amazon EventBridge"],
                rationale=orchestration["rationale"],
            ),
            monitoring_strategy=LayerRecommendation(
                name="Monitoring",
                services=["Amazon CloudWatch", "AWS CloudTrail", "Amazon EventBridge"],
                rationale=(
                    "Capture job logs, API calls, freshness metrics, failed runs, "
                    "data quality outcomes, and cost signals in one operational view."
                ),
            ),
            security_best_practices=[
                "Use least-privilege IAM roles for ingestion, transformation, and orchestration services.",
                "Encrypt S3 buckets, DynamoDB tables, CloudWatch logs, and secrets with AWS KMS.",
                "Store FTP, warehouse, and application credentials in AWS Secrets Manager.",
                "Enable S3 Block Public Access and require TLS with bucket policies.",
                "Use VPC endpoints for S3, DynamoDB, and Secrets Manager when private network paths are required.",
                "Record control-plane activity with AWS CloudTrail and review access anomalies.",
                "Classify sensitive datasets and apply Lake Formation or warehouse-level access controls.",
            ],
            cost_optimization=[
                "Partition S3 datasets by date and high-cardinality query filters to reduce scan cost.",
                "Apply S3 lifecycle policies to transition old raw data to lower-cost storage classes.",
                "Use incremental dbt or Spark jobs instead of rebuilding full datasets every run.",
                "Right-size Glue workers, Lambda memory, and orchestration retries from observed runtime metrics.",
                "Set AWS Budgets and alarms for data transfer, warehouse credits, and transformation jobs.",
                "Use compression formats such as Parquet with Snappy for analytics-ready datasets.",
            ],
            folder_structure=self._folder_structure(),
            deployment_recommendations=[
                "Deploy infrastructure with AWS CDK using separate dev, staging, and prod stacks.",
                "Host the React frontend with AWS Amplify Hosting and inject the API URL at build time.",
                "Expose FastAPI through Lambda and API Gateway for a low-operations serverless API.",
                "Store generated pipeline history in DynamoDB and export artifacts in S3.",
                "Add CI checks for frontend build, backend tests, CDK synth, and dependency scanning.",
            ],
            diagram=DiagramSpec(nodes=nodes, edges=edges),
            assumptions=[
                "The pipeline is optimized for daily or scheduled batch loads.",
                "Source credentials and warehouse credentials are stored outside application code.",
                "The selected Region supports the required AWS services and Bedrock model.",
            ],
            risks=[
                "Source schema drift can break downstream transformations without contracts and tests.",
                "Long-running transformations may need asynchronous orchestration beyond API request timeouts.",
                "Cross-system egress and external warehouse costs must be monitored separately.",
            ],
            generated_by="local-fallback",
            generation_warnings=[
                "Generated without Amazon Bedrock. Set USE_MOCK_AI=false with AWS credentials for AI output."
            ],
        )

    def _source(self, description: str) -> dict[str, str]:
        if _contains(description, "ftp", "sftp"):
            return {
                "label": "FTP/SFTP Files",
                "service": "External FTP/SFTP server",
            }
        if _contains(description, "api", "rest", "graphql"):
            return {"label": "External API", "service": "External API"}
        if _contains(description, "kafka", "stream"):
            return {"label": "Event Stream", "service": "Apache Kafka"}
        if _contains(description, "database", "postgres", "mysql", "oracle"):
            return {"label": "Operational Database", "service": "Source database"}
        return {"label": "Source Data", "service": "External data source"}

    def _ingestion(self, description: str) -> dict[str, object]:
        if _contains(description, "ftp", "sftp"):
            return {
                "service": "AWS Transfer Family",
                "purpose": "Managed SFTP/FTP endpoint for secure file ingestion into S3.",
                "why": "It removes server maintenance and writes inbound files directly to S3.",
                "alternatives": ["AWS DataSync", "AWS Lambda scheduled pull", "AWS Glue connector"],
                "rationale": (
                    "Use AWS Transfer Family when the upstream system can push files. "
                    "For pull-based FTP sources, schedule a Lambda or container task "
                    "that lands files in the same raw S3 prefix."
                ),
            }
        if _contains(description, "stream", "real-time", "kafka"):
            return {
                "service": "Amazon Kinesis Data Streams",
                "purpose": "Durable streaming ingestion with ordered shards and replay.",
                "why": "It supports low-latency event pipelines and native AWS integrations.",
                "alternatives": ["Amazon MSK", "Amazon Data Firehose", "Amazon SQS"],
                "rationale": (
                    "Use Kinesis for streaming events that need replay and ordering. "
                    "Firehose is a simpler option when delivery to S3 is enough."
                ),
            }
        return {
            "service": "AWS Glue",
            "purpose": "Serverless ingestion jobs and crawlers for batch-oriented data movement.",
            "why": "Glue handles scheduled extracts, schema inference, and scalable Spark jobs.",
            "alternatives": ["AWS Lambda", "AWS DataSync", "Amazon AppFlow"],
            "rationale": (
                "Use Glue for scheduled batch ingestion, especially when files need "
                "schema discovery or Spark-scale preprocessing."
            ),
        }

    def _transformation(self, description: str) -> dict[str, object]:
        if _contains(description, "dbt") and _contains(description, "glue", "aws glue"):
            return {
                "service": "AWS Glue and dbt",
                "purpose": "Serverless data preparation with AWS Glue and governed SQL modeling with dbt.",
                "why": (
                    "Glue is a strong fit for file cleanup and cataloged lake processing, "
                    "while dbt keeps analytics transformations tested and versioned."
                ),
                "alternatives": ["dbt Cloud", "Amazon EMR Serverless", "Amazon Athena CTAS"],
                "rationale": (
                    "Use AWS Glue to cleanse FTP CSV files into partitioned S3 Bronze/Silver "
                    "datasets, then run dbt models against Athena or the serving warehouse "
                    "for curated analytics-ready tables."
                ),
            }
        if _contains(description, "dbt"):
            return {
                "service": "dbt on AWS CodeBuild",
                "purpose": "Versioned SQL transformations, testing, and documentation.",
                "why": "It fits analytics engineering workflows and CI-driven deployments.",
                "alternatives": ["dbt Cloud", "AWS Glue", "Amazon EMR Serverless"],
                "rationale": (
                    "Run dbt jobs in CodeBuild or ECS with warehouse credentials in "
                    "Secrets Manager. Trigger jobs from the orchestrator after raw "
                    "data arrives."
                ),
            }
        if _contains(description, "spark", "large", "big data"):
            return {
                "service": "AWS Glue",
                "purpose": "Serverless Spark transformations at data lake scale.",
                "why": "Glue gives managed Spark without cluster administration.",
                "alternatives": ["Amazon EMR Serverless", "Amazon Athena CTAS", "dbt"],
                "rationale": (
                    "Use Glue Spark jobs for heavy transformations and write curated "
                    "outputs as partitioned Parquet."
                ),
            }
        return {
            "service": "AWS Glue",
            "purpose": "Clean, join, enrich, and publish curated datasets.",
            "why": "Glue integrates with S3 and the Data Catalog for lake transformations.",
            "alternatives": ["dbt", "Amazon EMR Serverless", "AWS Lambda"],
            "rationale": (
                "Use Glue jobs for reusable transformation code and Glue Data Quality "
                "rules for validation gates."
            ),
        }

    def _orchestration(self, description: str) -> dict[str, object]:
        if _contains(description, "dagster"):
            return {
                "service": "Dagster on Amazon ECS Fargate",
                "purpose": "Asset-aware orchestration with lineage and software-defined assets.",
                "why": "It matches teams that already use Dagster and need rich data asset metadata.",
                "alternatives": ["AWS Step Functions", "Amazon MWAA", "AWS Glue Workflows"],
                "rationale": (
                    "Run Dagster webserver and daemon on ECS Fargate, store secrets in "
                    "Secrets Manager, and emit run telemetry to CloudWatch."
                ),
            }
        if _contains(description, "airflow"):
            return {
                "service": "Amazon MWAA",
                "purpose": "Managed Apache Airflow for DAG-based orchestration.",
                "why": "It reduces Airflow operations while preserving the Airflow ecosystem.",
                "alternatives": ["AWS Step Functions", "Dagster on ECS Fargate"],
                "rationale": (
                    "Use Amazon MWAA when the organization standardizes on Airflow DAGs "
                    "and provider operators."
                ),
            }
        return {
            "service": "AWS Step Functions",
            "purpose": "Serverless workflow orchestration with retries and state tracking.",
            "why": "It is operationally simple, integrates with AWS services, and has visual run history.",
            "alternatives": ["Amazon MWAA", "Dagster on ECS Fargate", "AWS Glue Workflows"],
            "rationale": (
                "Use Step Functions to coordinate ingestion, validation, transformation, "
                "publishing, retries, and failure notifications."
            ),
        }

    def _serving(self, description: str) -> dict[str, str]:
        if _contains(description, "snowflake"):
            return {"service": "Snowflake", "analytics": "BI and SQL tools"}
        if _contains(description, "redshift"):
            return {"service": "Amazon Redshift", "analytics": "Amazon QuickSight"}
        return {"service": "Amazon Athena", "analytics": "Amazon QuickSight"}

    def _title(self, description: str) -> str:
        if _contains(description, "csv") and _contains(description, "snowflake"):
            return "CSV to Snowflake Data Pipeline"
        if _contains(description, "stream", "real-time"):
            return "Streaming Analytics Data Pipeline"
        return "Modern AWS Data Pipeline"

    def _folder_structure(self) -> str:
        return """data-platform/
  ingestion/
    jobs/
    schemas/
    tests/
  transformation/
    dbt_project.yml
    models/
    macros/
    tests/
  orchestration/
    definitions/
    schedules/
    sensors/
  infrastructure/
    cdk/
    environments/
  monitoring/
    dashboards/
    alarms/
  docs/
    architecture.md
    runbook.md"""

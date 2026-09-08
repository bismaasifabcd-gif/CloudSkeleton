# AWS Services and Rationale

## Application Platform

| Service | Why it is used |
| --- | --- |
| AWS Amplify Hosting | Managed frontend hosting for the Vite static bundle with simple deployment artifacts. |
| Amazon API Gateway HTTP API | Public HTTPS entry point for the backend with lower overhead than REST API for this MVP. |
| AWS Lambda | Runs FastAPI without servers and scales with request volume. |
| Amazon Bedrock | Generates pipeline architectures from prompts using managed foundation models. |
| Amazon DynamoDB | Persists pipeline generation history with simple key-value and user-history access patterns. |
| Amazon S3 | Stores generated Markdown and JSON exports durably and cheaply. |
| Amazon CloudWatch | Collects backend logs and operational signals. |
| AWS X-Ray | Traces Lambda requests and downstream AWS SDK calls. |
| AWS IAM | Grants the backend exact service permissions required for DynamoDB, S3, and Bedrock. |
| AWS KMS | Recommended encryption control for production datasets and secrets. |
| AWS CDK / CloudFormation | Reproducible infrastructure deployment and change tracking. |

## Generated Data Pipeline

| Service | Why it is selected |
| --- | --- |
| AWS Transfer Family | Fits FTP/SFTP CSV ingestion without managing file-transfer servers. |
| Amazon S3 Bronze | Provides immutable raw storage for replay, audit, and downstream transformation. |
| AWS Glue | Cleans CSV data, handles schema evolution, and writes curated lake datasets. |
| Amazon Athena | Provides serverless SQL access over curated S3 data. |
| Amazon CloudWatch | Monitors ingestion failures, transformation jobs, orchestration failures, and API health. |
| AWS IAM | Enforces least-privilege access between pipeline services. |
| AWS KMS | Protects stored data and export artifacts with managed encryption keys. |

dbt and Dagster are not AWS services, but the generator preserves them when the user explicitly asks for them. A practical AWS deployment would run dbt in CodeBuild, ECS Fargate, or dbt Cloud, and run Dagster on ECS Fargate or a managed Dagster provider.

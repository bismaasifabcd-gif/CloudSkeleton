export const samplePrompt = `Pipeline:
  Source:
    - FTP CSV

  Ingestion:
    - AWS Transfer Family

  Storage:
    - Amazon S3 Bronze

  Transformation:
    - AWS Glue
    - dbt

  Orchestration:
    - Dagster

  Serving:
    - Amazon Athena

  Monitoring:
    - CloudWatch

  Security:
    - IAM
    - KMS`;

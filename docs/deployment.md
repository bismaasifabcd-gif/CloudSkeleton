# Deployment Guide

## One-Command AWS Deployment

From Windows PowerShell:

```powershell
npm install
npm run deploy -- -Stage dev -Region ap-southeast-2 -Profile aws-beta -BedrockModelId amazon.nova-pro-v1:0
```

From macOS/Linux:

```bash
npm install
STAGE=dev AWS_REGION=ap-southeast-2 BEDROCK_MODEL_ID=amazon.nova-pro-v1:0 bash scripts/deploy-all.sh
```

## What Gets Deployed

- API Gateway HTTP API
- Lambda FastAPI backend
- DynamoDB history table with a user and creation-time index
- S3 export bucket
- IAM role and policies for backend access to DynamoDB, S3, and Bedrock
- CloudWatch log retention for Lambda
- Amplify Hosting app and branch
- Frontend static deployment artifact

## Required AWS Setup

1. Authenticate the AWS CLI for your AWS project.
2. Use the selected Region for all resources.
3. Enable the required Bedrock model in that selected Region.
4. Bootstrap CDK once:

```bash
cd infrastructure
npx cdk bootstrap
```

## Deployment Parameters

PowerShell:

```powershell
npm run deploy -- -Stage prod -Region ap-southeast-2 -BedrockModelId amazon.nova-pro-v1:0 -CorsOrigins https://example.com
```

Bash:

```bash
STAGE=prod \
AWS_REGION=ap-southeast-2 \
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0 \
CORS_ORIGINS=https://example.com \
bash scripts/deploy-all.sh
```

## Notes for the New AWS Experience

- Create resources only in your selected Region.
- Human access is managed through team members in AWS Settings.
- IAM in this project is used for service-to-service permissions, not for creating team members.
- Billing, spend limits, invoices, and team members are managed in AWS Settings.
- If resources suddenly become inaccessible, check whether a spend limit paused the AWS project.

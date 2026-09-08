import * as cdk from 'aws-cdk-lib';
import { DataPipelineGeneratorStack } from '../lib/data-pipeline-generator-stack.js';

const app = new cdk.App();

const stage = app.node.tryGetContext('stage') ?? process.env.STAGE ?? 'dev';
const region =
  app.node.tryGetContext('region') ??
  process.env.CDK_DEFAULT_REGION ??
  process.env.AWS_REGION ??
  'us-east-1';
const account = process.env.CDK_DEFAULT_ACCOUNT;

new DataPipelineGeneratorStack(app, `AiDataPipelineGenerator-${stage}`, {
  env: {
    account,
    region,
  },
  stage,
  bedrockModelId:
    app.node.tryGetContext('bedrockModelId') ??
    process.env.BEDROCK_MODEL_ID ??
    'us.anthropic.claude-sonnet-4-6',
  corsOrigins:
    app.node.tryGetContext('corsOrigins') ??
    process.env.CORS_ORIGINS ??
    '*',
});

# AWS CDK Infrastructure Skill

## Purpose
Expert knowledge for building production-ready AWS infrastructure using the Cloud Development Kit (CDK) with TypeScript, focusing on serverless architectures and best practices.

## Core CDK Patterns

### Stack Organization
```typescript
// lib/ai-pipeline-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

interface AiPipelineStackProps extends cdk.StackProps {
  readonly stage: string;
  readonly bedrockModelId: string;
  readonly region: string;
}

export class AiPipelineStack extends cdk.Stack {
  public readonly apiUrl: string;
  public readonly historyTable: dynamodb.Table;
  public readonly exportsBucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: AiPipelineStackProps) {
    super(scope, id, props);

    const { stage, bedrockModelId, region } = props;

    // DynamoDB Table for generation history
    this.historyTable = this.createHistoryTable(stage);

    // S3 Bucket for exports
    this.exportsBucket = this.createExportsBucket(stage);

    // Lambda function
    const lambdaFunction = this.createLambdaFunction(stage, bedrockModelId, region);

    // API Gateway
    const api = this.createApiGateway(lambdaFunction, stage);
    
    this.apiUrl = api.url;

    // Permissions
    this.setupPermissions(lambdaFunction);

    // Outputs
    this.createOutputs();
  }

  private createHistoryTable(stage: string): dynamodb.Table {
    return new dynamodb.Table(this, 'HistoryTable', {
      tableName: `ai-pipeline-history-${stage}`,
      partitionKey: {
        name: 'userId',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'id',
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecovery: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Use RETAIN for production
      globalSecondaryIndexes: [
        {
          indexName: 'timestamp-index',
          partitionKey: {
            name: 'userId',
            type: dynamodb.AttributeType.STRING,
          },
          sortKey: {
            name: 'timestamp',
            type: dynamodb.AttributeType.NUMBER,
          },
        },
      ],
    });
  }

  private createExportsBucket(stage: string): s3.Bucket {
    return new s3.Bucket(this, 'ExportsBucket', {
      bucketName: `ai-pipeline-exports-${stage}-${this.account}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      lifecycleRules: [
        {
          id: 'delete-old-versions',
          expiration: cdk.Duration.days(90),
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Use RETAIN for production
    });
  }

  private createLambdaFunction(
    stage: string, 
    bedrockModelId: string, 
    region: string
  ): lambda.Function {
    const lambdaFunction = new lambda.Function(this, 'ApiFunction', {
      functionName: `ai-pipeline-api-${stage}`,
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'app.main.handler',
      code: lambda.Code.fromAsset('../backend'),
      timeout: cdk.Duration.minutes(5),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        AWS_REGION: region,
        BEDROCK_MODEL_ID: bedrockModelId,
        BEDROCK_MAX_TOKENS: '4000',
        BEDROCK_TEMPERATURE: '0.7',
        HISTORY_TABLE_NAME: this.historyTable.tableName,
        EXPORT_BUCKET_NAME: this.exportsBucket.bucketName,
        CORS_ORIGINS: '*', // Configure for production
        USE_MOCK_AI: 'false',
        ENABLE_FALLBACK: 'true',
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
      tracing: lambda.Tracing.ACTIVE,
    });

    return lambdaFunction;
  }

  private createApiGateway(lambdaFunction: lambda.Function, stage: string): apigateway.RestApi {
    const api = new apigateway.RestApi(this, 'ApiGateway', {
      restApiName: `ai-pipeline-api-${stage}`,
      description: 'AI Data Pipeline Generator API',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS, // Configure for production
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Amz-Security-Token',
        ],
      },
      deployOptions: {
        stageName: stage,
        throttle: {
          rateLimit: 100,
          burstLimit: 200,
        },
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        metricsEnabled: true,
      },
    });

    // Lambda integration
    const lambdaIntegration = new apigateway.LambdaIntegration(lambdaFunction, {
      requestTemplates: { 'application/json': '{ "statusCode": "200" }' },
    });

    // API routes
    api.root.addMethod('ANY', lambdaIntegration);
    api.root.addProxy({
      defaultIntegration: lambdaIntegration,
      anyMethod: true,
    });

    return api;
  }

  private setupPermissions(lambdaFunction: lambda.Function): void {
    // DynamoDB permissions
    this.historyTable.grantReadWriteData(lambdaFunction);

    // S3 permissions
    this.exportsBucket.grantReadWrite(lambdaFunction);

    // Bedrock permissions
    lambdaFunction.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'bedrock:InvokeModel',
          'bedrock:InvokeModelWithResponseStream',
        ],
        resources: [
          `arn:aws:bedrock:${this.region}::foundation-model/*`,
        ],
      })
    );
  }

  private createOutputs(): void {
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: this.apiUrl,
      description: 'API Gateway URL',
      exportName: `ai-pipeline-api-url-${this.stackName}`,
    });

    new cdk.CfnOutput(this, 'HistoryTableName', {
      value: this.historyTable.tableName,
      description: 'DynamoDB History Table Name',
      exportName: `ai-pipeline-history-table-${this.stackName}`,
    });

    new cdk.CfnOutput(this, 'ExportsBucketName', {
      value: this.exportsBucket.bucketName,
      description: 'S3 Exports Bucket Name',
      exportName: `ai-pipeline-exports-bucket-${this.stackName}`,
    });
  }
}
```

### Environment Configuration
```typescript
// lib/config.ts
export interface EnvironmentConfig {
  readonly stage: string;
  readonly region: string;
  readonly bedrockModelId: string;
  readonly lambdaMemorySize: number;
  readonly apiThrottling: {
    rateLimit: number;
    burstLimit: number;
  };
  readonly retentionDays: number;
  readonly enableXRayTracing: boolean;
  readonly corsOrigins: string[];
}

export const getEnvironmentConfig = (stage: string): EnvironmentConfig => {
  const configs: Record<string, EnvironmentConfig> = {
    dev: {
      stage: 'dev',
      region: 'us-east-1',
      bedrockModelId: 'amazon.nova-pro-v1:0',
      lambdaMemorySize: 512,
      apiThrottling: {
        rateLimit: 10,
        burstLimit: 20,
      },
      retentionDays: 3,
      enableXRayTracing: false,
      corsOrigins: ['*'],
    },
    prod: {
      stage: 'prod',
      region: 'us-east-1',
      bedrockModelId: 'amazon.nova-pro-v1:0',
      lambdaMemorySize: 2048,
      apiThrottling: {
        rateLimit: 100,
        burstLimit: 200,
      },
      retentionDays: 30,
      enableXRayTracing: true,
      corsOrigins: ['https://app.example.com'],
    },
  };

  const config = configs[stage];
  if (!config) {
    throw new Error(`No configuration found for stage: ${stage}`);
  }

  return config;
};
```

## Advanced CDK Constructs

### Monitoring Construct
```typescript
// lib/constructs/monitoring-construct.ts
import * as cdk from 'aws-cdk-lib';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as snsSubscriptions from 'aws-cdk-lib/aws-sns-subscriptions';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import { Construct } from 'constructs';

interface MonitoringConstructProps {
  readonly lambdaFunction: lambda.Function;
  readonly apiGateway: apigateway.RestApi;
  readonly stage: string;
  readonly alertEmail?: string;
}

export class MonitoringConstruct extends Construct {
  public readonly dashboard: cloudwatch.Dashboard;
  public readonly alertTopic: sns.Topic;

  constructor(scope: Construct, id: string, props: MonitoringConstructProps) {
    super(scope, id);

    const { lambdaFunction, apiGateway, stage, alertEmail } = props;

    // SNS Topic for alerts
    this.alertTopic = new sns.Topic(this, 'AlertTopic', {
      topicName: `ai-pipeline-alerts-${stage}`,
      displayName: 'AI Pipeline Alerts',
    });

    if (alertEmail) {
      this.alertTopic.addSubscription(
        new snsSubscriptions.EmailSubscription(alertEmail)
      );
    }

    // CloudWatch Alarms
    this.createAlarms(lambdaFunction, apiGateway);

    // CloudWatch Dashboard
    this.dashboard = this.createDashboard(lambdaFunction, apiGateway, stage);
  }

  private createAlarms(
    lambdaFunction: lambda.Function,
    apiGateway: apigateway.RestApi
  ): void {
    // Lambda Error Rate Alarm
    const lambdaErrorAlarm = new cloudwatch.Alarm(this, 'LambdaErrorAlarm', {
      alarmName: 'ai-pipeline-lambda-errors',
      metric: lambdaFunction.metricErrors({
        period: cdk.Duration.minutes(5),
        statistic: 'Sum',
      }),
      threshold: 5,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'Lambda function error rate is too high',
    });

    lambdaErrorAlarm.addAlarmAction(
      new cloudwatch.SnsAction(this.alertTopic)
    );

    // API Gateway 5xx Errors
    const apiErrorAlarm = new cloudwatch.Alarm(this, 'ApiErrorAlarm', {
      alarmName: 'ai-pipeline-api-5xx-errors',
      metric: apiGateway.metricServerError({
        period: cdk.Duration.minutes(5),
        statistic: 'Sum',
      }),
      threshold: 10,
      evaluationPeriods: 2,
      treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
      alarmDescription: 'API Gateway 5xx error rate is too high',
    });

    apiErrorAlarm.addAlarmAction(
      new cloudwatch.SnsAction(this.alertTopic)
    );
  }

  private createDashboard(
    lambdaFunction: lambda.Function,
    apiGateway: apigateway.RestApi,
    stage: string
  ): cloudwatch.Dashboard {
    const dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
      dashboardName: `ai-pipeline-${stage}`,
    });

    // API Gateway Metrics
    dashboard.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API Gateway Requests',
        left: [
          apiGateway.metricCount({
            period: cdk.Duration.minutes(5),
            statistic: 'Sum',
          }),
        ],
        width: 12,
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration',
        left: [
          lambdaFunction.metricDuration({
            period: cdk.Duration.minutes(5),
            statistic: 'Average',
          }),
        ],
        width: 12,
      })
    );

    return dashboard;
  }
}
```

## Security Best Practices

### IAM Policy Management
```typescript
// Create least-privilege policies
const bedrockPolicy = new iam.PolicyStatement({
  effect: iam.Effect.ALLOW,
  actions: [
    'bedrock:InvokeModel',
    'bedrock:InvokeModelWithResponseStream',
  ],
  resources: [
    `arn:aws:bedrock:${this.region}::foundation-model/amazon.nova-pro-v1:0`,
  ],
});

// Use resource-specific grants
this.historyTable.grantReadWriteData(lambdaFunction);
this.exportsBucket.grantReadWrite(lambdaFunction, 'exports/*');
```

### Encryption and Security
```typescript
// Enable encryption for all resources
const kmsKey = new kms.Key(this, 'EncryptionKey', {
  alias: `ai-pipeline-${stage}`,
  description: 'KMS key for AI Pipeline encryption',
  enableKeyRotation: true,
});

// Apply encryption to resources
const encryptedBucket = new s3.Bucket(this, 'EncryptedBucket', {
  encryption: s3.BucketEncryption.KMS,
  encryptionKey: kmsKey,
  blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
});
```

## Testing Infrastructure

### CDK Unit Tests
```typescript
// test/ai-pipeline-stack.test.ts
import * as cdk from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { AiPipelineStack } from '../lib/ai-pipeline-stack';

describe('AiPipelineStack', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new AiPipelineStack(app, 'TestStack', {
      stage: 'test',
      bedrockModelId: 'amazon.nova-pro-v1:0',
      region: 'us-east-1',
    });
    template = Template.fromStack(stack);
  });

  test('creates DynamoDB table with correct configuration', () => {
    template.hasResourceProperties('AWS::DynamoDB::Table', {
      BillingMode: 'PAY_PER_REQUEST',
      AttributeDefinitions: [
        {
          AttributeName: 'userId',
          AttributeType: 'S',
        },
      ],
    });
  });

  test('creates Lambda function with proper environment', () => {
    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'python3.12',
      Handler: 'app.main.handler',
      Environment: {
        Variables: {
          STAGE: 'test',
          BEDROCK_MODEL_ID: 'amazon.nova-pro-v1:0',
        },
      },
    });
  });

  test('creates proper IAM permissions', () => {
    template.hasResourceProperties('AWS::IAM::Policy', {
      PolicyDocument: {
        Statement: [
          {
            Effect: 'Allow',
            Action: [
              'bedrock:InvokeModel',
              'bedrock:InvokeModelWithResponseStream',
            ],
          },
        ],
      },
    });
  });
});
```

## Deployment Automation

### Deployment Script
```typescript
// scripts/deploy.ts
import { execSync } from 'child_process';
import * as fs from 'fs';

interface DeploymentOptions {
  stage: string;
  region: string;
  profile?: string;
  bedrockModelId: string;
}

export const deployStack = async (options: DeploymentOptions): Promise<void> => {
  const { stage, region, profile, bedrockModelId } = options;

  console.log(`🚀 Deploying AI Pipeline to ${stage} environment...`);

  try {
    // Set AWS environment
    process.env.CDK_DEFAULT_REGION = region;
    if (profile) {
      process.env.AWS_PROFILE = profile;
    }

    // Synthesize CDK
    console.log('📦 Synthesizing CDK templates...');
    execSync(
      `npx cdk synth --context stage=${stage} --context bedrockModelId=${bedrockModelId}`,
      { stdio: 'inherit' }
    );

    // Deploy stack
    console.log('☁️ Deploying to AWS...');
    execSync(
      `npx cdk deploy --context stage=${stage} --context bedrockModelId=${bedrockModelId} --require-approval never`,
      { stdio: 'inherit' }
    );

    // Get stack outputs
    const outputs = await getStackOutputs(stage);
    console.log('✅ Deployment completed!');
    console.log('📊 Stack Outputs:', outputs);

  } catch (error) {
    console.error('❌ Deployment failed:', error);
    throw error;
  }
};

const getStackOutputs = async (stage: string): Promise<Record<string, string>> => {
  try {
    const result = execSync(
      `aws cloudformation describe-stacks --stack-name AiPipelineStack-${stage} --query "Stacks[0].Outputs" --output json`,
      { encoding: 'utf-8' }
    );

    const outputs = JSON.parse(result);
    return outputs.reduce((acc: Record<string, string>, output: any) => {
      acc[output.OutputKey] = output.OutputValue;
      return acc;
    }, {});
  } catch (error) {
    console.error('Failed to retrieve stack outputs:', error);
    return {};
  }
};
```

#[[file:infrastructure/lib/ai-pipeline-stack.ts]]
#[[file:infrastructure/lib/config.ts]]
#[[file:infrastructure/bin/ai-pipeline.ts]]
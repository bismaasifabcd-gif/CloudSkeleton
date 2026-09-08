import { execFileSync } from 'node:child_process';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as cdk from 'aws-cdk-lib';
import * as amplify from 'aws-cdk-lib/aws-amplify';
import * as apigatewayv2 from 'aws-cdk-lib/aws-apigatewayv2';
import * as integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import { Construct } from 'constructs';

const currentDir = path.dirname(fileURLToPath(import.meta.url));

function pruneDirectory(parentPath: string, keepNames: Set<string>): void {
  if (!fs.existsSync(parentPath)) {
    return;
  }
  for (const entry of fs.readdirSync(parentPath, { withFileTypes: true })) {
    if (entry.isDirectory() && !keepNames.has(entry.name)) {
      fs.rmSync(path.join(parentPath, entry.name), { recursive: true, force: true });
    }
  }
}

function packageLambdaAsset(backendPath: string): string {
  const projectRoot = path.join(backendPath, '..');
  const buildDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-dpg-lambda-'));
  const artifactDir = path.join(projectRoot, '.deployment', 'lambda');
  const artifactPath = path.join(artifactDir, 'api.zip');
  const python = process.env.PYTHON ?? (process.platform === 'win32' ? 'python' : 'python3');
  const cacheDir = path.join(projectRoot, '.pip-cache');

  fs.mkdirSync(buildDir, { recursive: true });
  fs.mkdirSync(artifactDir, { recursive: true });
  fs.mkdirSync(cacheDir, { recursive: true });

  execFileSync(
    python,
    [
      '-m',
      'pip',
      'install',
      '-r',
      path.join(backendPath, 'requirements-lambda.txt'),
      '-t',
      buildDir,
      '--platform',
      'manylinux2014_aarch64',
      '--implementation',
      'cp',
      '--python-version',
      '3.12',
      '--abi',
      'cp312',
      '--only-binary=:all:',
      '--no-compile',
      '--upgrade',
      '--cache-dir',
      cacheDir,
    ],
    { stdio: 'inherit' },
  );

  fs.cpSync(path.join(backendPath, 'app'), path.join(buildDir, 'app'), {
    recursive: true,
  });
  pruneDirectory(
    path.join(buildDir, 'botocore', 'data'),
    new Set(['_retry.json', 'endpoints.json', 'partitions.json', 'bedrock-runtime', 'dynamodb', 's3']),
  );
  pruneDirectory(path.join(buildDir, 'boto3', 'data'), new Set(['dynamodb', 's3']));
  fs.rmSync(artifactPath, { force: true });

  const zipScript = [
    'import os, sys, zipfile',
    'source, target = sys.argv[1], sys.argv[2]',
    'with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:',
    '    for root, dirs, files in os.walk(source):',
    '        dirs[:] = [d for d in dirs if d != "__pycache__"]',
    '        for file_name in files:',
    '            full_path = os.path.join(root, file_name)',
    '            rel_path = os.path.relpath(full_path, source)',
    '            archive.write(full_path, rel_path)',
  ].join('\n');

  execFileSync(python, ['-c', zipScript, buildDir, artifactPath], { stdio: 'inherit' });
  return artifactPath;
}

interface DataPipelineGeneratorStackProps extends cdk.StackProps {
  readonly stage: string;
  readonly bedrockModelId: string;
  readonly corsOrigins: string;
}

export class DataPipelineGeneratorStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DataPipelineGeneratorStackProps) {
    super(scope, id, props);

    const historyTable = new dynamodb.Table(this, 'HistoryTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
    });

    historyTable.addGlobalSecondaryIndex({
      indexName: 'userIdCreatedAtIndex',
      partitionKey: { name: 'userId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.ALL,
    });

    const exportBucket = new s3.Bucket(this, 'ExportBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [
        {
          id: 'MoveOldExportsToInfrequentAccess',
          prefix: 'exports/',
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: cdk.Duration.days(30),
            },
          ],
        },
      ],
    });

    const backendPath = path.join(currentDir, '..', '..', 'backend');
    const lambdaArtifactPath = packageLambdaAsset(backendPath);
    const apiLogGroup = new logs.LogGroup(this, 'ApiFunctionLogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const apiFunction = new lambda.Function(this, 'ApiFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      architecture: lambda.Architecture.ARM_64,
      handler: 'app.adapter.handler',
      code: lambda.Code.fromAsset(lambdaArtifactPath),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(29),
      tracing: lambda.Tracing.ACTIVE,
      logGroup: apiLogGroup,
      environment: {
        APP_ENV: props.stage,
        HISTORY_TABLE_NAME: historyTable.tableName,
        EXPORT_BUCKET_NAME: exportBucket.bucketName,
        BEDROCK_MODEL_ID: props.bedrockModelId,
        BEDROCK_MAX_TOKENS: '4096',
        BEDROCK_TEMPERATURE: '0.2',
        ENABLE_FALLBACK: 'true',
        USE_MOCK_AI: 'false',
        CORS_ORIGINS: props.corsOrigins,
      },
    });

    historyTable.grantReadWriteData(apiFunction);
    exportBucket.grantReadWrite(apiFunction, 'exports/*');
    apiFunction.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: ['*'],
      }),
    );

    const allowedOrigins = props.corsOrigins
      .split(',')
      .map((origin) => origin.trim())
      .filter(Boolean);
    const allowAllOrigins = allowedOrigins.includes('*') || allowedOrigins.length === 0;

    const httpApi = new apigatewayv2.HttpApi(this, 'HttpApi', {
      apiName: `ai-data-pipeline-generator-${props.stage}`,
      corsPreflight: {
        allowHeaders: ['content-type', 'authorization', 'x-requested-with'],
        allowMethods: [
          apigatewayv2.CorsHttpMethod.GET,
          apigatewayv2.CorsHttpMethod.POST,
          apigatewayv2.CorsHttpMethod.DELETE,
          apigatewayv2.CorsHttpMethod.OPTIONS,
        ],
        allowOrigins: allowAllOrigins ? ['*'] : allowedOrigins,
        maxAge: cdk.Duration.days(1),
      },
    });

    const integration = new integrations.HttpLambdaIntegration('ApiIntegration', apiFunction);
    httpApi.addRoutes({
      path: '/{proxy+}',
      methods: [apigatewayv2.HttpMethod.ANY],
      integration,
    });

    const amplifyApp = new amplify.CfnApp(this, 'FrontendAmplifyApp', {
      name: `ai-data-pipeline-generator-${props.stage}`,
      platform: 'WEB',
      environmentVariables: [
        {
          name: 'VITE_API_BASE_URL',
          value: httpApi.apiEndpoint,
        },
      ],
      customRules: [
        {
          source: '</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>',
          target: '/index.html',
          status: '200',
        },
      ],
    });

    const branchName = props.stage;
    const branch = new amplify.CfnBranch(this, 'FrontendBranch', {
      appId: amplifyApp.attrAppId,
      branchName,
      enableAutoBuild: false,
      framework: 'React',
      stage: props.stage === 'prod' ? 'PRODUCTION' : 'DEVELOPMENT',
    });

    new cdk.CfnOutput(this, 'ApiUrl', {
      value: httpApi.apiEndpoint,
      description: 'API Gateway HTTP API endpoint.',
    });
    new cdk.CfnOutput(this, 'HistoryTableName', {
      value: historyTable.tableName,
      description: 'DynamoDB table used for pipeline generation history.',
    });
    new cdk.CfnOutput(this, 'ExportBucketName', {
      value: exportBucket.bucketName,
      description: 'S3 bucket used for generated export artifacts.',
    });
    new cdk.CfnOutput(this, 'AmplifyAppId', {
      value: amplifyApp.attrAppId,
      description: 'Amplify Hosting app ID.',
    });
    new cdk.CfnOutput(this, 'AmplifyBranchName', {
      value: branchName,
      description: 'Amplify Hosting branch name.',
    });
    new cdk.CfnOutput(this, 'AmplifyUrl', {
      value: `https://${branchName}.${amplifyApp.attrDefaultDomain}`,
      description: 'Amplify Hosting URL after the frontend artifact is deployed.',
    });

    branch.node.addDependency(amplifyApp);
  }
}

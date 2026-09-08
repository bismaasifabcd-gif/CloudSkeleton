param(
  [string]$Stage = "dev",
  [string]$Region = $(if ($env:AWS_REGION) { $env:AWS_REGION } else { "us-east-1" }),
  [string]$Profile = $(if ($env:AWS_PROFILE) { $env:AWS_PROFILE } else { "" }),
  [string]$BedrockModelId = $(if ($env:BEDROCK_MODEL_ID) { $env:BEDROCK_MODEL_ID } else { "us.anthropic.claude-sonnet-4-6" }),
  [string]$CorsOrigins = $(if ($env:CORS_ORIGINS) { $env:CORS_ORIGINS } else { "*" })
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$OutputsPath = Join-Path $Root ".deployment\cdk-outputs.json"
$ZipPath = Join-Path $Root ".deployment\frontend.zip"
$FrontendDist = Join-Path $Root "frontend\dist"

New-Item -ItemType Directory -Force -Path (Split-Path $OutputsPath) | Out-Null

Write-Host "Deploying backend and storage with AWS CDK..."
Push-Location (Join-Path $Root "infrastructure")
try {
  $env:AWS_REGION = $Region
  if ($Profile) {
    $env:AWS_PROFILE = $Profile
    npx cdk deploy --all --profile $Profile --require-approval never --outputs-file $OutputsPath -c stage=$Stage -c region=$Region -c bedrockModelId=$BedrockModelId -c corsOrigins=$CorsOrigins
  } else {
    npx cdk deploy --all --require-approval never --outputs-file $OutputsPath -c stage=$Stage -c region=$Region -c bedrockModelId=$BedrockModelId -c corsOrigins=$CorsOrigins
  }
}
finally {
  Pop-Location
}

$Outputs = Get-Content $OutputsPath -Raw | ConvertFrom-Json
$StackName = ($Outputs.PSObject.Properties | Select-Object -First 1).Name
$StackOutputs = $Outputs.$StackName
$ApiUrl = $StackOutputs.ApiUrl
$AmplifyAppId = $StackOutputs.AmplifyAppId
$AmplifyBranchName = $StackOutputs.AmplifyBranchName
$AmplifyUrl = $StackOutputs.AmplifyUrl

Write-Host "Building frontend with API URL $ApiUrl..."
Push-Location $Root
try {
  $env:VITE_API_BASE_URL = $ApiUrl
  npm --workspace frontend run build
}
finally {
  Pop-Location
}

Write-Host "Packaging frontend for Amplify Hosting..."
if (Test-Path $ZipPath) {
  Remove-Item -LiteralPath $ZipPath -Force
}
$Python = Join-Path $Root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
  $Python = "python"
}
& $Python -c @'
import pathlib
import sys
import zipfile

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
with zipfile.ZipFile(target, chr(119), zipfile.ZIP_DEFLATED) as archive:
    for path in source.rglob(chr(42)):
        if path.is_file():
            archive.write(path, path.relative_to(source).as_posix())
'@ $FrontendDist $ZipPath
if ($LASTEXITCODE -ne 0) {
  throw "Failed to package frontend artifact."
}

Write-Host "Uploading frontend artifact to Amplify..."
if ($Profile) {
  $DeploymentJson = aws amplify create-deployment --app-id $AmplifyAppId --branch-name $AmplifyBranchName --region $Region --profile $Profile --output json
} else {
  $DeploymentJson = aws amplify create-deployment --app-id $AmplifyAppId --branch-name $AmplifyBranchName --region $Region --output json
}
$Deployment = $DeploymentJson | ConvertFrom-Json
Invoke-RestMethod -Uri $Deployment.zipUploadUrl -Method Put -InFile $ZipPath -ContentType "application/zip" | Out-Null
if ($Profile) {
  aws amplify start-deployment --app-id $AmplifyAppId --branch-name $AmplifyBranchName --job-id $Deployment.jobId --region $Region --profile $Profile | Out-Null
} else {
  aws amplify start-deployment --app-id $AmplifyAppId --branch-name $AmplifyBranchName --job-id $Deployment.jobId --region $Region | Out-Null
}

Write-Host "Deployment started."
Write-Host "API URL: $ApiUrl"
Write-Host "Amplify URL: $AmplifyUrl"

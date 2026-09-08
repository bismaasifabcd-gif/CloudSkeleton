#!/usr/bin/env bash
set -euo pipefail

STAGE="${STAGE:-dev}"
REGION="${AWS_REGION:-us-east-1}"
PROFILE="${AWS_PROFILE:-}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-us.anthropic.claude-sonnet-4-6}"
CORS_ORIGINS="${CORS_ORIGINS:-*}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUTS_PATH="$ROOT/.deployment/cdk-outputs.json"
ZIP_PATH="$ROOT/.deployment/frontend.zip"
FRONTEND_DIST="$ROOT/frontend/dist"

mkdir -p "$(dirname "$OUTPUTS_PATH")"

echo "Deploying backend and storage with AWS CDK..."
CDK_PROFILE_ARGS=()
AWS_PROFILE_ARGS=()
if [[ -n "$PROFILE" ]]; then
  CDK_PROFILE_ARGS=(--profile "$PROFILE")
  AWS_PROFILE_ARGS=(--profile "$PROFILE")
fi
(
  cd "$ROOT/infrastructure"
  AWS_REGION="$REGION" AWS_PROFILE="$PROFILE" npx cdk deploy --all "${CDK_PROFILE_ARGS[@]}" --require-approval never \
    --outputs-file "$OUTPUTS_PATH" \
    -c "stage=$STAGE" \
    -c "region=$REGION" \
    -c "bedrockModelId=$BEDROCK_MODEL_ID" \
    -c "corsOrigins=$CORS_ORIGINS"
)

STACK_NAME="$(node -e "const o=require(process.argv[1]); console.log(Object.keys(o)[0])" "$OUTPUTS_PATH")"
API_URL="$(node -e "const o=require(process.argv[1]); const s=process.argv[2]; console.log(o[s].ApiUrl)" "$OUTPUTS_PATH" "$STACK_NAME")"
AMPLIFY_APP_ID="$(node -e "const o=require(process.argv[1]); const s=process.argv[2]; console.log(o[s].AmplifyAppId)" "$OUTPUTS_PATH" "$STACK_NAME")"
AMPLIFY_BRANCH_NAME="$(node -e "const o=require(process.argv[1]); const s=process.argv[2]; console.log(o[s].AmplifyBranchName)" "$OUTPUTS_PATH" "$STACK_NAME")"
AMPLIFY_URL="$(node -e "const o=require(process.argv[1]); const s=process.argv[2]; console.log(o[s].AmplifyUrl)" "$OUTPUTS_PATH" "$STACK_NAME")"

echo "Building frontend with API URL $API_URL..."
(
  cd "$ROOT"
  VITE_API_BASE_URL="$API_URL" npm --workspace frontend run build
)

echo "Packaging frontend for Amplify Hosting..."
rm -f "$ZIP_PATH"
(
  cd "$FRONTEND_DIST"
  zip -qr "$ZIP_PATH" .
)

echo "Uploading frontend artifact to Amplify..."
DEPLOYMENT_JSON="$(aws amplify create-deployment --app-id "$AMPLIFY_APP_ID" --branch-name "$AMPLIFY_BRANCH_NAME" --region "$REGION" "${AWS_PROFILE_ARGS[@]}" --output json)"
ZIP_UPLOAD_URL="$(node -e "const o=JSON.parse(process.argv[1]); console.log(o.zipUploadUrl)" "$DEPLOYMENT_JSON")"
JOB_ID="$(node -e "const o=JSON.parse(process.argv[1]); console.log(o.jobId)" "$DEPLOYMENT_JSON")"
curl -fsS -X PUT -H "Content-Type: application/zip" --upload-file "$ZIP_PATH" "$ZIP_UPLOAD_URL" >/dev/null
aws amplify start-deployment --app-id "$AMPLIFY_APP_ID" --branch-name "$AMPLIFY_BRANCH_NAME" --job-id "$JOB_ID" --region "$REGION" "${AWS_PROFILE_ARGS[@]}" >/dev/null

echo "Deployment started."
echo "API URL: $API_URL"
echo "Amplify URL: $AMPLIFY_URL"

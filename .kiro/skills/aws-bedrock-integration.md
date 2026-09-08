# AWS Bedrock Integration Skill

## Purpose
Expert knowledge for integrating Amazon Bedrock AI services into Python applications, specifically for pipeline generation and AI-powered content creation.

## Core Concepts

### Bedrock Service Setup
- Use boto3 bedrock-runtime client for model inference
- Configure proper region and credential management
- Implement retry logic and error handling for service resilience
- Use structured prompts for consistent model responses

### Model Selection and Configuration
- **amazon.nova-pro-v1:0**: Production model for complex pipeline generation
- **anthropic.claude-3-sonnet-20240229-v1:0**: Alternative for detailed reasoning
- Configure temperature (0.3-0.7) for creativity vs consistency balance
- Set max_tokens based on expected response length requirements

### Prompt Engineering Patterns
```python
def create_pipeline_prompt(user_input: str, context: dict) -> dict:
    """Create structured prompt for Bedrock pipeline generation"""
    return {
        "role": "system",
        "content": f"""
        You are an AWS data architecture expert. Generate a comprehensive pipeline 
        specification based on the user requirements: {user_input}
        
        Return JSON with:
        - services: List of AWS services with justifications
        - architecture: Step-by-step workflow description  
        - connections: Service dependencies and data flow
        - recommendations: Security, monitoring, cost guidance
        """
    }
```

### Response Processing
- Parse JSON responses with proper error handling
- Validate response structure against Pydantic models
- Implement fallback mechanisms for malformed responses
- Extract and normalize service recommendations

## Implementation Patterns

### Async Client Management
```python
class BedrockService:
    def __init__(self) -> None:
        self.client: Optional[boto3.client] = None
        
    async def get_client(self) -> boto3.client:
        if not self.client:
            session = get_session()
            self.client = session.create_client('bedrock-runtime')
        return self.client
        
    async def generate_pipeline(self, prompt: str) -> PipelineSpec:
        client = await self.get_client()
        # Implementation with proper error handling
```

### Error Handling Strategy
- Catch `ClientError` for AWS service exceptions
- Implement exponential backoff for throttling
- Use circuit breaker pattern for service unavailability
- Log errors with correlation IDs for debugging

### Testing Approaches
- Mock Bedrock responses for unit testing
- Use actual service calls for integration testing
- Implement deterministic fallback for development
- Test error scenarios and edge cases

## Security and Best Practices

### IAM Permissions
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "arn:aws:bedrock:*:*:foundation-model/*"
        }
    ]
}
```

### Cost Optimization
- Monitor token usage and implement limits
- Use caching for repeated similar requests
- Implement request deduplication
- Set appropriate timeout values

### Content Safety
- Validate input prompts for appropriate content
- Implement output filtering and sanitization
- Use Bedrock guardrails when available
- Log all interactions for audit purposes

## Common Patterns

### Streaming Responses
```python
async def stream_generation(self, prompt: str) -> AsyncGenerator[str, None]:
    response = await client.invoke_model_with_response_stream(
        modelId=self.model_id,
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    
    async for event in response['body']:
        # Process streaming chunks with proper error handling
        yield event
```

### Batch Processing
- Process multiple requests concurrently using asyncio.gather()
- Implement proper rate limiting to avoid throttling
- Use connection pooling for multiple concurrent requests
- Handle partial failures in batch operations

## Integration Points

### FastAPI Integration
- Use dependency injection for service instances
- Implement proper async route handlers
- Add request/response logging and monitoring
- Handle streaming responses appropriately

### Configuration Management
- Use environment variables for model IDs and parameters
- Implement feature flags for A/B testing different models
- Support runtime configuration updates
- Maintain backward compatibility for configuration changes

## Troubleshooting Guide

### Common Issues
- **ModelNotFound**: Verify model ID and region availability
- **AccessDenied**: Check IAM permissions and service availability
- **ThrottlingException**: Implement exponential backoff and rate limiting
- **ValidationException**: Validate request parameters and prompt structure

### Performance Optimization
- Use connection pooling for better throughput
- Implement request caching for identical prompts
- Monitor and optimize prompt length for faster responses
- Use appropriate model selection based on complexity requirements

#[[file:backend/app/services/bedrock_service.py]]
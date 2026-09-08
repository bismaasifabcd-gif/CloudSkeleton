# FastAPI Development Skill

## Purpose
Expert knowledge for building production-ready FastAPI applications with proper architecture, async patterns, and AWS integration.

## Core FastAPI Patterns

### Application Structure
```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Any
import logging

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management"""
    # Startup logic
    logging.info("Application starting up")
    yield
    # Cleanup logic  
    logging.info("Application shutting down")

app = FastAPI(
    title="AI Data Pipeline Generator",
    description="Generate AWS data pipeline architectures from natural language",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Dependency Injection Patterns
```python
from typing import Annotated, Optional
from fastapi import Depends

class ServiceDependencies:
    """Container for service dependencies"""
    
    def __init__(self) -> None:
        self._bedrock_service: Optional[BedrockService] = None
        self._history_repository: Optional[HistoryRepository] = None
    
    def get_bedrock_service(self) -> BedrockService:
        if self._bedrock_service is None:
            self._bedrock_service = BedrockService()
        return self._bedrock_service
    
    def get_history_repository(self) -> HistoryRepository:
        if self._history_repository is None:
            self._history_repository = HistoryRepository()
        return self._history_repository

# Global dependencies instance
dependencies = ServiceDependencies()

# Dependency functions
async def get_bedrock_service() -> BedrockService:
    return dependencies.get_bedrock_service()

async def get_history_repository() -> HistoryRepository:
    return dependencies.get_history_repository()

# Type aliases for cleaner route signatures
BedrockDep = Annotated[BedrockService, Depends(get_bedrock_service)]
HistoryDep = Annotated[HistoryRepository, Depends(get_history_repository)]
```

### Route Handler Patterns
```python
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
import logging

router = APIRouter(prefix="/api/v1", tags=["pipelines"])

@router.post("/generate", response_model=GenerationResponse)
async def generate_pipeline(
    request: GenerationRequest,
    bedrock_service: BedrockDep,
    history_repo: HistoryDep
) -> GenerationResponse:
    """Generate pipeline architecture from natural language prompt"""
    
    try:
        # Validate input
        if not request.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt cannot be empty"
            )
        
        # Generate pipeline
        pipeline_spec = await bedrock_service.generate_pipeline(
            prompt=request.prompt,
            tags=request.tags,
            user_id=request.user_id
        )
        
        # Save to history
        history_entry = await history_repo.save_generation(
            user_id=request.user_id,
            prompt=request.prompt,
            pipeline_spec=pipeline_spec,
            tags=request.tags
        )
        
        return GenerationResponse(
            id=history_entry.id,
            pipeline=pipeline_spec,
            metadata=GenerationMetadata(
                timestamp=history_entry.created_at,
                model_id=bedrock_service.model_id,
                tags=request.tags
            )
        )
        
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation failed: {str(e)}"
        )
    except ValueError as e:
        logging.error(f"Business logic error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logging.exception("Unexpected error in pipeline generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
```

## Async Programming Patterns

### Async Service Layer
```python
import asyncio
from typing import List, Optional, Any
import aiohttp
from contextlib import asynccontextmanager
import json
from botocore.exceptions import ClientError

class BedrockService:
    def __init__(self) -> None:
        self._client: Optional[Any] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self.model_id: str = "amazon.nova-pro-v1:0"
    
    async def __aenter__(self) -> "BedrockService":
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._session:
            await self._session.close()
    
    @asynccontextmanager
    async def get_client(self):
        """Async context manager for Bedrock client"""
        if not self._client:
            session = get_session()
            self._client = session.create_client('bedrock-runtime')
        
        try:
            yield self._client
        except Exception as e:
            logging.error(f"Bedrock client error: {e}")
            raise
        finally:
            # Cleanup if needed
            pass
    
    async def generate_pipeline(
        self, 
        prompt: str, 
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> PipelineSpec:
        """Generate pipeline with proper async handling"""
        
        async with self.get_client() as client:
            try:
                # Prepare request
                request_body = self._prepare_request(prompt, tags)
                
                # Make async call to Bedrock
                response = await asyncio.to_thread(
                    client.invoke_model,
                    modelId=self.model_id,
                    body=json.dumps(request_body)
                )
                
                # Process response
                result = await self._process_response(response)
                
                # Validate and normalize
                pipeline_spec = self._normalize_pipeline(result)
                
                return pipeline_spec
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ThrottlingException':
                    await asyncio.sleep(1)  # Simple backoff
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Service is temporarily busy, please try again"
                    )
                else:
                    logging.error(f"Bedrock error: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="AI service temporarily unavailable"
                    )
    
    def _prepare_request(self, prompt: str, tags: Optional[List[str]]) -> dict:
        """Prepare request body for Bedrock API"""
        return {
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.7
        }
    
    async def _process_response(self, response: dict) -> dict:
        """Process Bedrock API response"""
        body = response.get('body')
        if body:
            content = json.loads(body.read())
            return content
        raise ValueError("Invalid response from Bedrock service")
    
    def _normalize_pipeline(self, result: dict) -> PipelineSpec:
        """Normalize AI response to PipelineSpec"""
        # Implementation would depend on specific response format
        return PipelineSpec(**result)
```

### Concurrent Processing
```python
async def process_batch_requests(
    requests: List[GenerationRequest],
    bedrock_service: BedrockService
) -> List[GenerationResponse]:
    """Process multiple requests concurrently"""
    
    async def process_single_request(req: GenerationRequest) -> GenerationResponse:
        try:
            pipeline = await bedrock_service.generate_pipeline(
                prompt=req.prompt,
                tags=req.tags,
                user_id=req.user_id
            )
            return GenerationResponse(pipeline=pipeline)
        except Exception as e:
            logging.error(f"Failed to process request {req.user_id}: {e}")
            raise
    
    # Process with concurrency limit
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
    
    async def limited_process(req: GenerationRequest) -> GenerationResponse:
        async with semaphore:
            return await process_single_request(req)
    
    tasks = [limited_process(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter successful results and handle failures
    successful_results: List[GenerationResponse] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Request {i} failed: {result}")
        else:
            successful_results.append(result)
    
    return successful_results
```

## Error Handling and Validation

### Custom Exception Classes
```python
class PipelineGenerationError(Exception):
    """Base exception for pipeline generation errors"""
    pass

class InvalidPromptError(PipelineGenerationError):
    """Raised when prompt validation fails"""
    pass

class ModelUnavailableError(PipelineGenerationError):
    """Raised when AI model is unavailable"""
    pass

class QuotaExceededError(PipelineGenerationError):
    """Raised when usage quota is exceeded"""
    pass

# Exception handlers
@app.exception_handler(InvalidPromptError)
async def invalid_prompt_handler(request: Request, exc: InvalidPromptError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "error_type": "invalid_prompt"}
    )

@app.exception_handler(ModelUnavailableError)
async def model_unavailable_handler(request: Request, exc: ModelUnavailableError):
    return JSONResponse(
        status_code=502,
        content={"detail": "AI service temporarily unavailable", "error_type": "service_unavailable"}
    )
```

### Request Validation
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import re

class GenerationRequest(BaseModel):
    prompt: str = Field(
        ..., 
        min_length=10, 
        max_length=5000,
        description="Natural language pipeline description"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        max_items=10,
        description="Optional tags for categorization"
    )
    user_id: str = Field(
        ...,
        min_length=1,
        description="User identifier"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v: str) -> str:
        """Validate prompt content"""
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace only")
        
        # Check for potentially problematic content
        if len(v.split()) < 3:
            raise ValueError("Prompt too short, please provide more detail")
        
        return v.strip()
    
    @validator('tags')
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize tags"""
        if v is None:
            return v
        
        validated_tags: List[str] = []
        for tag in v:
            # Normalize tag format
            normalized = re.sub(r'[^a-zA-Z0-9-_]', '', tag.lower())
            if normalized and len(normalized) <= 50:
                validated_tags.append(normalized)
        
        return validated_tags if validated_tags else None
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Create a real-time data pipeline for processing IoT sensor data",
                "tags": ["iot", "realtime", "sensors"],
                "user_id": "user123"
            }
        }
```

## Testing Patterns

### Unit Testing with Mocks
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
import json

class TestBedrockService:
    @pytest.fixture
    def bedrock_service(self) -> BedrockService:
        service = BedrockService()
        service._client = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_generate_pipeline_success(self, bedrock_service: BedrockService):
        # Mock successful response
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{
                'text': '{"services": ["s3", "lambda"], "architecture": "serverless"}'
            }]
        })
        
        bedrock_service._client.invoke_model.return_value = mock_response
        
        result = await bedrock_service.generate_pipeline("test prompt")
        
        assert isinstance(result, PipelineSpec)
        assert len(result.services) > 0
    
    @pytest.mark.asyncio  
    async def test_generate_pipeline_throttling(self, bedrock_service: BedrockService):
        # Mock throttling error
        from botocore.exceptions import ClientError
        
        error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        bedrock_service._client.invoke_model.side_effect = error
        
        with pytest.raises(HTTPException) as exc_info:
            await bedrock_service.generate_pipeline("test prompt")
        
        assert exc_info.value.status_code == 429
```

### Integration Testing
```python
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)

def test_generate_pipeline_endpoint(test_client: TestClient):
    """Test the pipeline generation endpoint"""
    
    request_data = {
        "prompt": "Create a data lake architecture for analytics",
        "tags": ["analytics", "data-lake"],
        "user_id": "test-user"
    }
    
    response = test_client.post("/api/v1/generate", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "pipeline" in data
    assert "metadata" in data
    assert isinstance(data["pipeline"]["services"], list)

def test_generate_pipeline_validation_error(test_client: TestClient):
    """Test validation error handling"""
    
    invalid_request = {
        "prompt": "",  # Empty prompt should fail validation
        "user_id": "test-user"
    }
    
    response = test_client.post("/api/v1/generate", json=invalid_request)
    
    assert response.status_code == 422
    assert "detail" in response.json()
```

## Performance and Security

### Response Caching
```python
from functools import lru_cache
import hashlib
from typing import Dict, Any

class CachedBedrockService(BedrockService):
    def __init__(self) -> None:
        super().__init__()
        self._cache: Dict[str, Any] = {}
    
    def _get_cache_key(self, prompt: str, tags: Optional[List[str]]) -> str:
        """Generate cache key for request"""
        cache_input = f"{prompt}:{','.join(sorted(tags or []))}"
        return hashlib.sha256(cache_input.encode()).hexdigest()
    
    async def generate_pipeline(
        self, 
        prompt: str, 
        tags: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> PipelineSpec:
        """Generate pipeline with optional caching"""
        
        if use_cache:
            cache_key = self._get_cache_key(prompt, tags)
            if cache_key in self._cache:
                logging.info(f"Cache hit for key: {cache_key}")
                return self._cache[cache_key]
        
        result = await super().generate_pipeline(prompt, tags)
        
        if use_cache:
            self._cache[cache_key] = result
            
        return result
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/generate")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def generate_pipeline(
    request: Request,  # Required for rate limiting
    generation_request: GenerationRequest,
    bedrock_service: BedrockDep
) -> GenerationResponse:
    """Rate-limited pipeline generation"""
    # Implementation...
```

### Security Headers
```python
from fastapi import security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> str:
    """Verify JWT token (placeholder implementation)"""
    # In production, implement proper JWT validation
    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return credentials.credentials

# Protected route example
@router.post("/generate")
async def generate_pipeline(
    request: GenerationRequest,
    token: str = Depends(verify_token),
    bedrock_service: BedrockDep
) -> GenerationResponse:
    """Protected pipeline generation endpoint"""
    # Implementation with authentication...
```

#[[file:backend/app/main.py]]
#[[file:backend/app/api/routes.py]]
#[[file:backend/app/services/bedrock_service.py]]
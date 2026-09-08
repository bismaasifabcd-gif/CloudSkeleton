---
inclusion: auto
---

# Python FastAPI Development Standards

## Application Architecture

### Project Structure
- Follow Domain-Driven Design principles for service organization
- Separate API routes, business logic, and data access layers
- Use dependency injection for service composition and testing
- Implement proper error handling with custom exception classes

### FastAPI Best Practices
- Use Pydantic models for request/response validation and serialization
- Implement proper HTTP status codes for different response scenarios
- Use FastAPI dependency system for shared logic and authentication
- Implement OpenAPI documentation with proper descriptions and examples

### Async Programming
- Use async/await for I/O operations (database, external APIs)
- Implement proper connection pooling for external service clients
- Use asyncio.gather() for concurrent operations when possible
- Handle async exceptions with proper error propagation

## Code Quality Standards

### Type Annotations
- Use explicit type hints for all function parameters and return values
- Import types from typing module for complex type annotations
- Use Union types for optional parameters and multiple return types
- Implement type checking with mypy in CI/CD pipeline

### Error Handling
- Create custom exception classes inheriting from HTTPException
- Implement proper error logging with structured format
- Use try/catch blocks for external service interactions
- Return appropriate HTTP status codes with descriptive error messages

### Testing Patterns
- Write unit tests for all business logic functions
- Use pytest fixtures for test data and mock dependencies
- Implement integration tests for API endpoints
- Use TestClient from FastAPI for endpoint testing

## Data Modeling

### Pydantic Models
- Create separate models for requests, responses, and internal data
- Use Field() for validation, documentation, and default values
- Implement custom validators for complex business rules
- Use Config class for model behavior configuration

### Database Integration
- Use repository pattern for data access abstraction
- Implement proper connection management and cleanup
- Use prepared statements or ORM for SQL injection prevention
- Implement proper pagination for large dataset queries

## AWS Integration Patterns

### Boto3 Client Management
- Use session-based clients for better connection management
- Implement proper error handling for AWS service exceptions
- Use exponential backoff for retryable operations
- Implement proper credential management and rotation

### Service Integration
- Create dedicated service classes for each AWS service integration
- Implement proper request/response transformation
- Use async clients when available for better performance
- Implement circuit breaker pattern for external service resilience

## Performance Optimization

### Response Time
- Use async programming for I/O-bound operations
- Implement caching for frequently accessed data
- Use connection pooling for database and external service connections
- Profile and optimize slow endpoints using proper monitoring

### Memory Management  
- Use generators for large dataset processing
- Implement proper cleanup for temporary resources
- Use streaming for large file uploads and downloads
- Monitor memory usage and implement limits when necessary

### Monitoring and Logging
- Use structured logging with JSON format for better parsing
- Implement proper log levels (DEBUG, INFO, WARNING, ERROR)
- Add correlation IDs for request tracking across services
- Use CloudWatch integration for centralized logging

## Security Implementation

### Input Validation
- Use Pydantic models for automatic request validation
- Implement additional business rule validation in service layer
- Sanitize inputs to prevent injection attacks
- Use proper encoding for data storage and transmission

### Authentication and Authorization
- Implement JWT token validation for authenticated endpoints
- Use dependency injection for authentication requirements
- Implement proper role-based access control
- Log authentication events for security monitoring

### Data Protection
- Never log sensitive information (passwords, tokens, PII)
- Use environment variables for all configuration secrets
- Implement proper encryption for data at rest and in transit
- Use secure random generators for tokens and session identifiers

## API Design Standards

### RESTful Conventions
- Use proper HTTP methods (GET, POST, PUT, DELETE) for operations
- Implement consistent URL patterns and resource naming
- Use proper HTTP status codes for different response scenarios
- Implement API versioning strategy for backward compatibility

### Documentation
- Use Pydantic model descriptions for automatic OpenAPI generation
- Include examples in request/response model definitions
- Document error responses and status codes
- Provide clear API usage examples and integration guides

### Response Format
- Use consistent response envelope for all endpoints
- Include metadata (timestamps, pagination) in responses
- Implement proper error response format with details
- Use appropriate content types and encoding headers

## Development Workflow

### Code Organization
```python
# routes.py - API endpoint definitions
@app.get("/api/v1/resource")
async def get_resource(service: ResourceService = Depends()):
    return await service.get_resource()

# services/ - Business logic implementation  
class ResourceService:
    def __init__(self, repository: ResourceRepository):
        self.repository = repository
    
    async def get_resource(self) -> ResourceResponse:
        # Business logic implementation
        pass

# models/ - Pydantic model definitions
class ResourceRequest(BaseModel):
    name: str = Field(..., description="Resource name")
    
class ResourceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
```

### Testing Structure
```python
# Test organization
def test_resource_creation():
    # Unit test for service logic
    pass

async def test_resource_api_endpoint():
    # Integration test for API endpoint
    pass

@pytest.fixture
def mock_resource_repository():
    # Test fixture for dependency mocking
    pass
```

#[[file:backend/app/main.py]]
#[[file:backend/app/api/routes.py]]
#[[file:backend/app/services/bedrock_service.py]]
#[[file:backend/app/models/pipeline.py]]
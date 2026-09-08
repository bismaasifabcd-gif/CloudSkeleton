---
inclusion: auto
---

# AWS Development Standards

## Architecture Principles

### Cloud-Native Design
- Use AWS managed services whenever possible to reduce operational overhead
- Design for serverless-first architecture with Lambda, API Gateway, DynamoDB
- Implement proper error handling and retry logic for distributed systems
- Use Infrastructure as Code (CDK) for all AWS resource provisioning

### Security Best Practices
- Apply least-privilege IAM policies for all service-to-service communication
- Use AWS managed encryption (KMS) for data at rest and in transit  
- Implement proper CORS configuration for browser-based applications
- Never commit AWS credentials or sensitive configuration to version control
- Use environment variables for all configuration values

### Monitoring and Observability
- Implement structured logging with CloudWatch for all Lambda functions
- Add X-Ray tracing for distributed request tracking
- Create CloudWatch alarms for critical metrics and error rates
- Use proper log retention policies to manage costs

## Service Selection Guidelines

### When to Use Each Service
- **Lambda**: Event-driven compute, API backends, data processing
- **API Gateway**: REST/HTTP APIs with built-in throttling and security
- **DynamoDB**: NoSQL for high-performance, variable workloads
- **S3**: Object storage for static assets, exports, backups
- **Amplify**: Static website hosting with CI/CD integration
- **Bedrock**: AI/ML inference with managed model access

### Cost Optimization
- Use appropriate DynamoDB capacity modes (on-demand vs provisioned)
- Implement S3 lifecycle policies for long-term storage optimization  
- Set CloudWatch log retention periods to balance debugging needs and costs
- Use Lambda provisioned concurrency only when cold starts are critical

## Development Workflow

### Local Development
- Use mock services and fallback mechanisms for offline development
- Implement feature flags to toggle between local and AWS services
- Provide clear setup instructions for both AWS-connected and offline modes

### Testing Strategy  
- Unit tests for business logic without AWS dependencies
- Integration tests using LocalStack or AWS test environments
- Load testing for Lambda cold start and DynamoDB performance
- Security testing for IAM policies and data access patterns

### Deployment Process
- Use CDK for infrastructure provisioning and updates
- Implement proper environment separation (dev/staging/prod)
- Use CloudFormation drift detection to maintain infrastructure consistency
- Implement automated rollback procedures for failed deployments

## Code Organization

### Backend Structure
```
backend/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Configuration and shared utilities  
│   ├── models/        # Pydantic data models
│   ├── services/      # Business logic and AWS integrations
│   └── utils/         # Helper functions and utilities
├── tests/             # Unit and integration tests
└── requirements*.txt  # Python dependencies
```

### Frontend Structure  
```
frontend/src/
├── components/        # React components organized by feature
├── hooks/            # Custom React hooks
├── lib/              # API clients and utilities
└── styles/           # CSS and styling configuration
```

## Performance Guidelines

### Lambda Optimization
- Minimize cold start times through proper dependency management
- Use appropriate memory allocation for cost/performance balance
- Implement connection pooling for external service calls
- Cache frequently accessed data using Lambda environment variables

### Frontend Performance
- Implement code splitting for large React applications
- Use React.memo and useMemo for expensive component renders
- Optimize bundle sizes through proper dependency management
- Implement lazy loading for non-critical components and routes

### DynamoDB Best Practices
- Design partition keys to distribute load evenly
- Use sparse indexes for optional attributes
- Implement proper pagination for large result sets
- Monitor read/write capacity utilization and adjust accordingly

#[[file:backend/app/core/config.py]]
#[[file:infrastructure/lib/ai-pipeline-stack.ts]]
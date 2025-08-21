# Evaluation Key - Internal Use Only
*This document is shared with candidates for transparency*

## Scoring Overview

Total possible score: 100 points
- **Minimum to proceed**: 70 points
- **Strong candidate**: 80+ points
- **Exceptional candidate**: 90+ points

## Detailed Scoring Rubric

### 1. Code Quality (30 points)

#### Clean Code (10 points)
- **10 points**: Exceptionally clean, follows all best practices
  - Meaningful variable/function names
  - Single responsibility functions
  - No code duplication (DRY)
  - Consistent formatting
  - Type hints throughout

- **7-9 points**: Very clean with minor issues
- **4-6 points**: Generally clean but some problems
- **0-3 points**: Significant code quality issues

#### Error Handling (10 points)
- **10 points**: Comprehensive error handling
  ```python
  # Example of excellent error handling
  try:
      result = await send_notification(user, template, context)
  except ProviderTimeoutError as e:
      logger.warning(f"Provider timeout: {e}", extra={"user_id": user.id})
      return await retry_with_backoff(send_notification, user, template, context)
  except InvalidTemplateError as e:
      logger.error(f"Invalid template: {e}", extra={"template_id": template.id})
      raise BadRequestError(f"Template {template.id} is invalid")
  except Exception as e:
      logger.exception("Unexpected error in notification service")
      raise InternalServerError("Failed to send notification")
  ```

- **7-9 points**: Good error handling, some edge cases missed
- **4-6 points**: Basic error handling
- **0-3 points**: Poor or no error handling

#### SOLID Principles (10 points)
- **10 points**: All SOLID principles clearly demonstrated
- **7-9 points**: Most principles followed
- **4-6 points**: Some principles evident
- **0-3 points**: No clear application of SOLID

### 2. Architecture (25 points)

#### Service Design (10 points)
- **10 points**: Excellent separation
  - Clear domain boundaries
  - Proper layering (API → Service → Repository)
  - Dependency injection
  - No circular dependencies

- **7-9 points**: Good separation with minor coupling
- **4-6 points**: Adequate separation
- **0-3 points**: Poor separation, high coupling

#### API Design (8 points)
- **8 points**: Professional API design
  - RESTful principles
  - Consistent naming
  - Proper status codes
  - Versioning implemented
  - Comprehensive OpenAPI docs

- **6-7 points**: Good API design, minor issues
- **3-5 points**: Basic API design
- **0-2 points**: Poor API design

#### Scalability Considerations (7 points)
- **7 points**: Designed for scale
  - Stateless services
  - Horizontal scaling ready
  - Caching strategy
  - Async processing where appropriate

- **5-6 points**: Good scalability considerations
- **2-4 points**: Some scalability thought
- **0-1 points**: No scalability considerations

### 3. Testing (20 points)

#### Test Coverage (8 points)
- **8 points**: >80% coverage with meaningful tests
- **6-7 points**: 60-80% coverage
- **3-5 points**: 40-60% coverage
- **0-2 points**: <40% coverage

#### Test Quality (7 points)
- **7 points**: Comprehensive test suite
  ```python
  # Example of excellent test
  @pytest.mark.asyncio
  async def test_send_notification_with_circuit_breaker_open():
      # Arrange
      circuit_breaker = CircuitBreaker(failure_threshold=1)
      circuit_breaker.record_failure()  # Open the circuit
      
      notification_service = NotificationService(circuit_breaker=circuit_breaker)
      
      # Act & Assert
      with pytest.raises(CircuitBreakerOpenError):
          await notification_service.send_email(
              user_id=123,
              template="welcome",
              context={"name": "Test"}
          )
      
      # Verify no external call was made
      mock_email_provider.send.assert_not_called()
  ```

- **5-6 points**: Good tests, some gaps
- **2-4 points**: Basic tests
- **0-1 points**: Poor or no tests

#### Integration Tests (5 points)
- **5 points**: Complete integration test suite
- **3-4 points**: Good integration tests
- **1-2 points**: Some integration tests
- **0 points**: No integration tests

### 4. Migration Strategy (15 points)

#### Zero-Downtime Plan (8 points)
- **8 points**: Comprehensive zero-downtime strategy
  - Dual-write period
  - Feature flags
  - Gradual rollout
  - Rollback plan
  - Data verification steps

- **5-7 points**: Good strategy with some gaps
- **2-4 points**: Basic strategy
- **0-1 points**: No clear strategy

#### Data Consistency (7 points)
- **7 points**: Strong consistency approach
  - Transaction boundaries defined
  - Eventual consistency handled
  - Conflict resolution strategy
  - Data validation steps

- **5-6 points**: Good consistency approach
- **2-4 points**: Basic approach
- **0-1 points**: No consistency consideration

### 5. Documentation (10 points)

#### README Quality (4 points)
- **4 points**: Excellent README
  - Clear setup instructions
  - Architecture overview
  - Design decisions explained
  - Running tests documented

- **3 points**: Good README
- **1-2 points**: Basic README
- **0 points**: Poor or no README

#### API Documentation (3 points)
- **3 points**: Complete OpenAPI spec with examples
- **2 points**: Good API documentation
- **1 point**: Basic documentation
- **0 points**: No API documentation

#### Architecture Decisions (3 points)
- **3 points**: Clear ADRs or decision documentation
- **2 points**: Some decisions documented
- **1 point**: Minimal documentation
- **0 points**: No architecture documentation

## Bonus Points (up to 10 additional)

### Extensions Completed
- **+3 points**: Performance optimization extension done well
- **+3 points**: Resilience patterns implemented correctly
- **+4 points**: Event streaming architecture implemented

### Exceptional Elements
- **+2 points**: Production-ready monitoring/observability
- **+2 points**: Comprehensive CI/CD pipeline
- **+2 points**: Performance benchmarks included
- **+2 points**: Security considerations (auth, encryption)

## Red Flags (Automatic Deductions)

- **-10 points**: Code doesn't run
- **-10 points**: No tests
- **-5 points**: Significant security vulnerabilities
- **-5 points**: Plagiarized code
- **-5 points**: No documentation
- **-3 points**: Hardcoded secrets/credentials

## Evaluation Process

### Step 1: Initial Review (15 minutes)
- Does the code run?
- Is the structure correct?
- Are basic requirements met?

### Step 2: Code Quality Assessment (30 minutes)
- Review code cleanliness
- Check error handling
- Evaluate architecture

### Step 3: Testing Review (15 minutes)
- Run test suite
- Check coverage
- Review test quality

### Step 4: Documentation Review (10 minutes)
- Read through README
- Check API documentation
- Review architecture decisions

### Step 5: Deep Dive (20 minutes)
- Examine integration patterns
- Review migration strategy
- Check for production readiness

### Step 6: Scoring (10 minutes)
- Complete scoring rubric
- Add bonus points
- Apply any deductions
- Write summary feedback

## Sample Feedback Template

```markdown
## Candidate Evaluation Summary

**Overall Score**: XX/100

### Strengths
- Excellent service extraction with clear boundaries
- Comprehensive test coverage (85%)
- Well-documented API with OpenAPI spec
- Strong error handling throughout

### Areas for Improvement
- Circuit breaker implementation could be more robust
- Missing distributed tracing setup
- Database indexes not fully optimized
- Could benefit from more integration tests

### Specific Highlights
- Creative solution for handling eventual consistency
- Good use of dependency injection pattern
- Clear migration strategy with rollback plan

### Recommendation
[Proceed to next round / Requires discussion / Do not proceed]

### Questions for Technical Interview
1. How would you handle distributed transactions in this architecture?
2. What monitoring would you add for production?
3. How would you scale this to handle 10x load?
```

## Calibration Notes

### What Distinguishes Great Submissions

**90+ Point Submissions:**
- Production-ready code
- Comprehensive testing
- Clear architectural thinking
- Excellent documentation
- Multiple extensions completed
- Shows deep Django knowledge
- Demonstrates real-world experience

**70-80 Point Submissions:**
- Meets all requirements
- Good code quality
- Adequate testing
- Clear documentation
- Some architectural sophistication
- Shows competence

**Below 70 Point Submissions:**
- Missing key requirements
- Poor code quality
- Insufficient testing
- Unclear architecture
- Limited documentation
- Shows gaps in experience
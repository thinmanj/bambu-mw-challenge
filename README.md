# MyBambu Middleware Architect - Coding Challenge

## 🎯 Challenge Overview

Welcome to the MyBambu Middleware Architect coding challenge! This challenge simulates a real-world task you'll face in this role: extracting a microservice from our Django monolith.

**Time Estimate:** 4-6 hours  
**Submission Deadline:** 1 week from receipt

## 📋 Your Task

Extract a notification service from a Django monolith that currently handles:
- Email notifications (via AWS SES)
- SMS notifications (via Twilio)
- Push notifications (via Firebase)
- In-app notifications

The service processes 50,000+ notifications daily with requirements for retry logic, delivery tracking, and template management.

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Basic knowledge of Django, REST APIs, and microservices

### Setup Instructions

1. **Clone this repository:**
```bash
git clone https://github.com/pwatson-mybambu/bambu-mw-challenge.git
cd bambu-mw-challenge
```

2. **Start the development environment:**
```bash
cd starter-code
docker-compose up -d
```

3. **Verify the setup:**
```bash
curl http://localhost:8000/health
```

## 📁 Repository Structure

```
bambu-mw-challenge/
├── README.md                    # This file
├── requirements.md              # Detailed challenge requirements
├── evaluation-key.md           # How we'll evaluate your submission
└── starter-code/               # Starting point for your solution
    ├── docker-compose.yml      # Docker setup
    ├── notifications/          # Current monolith code
    │   ├── models.py          # Notification models
    │   └── services.py        # Core notification logic
    └── ... (additional files)
```

## 📝 Challenge Phases

### Phase 1: Analysis (30 minutes)
- Document current dependencies
- Identify service boundaries
- Plan data migration strategy

### Phase 2: Service Extraction (2-3 hours)
- Create standalone notification service
- Implement REST API
- Handle authentication and authorization
- Maintain backward compatibility

### Phase 3: Integration (1-2 hours)
- Implement async communication
- Add monitoring and logging
- Create migration scripts
- Write tests

### Phase 4: Documentation (30 minutes)
- Architecture decisions
- API documentation
- Deployment instructions
- Future improvements

**[View Full Requirements →](requirements.md)**

## 🎯 Evaluation Criteria

Your solution will be evaluated on:

| Category | Weight | Focus Areas |
|----------|--------|-------------|
| **Architecture** | 40% | Service boundaries, API design, data strategy |
| **Code Quality** | 30% | Clean code, testing, documentation |
| **Operations** | 20% | Monitoring, performance, deployment |
| **Communication** | 10% | Clear documentation, decision rationale |

**[View Detailed Evaluation →](evaluation-key.md)**

## 📤 Submission Guidelines

### How to Submit

1. **Fork this repository** to your GitHub account
2. **Create a new branch** called `solution`
3. **Implement your solution** with clear commits
4. **Push to your fork**
5. **Create a Pull Request** with:
   - Summary of your approach
   - Key decisions and trade-offs
   - Any assumptions made
   - Time spent on each phase

### Required Deliverables

✅ **Code**
- Extracted notification service
- API implementation (REST required, GraphQL bonus)
- Database migrations
- Test suite

✅ **Documentation**
- README with setup instructions
- API documentation (OpenAPI/Swagger preferred)
- Architecture decision records (ADRs)
- Migration runbook

✅ **Infrastructure**
- Updated docker-compose.yml
- Environment configuration
- Basic monitoring setup

### Optional Bonus Items

🎁 If time permits:
- GraphQL API
- Kubernetes manifests
- CI/CD pipeline (GitHub Actions)
- Performance benchmarks
- Advanced monitoring (Prometheus/Grafana)

## 💡 Tips for Success

1. **Read everything first** - Understand requirements before coding
2. **Plan your approach** - Spend time on design before implementation
3. **Start simple** - Get a working solution before optimizing
4. **Document as you go** - Explain your decisions and trade-offs
5. **Test your solution** - Include at least basic unit tests
6. **Consider production** - Think about real-world deployment

## ⏱️ Suggested Timeline

| Hour | Focus |
|------|-------|
| 1 | Requirements review, planning, setup |
| 2-3 | Core service extraction |
| 4 | API implementation |
| 5 | Testing and documentation |
| 6 | Polish and submission prep |

## 🤔 FAQs

**Q: Can I use additional libraries/frameworks?**  
A: Yes! Use whatever tools you're comfortable with. Document your choices.

**Q: Should I implement all notification types?**  
A: Focus on 2-3 types with a clear pattern for adding more.

**Q: How much testing is expected?**  
A: Basic unit tests are required. Integration tests are a bonus.

**Q: Should I deploy this somewhere?**  
A: Local Docker setup is sufficient. Cloud deployment is optional.

## 📧 Questions?

If you need clarification:
1. Check the [requirements.md](requirements.md) file first
2. Review [evaluation-key.md](evaluation-key.md) for expectations
3. Make reasonable assumptions and document them
4. Email: middleware-hiring@mybambu.com (for critical blockers only)

## 🏆 What Success Looks Like

A successful submission will:
- Extract a clean, well-bounded service
- Provide a clear migration path
- Include comprehensive documentation
- Demonstrate production-ready thinking
- Show architectural maturity

## 📜 Confidentiality

This challenge is proprietary to MyBambu. Please:
- Don't share challenge details publicly
- Keep your solution private until after the interview process
- You may reference this work in future portfolios after hire decision

---

**Good luck! We're excited to see your approach to this real-world architectural challenge.**

*The MyBambu Engineering Team* 🚀
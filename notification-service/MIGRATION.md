# Notification Service Migration Guide

This document describes the migration strategy from a monolithic notification system to the new standalone notification microservice using a dual read+write approach with database synchronization.

## Migration Overview

The migration follows a safe, incremental approach that ensures zero-downtime transition from the existing monolithic notification system to the new microservice architecture.

### Key Principles
- **Zero Downtime**: Users experience no service interruption
- **Data Consistency**: All notification data is preserved and synchronized
- **Gradual Transition**: Traffic is migrated to new microservice and monolithic notification subsystem is being disabled
- **Dual Operations**: Both DB update in parallel during transition

---

## Migration Phases

### Phase 1: Current State - Monolithic Architecture

**Description**: The existing monolithic service handles all notification operations with a single database.

```
┌─────────────────────────────────────────────┐
│              MONOLITHIC SERVICE             │
├─────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐            │
│  │   Web API   │ │   Admin     │            │
│  └─────────────┘ └─────────────┘            │
│  ┌────────────────────────────────────────┐ │
│  │        Application Logic               │ │
│  │  ┌─────────┐ ┌──────────────────────┐  │ │
│  │  │  User   │ │    NOTIFICATIONS     │  │ │
│  │  │  Mgmt   │ │     SUBSYSTEM        │  │ │
│  │  └─────────┘ └──────────────────────┘  │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │ │
│  │  │ Orders  │ │Payments │ │Reports  │   │ │
│  │  └─────────┘ └─────────┘ └─────────┘   │ │
│  └────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │     MONOLITHIC DATABASE    │
        ├────────────────────────────┤
        │  ┌─────────────────────┐   │
        │  │        users        │   │
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │     notifications   │   │ ◄─── Notification Tables
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │      templates      │   │ ◄─── Template Tables  
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │    preferences      │   │ ◄─── User Preferences
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │       orders        │   │
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │      payments       │   │
        │  └─────────────────────┘   │
        │         ...more tables     │
        └────────────────────────────┘
```

**Characteristics:**
- Single application handling all business logic
- Unified database with all domain data
- Notification logic embedded within the monolith
- Direct database access for all operations

---

### Phase 2: Introduce New Microservice (Parallel Deployment)

**Description**: Deploy the new notification microservice alongside the existing monolith with its own dedicated database.

```
┌─────────────────────────────────────────────┐
│              MONOLITHIC SERVICE             │
├─────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐            │
│  │   Web API   │ │   Admin     │            │
│  └─────────────┘ └─────────────┘            │
│  ┌────────────────────────────────────────┐ │
│  │        Application Logic               │ │
│  │  ┌─────────┐ ┌──────────────────────┐  │ │
│  │  │  User   │ │    NOTIFICATIONS     │  │ │ ◄─── Still Active
│  │  │  Mgmt   │ │     SUBSYSTEM        │  │ │
│  │  └─────────┘ └──────────────────────┘  │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │ │
│  │  │ Orders  │ │Payments │ │Reports  │   │ │
│  │  └─────────┘ └─────────┘ └─────────┘   │ │
│  └────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │     MONOLITHIC DATABASE    │
        ├────────────────────────────┤
        │  ┌─────────────────────┐   │
        │  │        users        │   │
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │     notifications   │   │ ◄─── Still Used
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │      templates      │   │
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │    preferences      │   │
        │  └─────────────────────┘   │
        │  ┌─────────────────────┐   │
        │  │       orders        │   │
        │  └─────────────────────┘   │
        │         ...more tables     │
        └────────────────────────────┘

                                     ┌───────────────────────────────┐
                                     │      NOTIFICATION SERVICE     │ ◄─── NEW
                                     ├───────────────────────────────┤
                                     │  ┌─────────────────────────┐  │
                                     │  │       REST API          │  │
                                     │  └─────────────────────────┘  │
                                     │  ┌─────────────────────────┐  │
                                     │  │      GraphQL API        │  │
                                     │  └─────────────────────────┘  │
                                     │  ┌─────────────────────────┐  │
                                     │  │    Business Logic       │  │
                                     │  │  ┌─────────────────┐    │  │
                                     │  │  │   Retry Logic   │    │  │
                                     │  │  └─────────────────┘    │  │
                                     │  │  ┌─────────────────┐    │  │
                                     │  │  │   Rate Limiting │    │  │
                                     │  │  └─────────────────┘    │  │
                                     │  │  ┌─────────────────┐    │  │
                                     │  │  │   Adapters      │    │  │
                                     │  │  │  (Email/SMS/Push)│   │  │
                                     │  │  └─────────────────┘    │  │
                                     │  └─────────────────────────┘  │
                                     └───────────────┬───────────────┘
                                                     │
                                                     ▼
                                       ┌─────────────────────────────┐
                                       │   NOTIFICATION DATABASE     │ ◄─── NEW
                                       ├─────────────────────────────┤
                                       │  ┌─────────────────────┐    │
                                       │  │     notifications   │    │
                                       │  └─────────────────────┘    │
                                       │  ┌─────────────────────┐    │
                                       │  │      templates      │    │
                                       │  └─────────────────────┘    │
                                       │  ┌─────────────────────┐    │
                                       │  │    preferences      │    │
                                       │  └─────────────────────┘    │
                                       │  ┌─────────────────────┐    │
                                       │  │      audit_logs     │    │
                                       │  └─────────────────────┘    │
                                       └─────────────────────────────┘
```

**Key Changes:**
- New notification microservice deployed
- Separate notification-specific database created
- Both systems running independently
- No data synchronization yet

**Implementation Steps:**
1. Deploy notification microservice infrastructure
2. Create new PostgreSQL database for notifications
3. Run database migrations for notification schema
4. Verify service health and API endpoints
5. Perform smoke tests on new service

---

### Phase 3: Remove Monolith Notification Logic + Add Bulk Copier

**Description**: Disable notification functionality in the monolith and introduce a bulk data copier to synchronize existing data.

```
┌─────────────────────────────────────────────┐
│              MONOLITHIC SERVICE             │
├─────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐            │
│  │   Web API   │ │   Admin     │            │
│  └─────────────┘ └─────────────┘            │
│  ┌────────────────────────────────────────┐ │
│  │        Application Logic               │ │
│  │  ┌─────────┐ ┌──────────────────────┐  │ │
│  │  │  User   │ │    NOTIFICATIONS     │  │ │ ◄─── DISABLED
│  │  │  Mgmt   │ │     SUBSYSTEM        │  │ │
│  │  └─────────┘ └─────────[OFF]────────┘  │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐   │ │
│  │  │ Orders  │ │Payments │ │Reports  │   │ │
│  │  └─────────┘ └─────────┘ └─────────┘   │ │
│  └────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │     MONOLITHIC DATABASE     │
        ├─────────────────────────────┤
        │  ┌─────────────────────┐    │
        │  │        users        │    │
        │  └─────────────────────┘    │
        │  ┌─────────────────────┐    │
        │  │     notifications   │    │ ◄─── Still Active
        │  └─────────────────────┘    │
        │  ┌─────────────────────┐    │
        │  │      templates      │    │ ◄─── Still Active
        │  └─────────────────────┘    │
        │  ┌─────────────────────┐    │
        │  │    preferences      │    │ ◄─── Still Active
        │  └─────────────────────┘    │
        │  ┌─────────────────────┐    │
        │  │       orders        │    │
        │  └─────────────────────┘    │
        │         ...more tables      │
        └──┬──────┬───────────────────┘
           │      │
           │      │ ┌─────────────────────────────────────┐
           │      └─┤           BULK COPIER               │ ◄─── NEW
           │        ├─────────────────────────────────────┤
           │        │  ┌─────────────────────────────┐    │
           │        │  │     Historical Data         │    │
           │        │  │        Migration            │    │
           │        │  └─────────────────────────────┘    │
           │        │  ┌─────────────────────────────┐    │
           │        │  │    Schema Mapping           │    │
           │        │  └─────────────────────────────┘    │
           │        │  ┌─────────────────────────────┐    │
           │        │  │   Data Transformation       │    │
           │        │  └─────────────────────────────┘    │
           │        │  ┌─────────────────────────────┐    │
           │        │  │    Progress Tracking        │    │
           │        │  └─────────────────────────────┘    │
           │        └────────────┬────────────────────────┘
           │                     │
           │                     ▼
           │           ┌─────────────────────────────┐
           │           │   NOTIFICATION DATABASE     │
           │           ├─────────────────────────────┤
           │           │  ┌─────────────────────┐    │
           │           │  │     notifications   │    │ ◄─── Being Populated
           │           │  └─────────────────────┘    │
           │           │  ┌─────────────────────┐    │
           │           │  │      templates      │    │ ◄─── Being Populated
           │           │  └─────────────────────┘    │
           │           │  ┌─────────────────────┐    │
           │           │  │    preferences      │    │ ◄─── Being Populated
           │           │  └─────────────────────┘    │
           │           │  ┌─────────────────────┐    │
           │           │  │      audit_logs     │    │
           │           │  └─────────────────────┘    │
           │           └─────────────────────────────┘
           │                     ▲
           │                     │
           │           ┌─────────────────────────────────┐
           └───────────┤      NOTIFICATION SERVICE       │
                       ├─────────────────────────────────┤
                       │  ┌─────────────────────────┐    │
                       │  │       REST API          │    │ ◄─── Active for New Data
                       │  └─────────────────────────┘    │
                       │  ┌─────────────────────────┐    │
                       │  │      GraphQL API        │    │
                       │  └─────────────────────────┘    │
                       │  ┌─────────────────────────┐    │
                       │  │    Business Logic       │    │
                       │  └─────────────────────────┘    │
                       └─────────────────────────────────┘
```

**Key Changes:**
- Notification logic in monolith **disabled**
- Bulk copier service introduced for data migration
- New notification service handling all new requests
- New notification service will try to read and write from/to notification DB and from monolithic DB

**Implementation Steps:**
1. Deploy bulk copier service
2. Disable notification endpoints in monolith (return 503 or redirect)
3. Update monolith to route notification requests to new service
4. Monitor migration progress and data consistency

---

### Phase 4: Dual Read+Write with Online Synchronization

**Description**: Implement dual read+write operations across both databases.

We are going to start the parallel processing and migration, for that we are going to call monolith DB as primary DB and notification DB as secondary.

So we are going to proceed in the following way:

**Implementation Steps:**
1. Notification service will proceed to read from both primary and secondary DB. Service will proceed in the following way
   1. If data is not present in secondary, then it will use data from primary and write it back to secondary
   2. If data is not present in primary, then will proceed to create it in primary with defaults.
   3. If data is in both places, then will diff it and update the one with early time stamp
2. After checks are made that the system is working correctly, we are going to enable bulk copier
   1. Data should flow from primary to secondary, If new or time stamp earlier in primary, then write to secondary.
   2. For log table, mostly copying early entries, there is no update proces as both should have the same entries.
   3. For Preferences and Templates, these tables *should be* smaller than Log table, so less copy quota for them. 
3. Once bulk copy reports 0 copies, then disable it
4. After verifications disable secondary read+write
5. Sunset Notifications subsystem in monolithic service

---

## Migration Checklist

### Pre-Migration Setup
- [ ] Deploy notification microservice infrastructure
- [ ] Create dedicated notification database
- [ ] Run database schema migrations
- [ ] Implement health checks and monitoring
- [ ] Set up logging and observability

### Phase 2: Parallel Deployment
- [ ] Deploy notification service to production
- [ ] Verify API endpoints and functionality
- [ ] Run integration tests
- [ ] Validate service health metrics
- [ ] Document API differences and new features

### Phase 3: Dual Read+Write
- [ ] Enable dual-write mode
- [ ] Set up bidirectional sync monitoring
- [ ] Confirm both DB are being updated
- [ ] Monitor performance and consistency metrics

### Phase 4: Data Migration
- [ ] CHeck configuration for each table
- [ ] Enable and configure bulk copier 
- [ ] Monitor both DB are being updated in parallel

### Phase 4: Clean UP
- [ ] Validate that bulk copier is not copying data
- [ ] Disable and sunset bulk copier
- [ ] Remove notification subsystem 
- [ ] Backup monolithic notifications tables

### Rollback Procedures
- [ ] Document rollback steps for each phase
- [ ] Prepare emergency procedures
- [ ] Test rollback scenarios in staging
- [ ] Define rollback triggers and decision points

---

## Monitoring and Observability

### Key Metrics to Monitor:
- **Data Consistency**: Sync lag, conflict rates, data discrepancies
- **Performance**: API response times, database query performance
- **Reliability**: Error rates, retry success rates, service availability
- **Traffic**: Request distribution, load balancing effectiveness

### Alerting Thresholds:
- Sync lag > 5 seconds
- Data inconsistency rate > 0.1%
- API error rate > 1%
- Service availability < 99.5%

---

## Risk Mitigation

### Identified Risks:
1. **Data Inconsistency**: Resolved by synchronization engine and monitoring
2. **Performance Degradation**: Mitigated by gradual traffic migration
3. **Service Downtime**: Prevented by dual-system operation
4. **Data Loss**: Protected by backup procedures and dual-write

### Contingency Plans:
- **Immediate Rollback**: Redirect all traffic to monolith
- **Data Recovery**: Restore from backups and re-sync
- **Performance Issues**: Adjust traffic distribution
- **Sync Failures**: Pause migration and investigate

---


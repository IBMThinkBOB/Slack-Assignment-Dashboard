# Assignment Visibility & Resource Alignment Platform
## Final Product Specification & AI Agent Build Instructions (v2)

---

# 1. Product Purpose

## Problem Statement

Assignment and project information is scattered across:

- Slack channels
- Excel spreadsheets
- Opportunity systems
- Team leader knowledge
- Skills inventories

Managers lack visibility into:

- Who is working on what
- Whether the right people are assigned
- Which skills are required
- Which skills are missing
- Whether staffing is aligned
- Whether the project is paid, presales, support, or internal
- Project readiness
- BP&E performance

---

# Vision

Create a centralized platform that combines:

```text
Slack Conversations
+
Excel Project Data
+
Skills Inventory
+
BP&E Data
+
Salesforce Opportunities
```

into a single operational dashboard.

The platform should answer:

```text
What projects exist?

Who is assigned?

Who should be assigned?

Do we have required skills?

Do we have staffing gaps?

What is current project status?

Are we qualified to execute?

What does BP&E indicate?

What work is at risk?
```

---

# Core Value

The system is primarily:

```text
VISIBILITY PLATFORM
```

not an automation platform.

Automation is secondary.

The primary goal is:

```text
Project Visibility
+
Resource Alignment
+
Readiness Analysis
+
Manager Oversight
```

---

# 2. User Roles

---

# Admin

Definition:

```text
Team Leader
Practice Lead
Manager
Resource Manager
Delivery Lead
```

Admin assigns work.

Admin monitors work.

Admin controls staffing.

---

## Admin Responsibilities

- Review assignments
- Review staffing
- Review skills requirements
- Review skills gaps
- Review BP&E
- Review readiness
- Assign resources
- Reassign resources
- Monitor project execution

---

# User

Definition:

```text
Engineer
Architect
Consultant
SME
Delivery Team Member
```

Users execute work.

---

## User Responsibilities

- View assignments
- View project details
- View timelines
- View skills requirements
- Update progress
- Complete assignments

---

# Relationship

```text
Manager Creates/Assigns Work
            ↓
      Team Member Executes
```

---

# 3. High-Level Architecture

```text
                      USER SLACK
                           │
                           ▼

                 Assignment Requests

                           │

─────────────────────────────────────────────

                     DATA SOURCES

    Slack       Excel        Salesforce

─────────────────────────────────────────────

                           │
                           ▼

                   DATA INTAKE LAYER

                           │
                           ▼

          ASSIGNMENT CORRELATION ENGINE

                           │
                           ▼

                ASSIGNMENT REPOSITORY

                           │
                           ▼

                 INTELLIGENCE LAYER

                           │
                           ▼

                VISUALIZATION ENGINE

               ┌──────────┴──────────┐
               │                     │

               ▼                     ▼

       ADMIN DASHBOARD       USER DASHBOARD

               │

               ▼

      ADMIN SLACK ALERTS
```

---

# 4. System Flow

---

## Step 1

Assignment request appears in Slack.

Example:

```text
Need Storage Scale deployment support
for ABC Corp.
```

---

## Step 2

Slack Events API captures request.

---

## Step 3

System extracts:

```text
Project Name
Customer
Skill Requirements
Timeline
Assignment Need
Status
```

---

## Step 4

System matches extracted information against:

```text
Excel Project Data

Salesforce Opportunity Data

Skills Inventory

BP&E Data
```

---

## Step 5

Project record created.

---

## Step 6

Admin Dashboard displays:

```text
Project
Timeline
Current Staff
Required Skills
Available Experts
Readiness
BP&E
```

---

## Step 7

Admin assigns resources.

Example:

```text
Storage SME → John

AWS Architect → Sarah

PM → Mike
```

---

## Step 8

Assignments appear in User Dashboard.

---

## Step 9

Users update progress.

---

## Step 10

Managers monitor status.

---

# 5. Data Sources

---

# Slack (Primary Source)

Purpose:

Assignment intake.

Examples:

```text
New assignment

Staffing request

Project discussion

Status update

Resource request
```

---

# Excel (Structured Source)

Purpose:

Project logistics.

Fields:

```text
Project Name
Customer
Description
Start Date
End Date
Project Type
Priority
Progress
Current Team
Required Skills
Manager
Practice
```

---

# Salesforce

Purpose:

Customer opportunity context.

Example:

```text
Opportunity

Account

Customer

Pipeline Stage

Revenue
```

---

# BP&E Repository

Purpose:

Planning and forecasting.

Contains:

```text
Estimated Hours
Actual Hours
Forecasts
Benchmarks
Utilization
```

---

# Skills Inventory

Purpose:

Resource alignment.

Contains:

```text
Employee

Skills

Skill Level

Certifications

Availability

Practice

Experience
```

---

# 6. APIs Required

---

# Slack APIs

## Events API

Purpose:

Receive events.

Examples:

```text
Messages

Threads

Mentions

Reactions
```

---

## Web API

Purpose:

Read and write Slack information.

Required Endpoints:

```text
users.list

users.info

conversations.list

conversations.history

conversations.replies

chat.postMessage

chat.update
```

---

## Slack Interactivity

Purpose:

Buttons and actions.

Examples:

```text
Assign Resource

View Project

Build Workflow

Refresh Data
```

---

# Salesforce APIs

Purpose:

Retrieve project/opportunity context.

Objects:

```text
Opportunity

Account

Contact

Case
```

---

# Microsoft Graph

Purpose:

Resource intelligence.

Services:

```text
Users

Calendars

Availability

Teams

Mail
```

---

# 7. Data Intake Layer

---

# Slack Connector

Responsibilities:

```text
Read assignment requests

Read status updates

Read project discussions
```

---

# Excel Connector

Responsibilities:

```text
Import file

Schedule sync

Read SharePoint file

Read OneDrive file
```

---

# Salesforce Connector

Responsibilities:

```text
Retrieve opportunity details

Link projects to opportunities
```

---

# Graph Connector

Responsibilities:

```text
User information

Availability

Calendar intelligence
```

---

# 8. Assignment Correlation Engine

Purpose:

Build a unified project view.

---

## NLP Extraction

Extract:

```text
Project Name

Customer

Skills

Products

Timeline

Status

Assignment Requests
```

---

## Correlation

Merge:

```text
Slack

Excel

Salesforce

BP&E

Skills Inventory
```

into:

```text
Single Project Record
```

---

# 9. Assignment Repository

Single source of truth.

---

## Project Entity

```json
{
  "projectId": "P001",
  "name": "Storage Scale Deployment",
  "customer": "ABC Corp",
  "status": "In Progress",
  "type": "Paid"
}
```

---

## Resource Entity

```json
{
  "resourceId": "R001",
  "name": "John Smith",
  "availability": "Available"
}
```

---

## Assignment Entity

```json
{
  "projectId": "P001",
  "resourceId": "R001",
  "role": "Storage SME",
  "status": "Assigned"
}
```

---

# 10. Intelligence Layer

---

# Skills Inventory Engine

Purpose:

Manage people and skills.

Fields:

```text
Skill

Level

Certification

Experience

Availability
```

---

# Resource Recommendation Engine

Purpose:

Recommend staffing.

Input:

```text
Required Skills
```

Output:

```text
Best Matching Resources
```

Example:

```text
Storage Scale

John
Raj
Sarah
```

---

# Qualification Alignment Engine

Purpose:

Determine readiness.

Questions:

```text
Do we have required skills?

Do we have enough people?

Are certifications available?

Do staffing gaps exist?
```

---

Output:

```text
Readiness Score
```

Example:

```text
91%

GREEN
```

---

# Staffing Gap Analysis

Purpose:

Find missing skills.

Example:

```text
Required:

Storage
Linux
AWS
Kubernetes

Available:

Storage
Linux
AWS

Gap:

Kubernetes
```

---

# BP&E Analytics Engine

Purpose:

Financial and effort visibility.

Metrics:

```text
Estimated Hours
Actual Hours
Variance
Utilization
Forecasts
```

---

# Workflow Builder

Phase 2.

Admin clicks:

```text
Build Workflow
```

Generates:

```text
Milestones

Tasks

Dependencies

Suggested Timeline
```

---

# 11. Visualization Engine

Most important component.

---

# Dashboard 1

Assignment Overview

Displays:

```text
Project

Customer

Status

Type

Progress

Timeline
```

---

# Dashboard 2

Resource Dashboard

Displays:

```text
Who is assigned

Roles

Workload

Availability
```

---

# Dashboard 3

Skills Dashboard

Displays:

```text
Required Skills

Available Skills

Skill Match

Missing Skills
```

---

# Dashboard 4

Readiness Dashboard

Displays:

```text
Readiness Score

Skill Coverage

Certification Coverage

Availability Coverage
```

---

# Dashboard 5

Staffing Dashboard

Displays:

```text
Assigned

Required

Understaffed

Overallocated
```

---

# Dashboard 6

Timeline Dashboard

Displays:

```text
Start

End

Milestones

Gantt View
```

---

# Dashboard 7

Project Health Dashboard

Displays:

```text
Progress

Blockers

Risks

Status
```

---

# Dashboard 8

BP&E Dashboard

Displays:

```text
Forecast Effort

Actual Effort

Variance

Utilization

Historical Comparisons
```

---

# 12. Admin Dashboard Requirements

Admin Dashboard is the primary interface.

---

## Assignment Oversight

Display:

```text
All Projects

All Assignments

All Teams
```

---

## Staffing Alignment

Display:

```text
Who is staffed?

Who is available?

Who is overloaded?
```

---

## Skill Gaps

Display:

```text
Required

Available

Missing
```

---

## Readiness

Display:

```text
Coverage

Alignment

Readiness Score
```

---

## Assignment Actions

Admin can:

```text
Assign User

Reassign User

Remove Assignment

Build Workflow
```

---

## BP&E Management

Display:

```text
Forecasts

Benchmarks

Variances
```

---

## Reporting

Generate:

```text
Project Reports

Readiness Reports

Staffing Reports

BP&E Reports
```

---

# 13. User Dashboard Requirements

User Dashboard is assignment-focused.

---

Display:

```text
My Assignments

My Projects

Required Skills

Timeline

Milestones

Progress

Status
```

---

Users Can:

```text
Update Status

Update Progress

View Deliverables
```

---

Cannot:

```text
Manage Projects

Assign Resources

Modify Readiness Models
```

---

# 14. MVP Prototype Scope

---

# Phase 1

Build:

```text
Slack Integration

Excel Upload

Project Repository

Assignment Dashboard
```

---

# Phase 2

Build:

```text
Skills Inventory

Resource Recommendations

Readiness Dashboard

Staffing Dashboard
```

---

# Phase 3

Build:

```text
Salesforce Integration

Microsoft Graph

BP&E Dashboard
```

---

# Phase 4

Build:

```text
Workflow Builder

Admin Slack Alerts

Advanced Analytics

Forecasting
```

---

# Prototype Success Criteria

The MVP is successful when a manager can:

```text
1. Post or detect an assignment from Slack

2. Automatically correlate it with Excel data

3. View project details

4. View required skills

5. View recommended resources

6. Assign team members

7. Monitor project progress

8. Evaluate staffing readiness

9. Review BP&E metrics

10. View all information in a single dashboard
```

This is the primary outcome the prototype must demonstrate.
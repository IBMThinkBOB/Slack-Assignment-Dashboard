# Slack Assignment Simulator Fix Specification
## Task Claiming, Assignment Ownership, Dashboard Synchronization, and Conversation Flow

Version: 1.0

---

# Overview

The current Slack Simulator successfully creates project records from messages, but it does not accurately model how managers and team members interact around assignment ownership.

The simulator currently has three major issues:

1. Messages appear out of logical order
2. Assignment claiming workflows are incomplete
3. Dashboard ownership does not update when work is claimed

The objective of this specification is to redesign the simulator around a proper assignment lifecycle so that it behaves like a real Slack-based team assignment system.

---

# Desired User Experience

## Scenario 1 — Manager Assigns Work Directly

Admin sends:

```text
@Aman build a cloud application for Morgan Stanley
```

System should:

```text
Create Assignment
Assign Owner = Aman
Status = Assigned
```

Dashboard immediately updates:

```text
Project: Morgan Stanley App
Assigned To: Aman
Status: Assigned
```

---

## Scenario 2 — Manager Posts Work for Team

Admin sends:

```text
Need a Storage Scale SME for ABC Corp.
```

System should:

```text
Create Assignment
Status = Unclaimed
Owner = None
```

Dashboard shows:

```text
Project: ABC Corp Storage Deployment
Assigned To: Unassigned
Status: Unclaimed
```

---

## Scenario 3 — Employee Claims Work Using Button

Admin posts:

```text
Need Storage Scale SME for ABC Corp.
```

Simulator displays:

```text
[Claim Task]
```

User clicks:

```text
Claim Task
```

System updates:

```text
Assigned To = User
Status = Claimed
```

Dashboard updates immediately.

---

## Scenario 4 — Employee Claims Work Via Chat Message

Admin:

```text
Need AWS Architect for Globex.
```

User:

```text
I'll take it.
```

System detects:

```text
Claim Intent
```

Assignment updates:

```text
Assigned To = User
Status = Claimed
```

Dashboard updates.

---

## Scenario 5 — Employee Claims Work Via Affirmation

Supported responses:

```text
Yes

Sure

I can do it

I'll handle it

Assign it to me

Count me in
```

All should be treated as:

```text
CLAIM_ASSIGNMENT
```

for the most recent unclaimed project.

---

# Core Assignment Lifecycle

Every project generated from Slack must have an assignment state.

---

## State Machine

```text
CREATED
   ↓

UNCLAIMED
   ↓

ASSIGNED
   ↓

IN_PROGRESS
   ↓

COMPLETED
```

---

## State Definitions

### CREATED

Assignment detected from Slack.

Example:

```text
Need OpenShift architect for customer XYZ.
```

System extracts project.

---

### UNCLAIMED

No owner exists.

```json
{
  "owner": null,
  "status": "UNCLAIMED"
}
```

---

### ASSIGNED

Owner exists.

```json
{
  "owner": "Aman",
  "status": "ASSIGNED"
}
```

---

### IN_PROGRESS

Employee has acknowledged and begun work.

```json
{
  "owner": "Aman",
  "status": "IN_PROGRESS"
}
```

---

### COMPLETED

Work is finished.

```json
{
  "owner": "Aman",
  "status": "COMPLETED"
}
```

---

# Conversation Ordering Fix

## Current Issue

Messages are appearing randomly or asynchronously.

Example:

```text
Employee response

appears

before

Admin request.
```

This breaks assignment context.

---

## Required Behavior

Messages must always be rendered using:

```text
message.createdAt
```

ascending order.

---

## Rule

Every message must contain:

```typescript
{
    id: string;
    text: string;
    userId: string;
    timestamp: number;
}
```

Messages should always be sorted:

```typescript
messages.sort(
    (a, b) => a.timestamp - b.timestamp
);
```

before rendering.

---

# Direct Mention Assignment

## Requirement

Admin should be able to assign someone directly.

Example:

```text
@Aman build Morgan Stanley app.
```

---

## Expected Behavior

System extracts:

```json
{
    "assignedUser": "Aman"
}
```

Creates:

```json
{
    "project": "Morgan Stanley App",
    "assignedTo": "Aman",
    "status": "ASSIGNED"
}
```

---

## Dashboard Update

Immediately update:

```text
Assigned To = Aman
```

---

# Claim Button Support

## Requirement

Every unclaimed assignment should display a Claim button.

---

## Display

Example:

```text
Need Storage Scale SME for ABC Corp.

[Claim Task]
```

---

## User Click

When clicked:

```text
Owner = Current User
Status = Claimed
```

---

## System Message

Automatically create:

```text
✅ Aman claimed Storage Scale Deployment
```

---

# NLP Claim Detection

## Requirement

Detect intent to claim work.

---

## Supported Phrases

Examples:

```text
I'll do it

I can take this

Yes

Sure

Happy to help

Count me in

Assign it to me

I can handle it

I will take this project
```

---

## Detection Rule

If:

```text
User Message
```

contains claim intent

AND

an unclaimed assignment exists

Then:

```text
Claim assignment
```

---

## Example

Admin:

```text
Need AWS Architect for Globex.
```

User:

```text
I'll take it.
```

Result:

```json
{
    "assignedTo": "Aman",
    "status": "CLAIMED"
}
```

---

# Dashboard Synchronization

## Current Issue

Slack simulator updates are not reflected on dashboard ownership.

---

## Required Behavior

Whenever assignment ownership changes:

```text
Slack Simulator
```

must update:

```text
Assignment Repository
```

which updates:

```text
Dashboard
```

---

# Ownership Updates

These actions must update the dashboard:

---

## Direct Assignment

```text
@Aman do this
```

---

## Claim Button

```text
Claim Task
```

---

## NLP Claim

```text
I'll take it.
```

---

## Admin Reassignment

```text
Assign Sarah instead.
```

---

# Dashboard Changes

## Add New Column

Existing:

```text
Project
Customer
Status
Progress
```

New:

```text
Assigned To
```

---

## Example

```text
Project                    Assigned To
----------------------------------------
Storage Deployment         Aman
AWS Architecture           Sarah
OpenShift Upgrade          Unassigned
```

---

# My Assignments Dashboard

## Requirement

User dashboard should automatically populate from assignment ownership.

---

## Example

Logged-in User:

```text
Aman
```

Assignments:

```text
Storage Deployment

Morgan Stanley App

Globex AWS Architecture
```

---

## Query

```sql
SELECT *
FROM assignments
WHERE assigned_to = current_user
```

---

# Slack Simulator Behavior

---

## Admin Mode

Can:

```text
Create Work

Assign Work

Mention Team Members

View Status
```

---

## User Mode

Can:

```text
Claim Work

Accept Work

Update Status

Complete Work
```

---

# Suggested Data Model

## Projects

```typescript
Project
{
    id: string;
    name: string;
    customer: string;
    type: string;
    status: string;
}
```

---

## Assignments

```typescript
Assignment
{
    id: string;
    projectId: string;
    assignedTo: string | null;
    status: AssignmentStatus;
    createdBy: string;
    createdAt: Date;
}
```

---

## Messages

```typescript
Message
{
    id: string;
    text: string;
    sender: string;
    timestamp: Date;
}
```

---

# Event Architecture

```text
Slack Message
      ↓

Assignment Detector
      ↓

Assignment Repository

      ↓

Dashboard
```

When ownership changes:

```text
Claim Button
      ↓

Repository Update
      ↓

Dashboard Refresh
      ↓

My Assignments Refresh
      ↓

Slack Confirmation Message
```

---

# Acceptance Criteria

The implementation is considered successful when:

## AC1

Messages always appear chronologically.

---

## AC2

Admin can mention users:

```text
@Aman
```

and auto-assign projects.

---

## AC3

Users can claim work using:

```text
Claim Button
```

---

## AC4

Users can claim work using:

```text
I'll take it.
```

or equivalent affirmative responses.

---

## AC5

Ownership updates immediately appear in:

```text
Assignment Overview Dashboard
```

---

## AC6

Ownership updates immediately appear in:

```text
My Assignments
```

---

## AC7

Unassigned projects show:

```text
Assigned To = Unassigned
```

---

## AC8

Assigned projects show:

```text
Assigned To = Employee Name
```

---

## AC9

Slack simulator displays system confirmation messages.

Example:

```text
✅ Aman claimed Storage Scale Deployment
```

---

## AC10

The assignment system behaves like a realistic manager/team-member workflow:

```text
Manager Creates Assignment
        ↓

Employee Claims Work
        ↓

Ownership Recorded
        ↓

Dashboard Updated
        ↓

Work Progress Tracked
```
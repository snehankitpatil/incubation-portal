# Incubation Portal

An Incubation Resource Management System for managing halls, startups, seat allocations, utilization monitoring, and audit-ready reporting.

## Features

- Startup registration with seat validation
- Dynamic seat allocation & release
- Multi-hall capacity management
- Allocation history audit log
- Real-time utilization metrics
- Rule-based system alerts
- Reports dashboard with previews
- CSV exports for startups and allocations

## Tech Stack

- Backend: Flask (Python)
- Database: PostgreSQL
- ORM: SQLAlchemy
- Templating: Jinja2
- Frontend: HTML, CSS (minimal, text-first)

## Key Design Principles

- Separation of operations and reporting
- Event-based allocation tracking
- Read-only analytical reports
- Enterprise-style navigation & UX

## Reports

- Startup Report (current state)
- Allocation History (audit trail)
- Hall Utilization Summary
- System Alerts

## Use Cases

- Incubation center administration
- Capacity planning
- Operational monitoring
- Audit & compliance reporting

## How to Run

```bash
python3 app.py

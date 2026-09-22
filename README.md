# Mini CRM: Lead Distribution Across Operators

A compact FastAPI service for registering leads and distributing incoming contacts across operators. Assignment is based on per-source weights, operator availability, and active-contact limits.

## Features

- CRUD APIs for operators, sources, leads, and contacts
- weighted operator assignment configured independently for each source
- workload limits based on each operator's open contacts
- unassigned contact preservation when no operator is available
- SQLite storage through SQLAlchemy
- Alembic migrations
- Docker Compose tasks and automated tests

## Run the project

### Locally

1. Install dependencies with [uv](https://docs.astral.sh/uv/):

   ```bash
   uv sync
   ```

2. Start the application:

   ```bash
   uv run uvicorn app.main:app --reload
   ```

The service is then available at:

- Swagger UI: <http://localhost:8000/docs>
- health check: <http://localhost:8000/health>

### With Docker

Build and run in the foreground:

```bash
uv run invoke docker-build
```

Run in the background:

```bash
uv run invoke docker-up
```

Stop the services:

```bash
uv run invoke docker-down
```

Run `uv run invoke help` to see all available project tasks.

## Data model

The service uses SQLite and SQLAlchemy. Its main entities are:

- `Operator`: handles incoming contacts. The `is_active` flag controls availability, and `max_active_contacts` sets the workload limit.
- `Source`: identifies the bot, channel, or other source that produced a contact.
- `OperatorSourceWeight`: links an operator to a source and stores the numeric assignment weight. Each `(operator_id, source_id)` pair is unique.
- `Lead`: represents an end customer. Its `external_id` is unique.
- `Contact`: represents a lead interaction from a particular source. It may remain unassigned when no eligible operator is available.

## Contact assignment

### Lead resolution

When `POST /api/contacts/` receives a contact, the service looks up a lead by `Lead.external_id = external_lead_id`. It reuses the existing lead or creates a new one, so contacts with the same external ID belong to the same lead.

### Source-specific weights

For the selected source, the service loads all `OperatorSourceWeight` records. After filtering unavailable operators, it makes a weighted random selection with `random.choices`:

```text
selection probability = operator weight / sum of eligible operator weights
```

### Workload limits

An operator's current workload is the number of assigned contacts whose status is `open`. An operator is eligible only when both conditions hold:

```text
operator.is_active = true
open contacts < operator.max_active_contacts
```

### No eligible operator

If no operator passes the filters, the service still stores the contact with `operator_id = null`. This prevents data loss and makes unassigned contacts available for later manual processing.

## Tests

Run the test suite locally:

```bash
uv run pytest
```

Or run it inside the API container:

```bash
uv run invoke tests
```

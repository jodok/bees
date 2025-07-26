# Beehive monitoring

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Database Setup

Start the PostgreSQL database:

```bash
docker-compose up -d postgres
```

## Database Migrations

When you modify the `ATTRIBUTES` in `settings.py`, you need to update the database schema.

### Quick Migration (Development)

Drops and recreates all tables (loses all data):

```bash
python migrate.py quick
```

### Alembic Migration (Production)

Preserves existing data:

```bash
# Create a new migration
python migrate.py alembic

# Review the generated migration file in migrations/versions/
# Then apply it:
alembic upgrade head
```

### Manual Migration

You can also run migrations directly:

```bash
# Drop and recreate all tables
python database.py

# Or use Alembic directly
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

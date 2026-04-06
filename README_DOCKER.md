# Docker Setup Guide

## Quick Start

```bash
docker-compose up --build
```

This will start:
- Neo4j at http://localhost:7474
- Backend API at http://localhost:8000
- Frontend UI at http://localhost:3000

## Services

### Neo4j
- Web UI: http://localhost:7474
- Bolt: bolt://localhost:7687
- Default credentials: neo4j/password123

### Backend API
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Frontend
- Dashboard: http://localhost:3000

## Environment Variables

Create a `.env` file for custom configuration:

```env
NEO4J_PASSWORD=your_password
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
```

## CLI Usage (Still Works)

The CLI workflow continues to work:

```bash
# Run inside backend container
docker-compose exec backend python -m backend.app.main --cloud aws

# Or locally (if dependencies installed)
python -m backend.app.main --cloud aws
```

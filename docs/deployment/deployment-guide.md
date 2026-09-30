# Deployment Guide

## Production Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Set strong values for: POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY
# Set ENVIRONMENT=production
# Set LLM_PROVIDER and API keys as needed

# Build and start production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Run database migrations
docker compose exec backend alembic upgrade head
```

## Security Checklist

- [ ] `SECRET_KEY` is a random 64-character string
- [ ] `POSTGRES_PASSWORD` is strong and unique
- [ ] `REDIS_PASSWORD` is set
- [ ] `DEBUG=False` in production
- [ ] `CORS_ORIGINS` restricted to your domain
- [ ] No API keys in Git history
- [ ] SSL termination at nginx or load balancer
- [ ] `MAX_UPLOAD_SIZE_MB` set appropriately
- [ ] File upload directory is outside the web root

## Environment Variables Reference

See `.env.example` for all variables with descriptions.

Critical production variables:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing key — random 64 chars |
| `DATABASE_URL` | PostgreSQL async DSN |
| `REDIS_URL` | Redis connection with password |
| `ENVIRONMENT` | Must be `production` |
| `LLM_PROVIDER` | `demo`, `openai`, or `gemini` |

## Scaling

- **Backend**: Increase `uvicorn --workers` in production Dockerfile (default: 4)
- **Worker**: Run multiple `worker` containers; they share the Redis queue
- **Database**: Vertical scaling first; pgvector performs well on a single instance

## Health Checks

```bash
# API health
curl http://localhost:8000/health

# Worker health
docker compose exec worker python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

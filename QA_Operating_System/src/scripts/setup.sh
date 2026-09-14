#!/bin/bash
echo "=== AI QA Operating System Setup ==="
if ! command -v docker &> /dev/null; then echo "Docker not found!"; exit 1; fi
if [ ! -f .env ]; then cp .env.example .env; fi
uv sync --all-packages
pnpm install
docker-compose up -d
sleep 15
uv run python infra/postgres/run_migrations.py
uv run pytest --tb=short -q
echo "Setup complete!"

# One-command setup for AI QA OS
$env:Path = "C:\Users\$env:USERNAME\.local\bin;$env:Path"
Write-Host "=== AI QA Operating System Setup ==" -ForegroundColor Cyan
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Write-Error "Docker not found!"; exit 1 }
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv sync --all-packages
pnpm install
docker-compose up -d
Start-Sleep -Seconds 15
uv run python infra/postgres/run_migrations.py
uv run pytest --tb=short -q
Write-Host "Setup complete!" -ForegroundColor Green

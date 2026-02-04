# Docker PostgreSQL Setup Guide

## 🐳 Quick Setup (Recommended)

### Option 1: Using Docker Compose (Easiest)

```powershell
# Start PostgreSQL
docker-compose up -d

# Check if running
docker-compose ps

# View logs
docker-compose logs -f

# Stop PostgreSQL
docker-compose down

# Stop and remove data
docker-compose down -v
```

### Option 2: Using Docker Command

```powershell
# Start PostgreSQL
docker run --name news-postgres `
  -e POSTGRES_USER=admin `
  -e POSTGRES_PASSWORD=admin `
  -e POSTGRES_DB=newsdb `
  -p 5432:5432 `
  -d postgres:15

# Check if running
docker ps

# View logs
docker logs news-postgres

# Stop PostgreSQL
docker stop news-postgres

# Start again
docker start news-postgres

# Remove container
docker rm news-postgres
```

## 📋 Prerequisites

1. **Install Docker Desktop for Windows**
   - Download from: https://www.docker.com/products/docker-desktop/
   - Install and restart your computer
   - Start Docker Desktop

2. **Verify Docker is running**
   ```powershell
   docker --version
   ```

## 🚀 Complete Workflow

### 1. Start PostgreSQL
```powershell
docker-compose up -d
```

### 2. Verify Connection
```powershell
# Connect to PostgreSQL CLI
docker exec -it news-postgres psql -U admin -d newsdb

# Inside psql, try:
\l                  # List databases
\q                  # Quit
```

### 3. Setup Database Schema
```powershell
python setup_database.py
```

### 4. Run the Scraper
```powershell
python refresh_articles.py
```

## 🔧 Useful Commands

### Check Database
```powershell
# List all tables
docker exec -it news-postgres psql -U admin -d newsdb -c "\dt"

# Count articles
docker exec -it news-postgres psql -U admin -d newsdb -c "SELECT COUNT(*) FROM articles;"

# View recent articles
docker exec -it news-postgres psql -U admin -d newsdb -c "SELECT title, category FROM articles LIMIT 5;"
```

### Backup Database
```powershell
# Backup
docker exec -t news-postgres pg_dump -U admin newsdb > backup.sql

# Restore
docker exec -i news-postgres psql -U admin newsdb < backup.sql
```

### Reset Everything
```powershell
# Stop and remove everything
docker-compose down -v

# Start fresh
docker-compose up -d
python setup_database.py
```

## 📊 Database Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** newsdb
- **User:** admin
- **Password:** admin

These credentials are already configured in your `.env` file.

## ✅ Why Docker?

✓ Clean setup (no Windows PostgreSQL installation)
✓ Same environment as production
✓ Easy to reset/delete
✓ Professional approach for interviews
✓ No configuration conflicts
✓ Portable across machines

## 🐛 Troubleshooting

**Port already in use:**
```powershell
# Check what's using port 5432
netstat -ano | findstr :5432

# Stop other PostgreSQL services
Get-Service -Name postgresql* | Stop-Service
```

**Docker not starting:**
- Make sure Docker Desktop is running
- Check if WSL 2 is enabled (Settings > General > Use WSL 2)

**Connection refused:**
```powershell
# Wait a few seconds after starting
docker-compose up -d
Start-Sleep -Seconds 5
python setup_database.py
```

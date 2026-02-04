# News Suggestion System - Day 1

## Setup Instructions

### 1. Install Docker Desktop
- Download from https://www.docker.com/products/docker-desktop/
- Install and restart Windows
- Start Docker Desktop

### 2. Start PostgreSQL with Docker
```powershell
docker-compose up -d
```

### 3. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Setup Database
```powershell
python setup_database.py
```

### 5. Run the Scraper
```powershell
python refresh_articles.py
```

**📚 See [docker-setup.md](docker-setup.md) for detailed Docker instructions**

## Project Structure
- `setup_database.py` - Creates the articles table
- `scraper.py` - Article scraping logic
- `text_cleaner.py` - Text cleaning utilities
- `refresh_articles.py` - Main script to fetch and store articles
- `config.py` - Configuration management

## Database Schema
- **articles** table with:
  - id (primary key)
  - title
  - content
  - category
  - published_date
  - source
  - url
  - created_at

# News Recommendation API - Usage Guide

## 🚀 Quick Start

The API runs on **http://localhost:8000**

Open in browser: http://localhost:8000/docs (interactive Swagger UI)

## 📋 Available Endpoints

### 1. **GET /** - API Info
```bash
curl http://localhost:8000
```
Returns API version and available endpoints.

### 2. **GET /stats** - Database Statistics
```bash
curl http://localhost:8000/stats
```
**Response:**
```json
{
  "total_articles": 650,
  "categories": {
    "health": 130,
    "sports": 120,
    "technology": 108,
    "business": 84,
    "science": 84,
    "entertainment": 68,
    "general": 56
  },
  "sources": 187
}
```

### 3. **GET /articles** - List Articles (Paginated)
```bash
# Basic pagination
curl "http://localhost:8000/articles?page=1&page_size=10"

# Filter by category
curl "http://localhost:8000/articles?category=technology"

# Search in titles
curl "http://localhost:8000/articles?search=storm"

# Combined filters
curl "http://localhost:8000/articles?category=sports&search=NBA&page=1&page_size=5"
```

**Query Parameters:**
- `page` (default: 1) - Page number
- `page_size` (default: 10, max: 100) - Items per page
- `category` (optional) - Filter by category
- `search` (optional) - Search in article titles

**Response:**
```json
{
  "articles": [
    {
      "id": 272,
      "title": "...",
      "content": "...",
      "category": "technology",
      "source": "...",
      "published_at": "2026-01-24T17:56:54",
      "created_at": "2026-01-25T18:17:35.372552"
    }
  ],
  "total": 108,
  "page": 1,
  "page_size": 10
}
```

### 4. **GET /articles/{id}** - Get Single Article
```bash
curl http://localhost:8000/articles/1
```

**Response:**
```json
{
  "id": 1,
  "title": "Why long-lasting power outages could be a big problem...",
  "content": "...",
  "category": "business",
  "source": "The Washington Post",
  "published_at": "2026-01-23T20:56:18",
  "created_at": "2026-01-25T18:17:35.372552"
}
```

### 5. **GET /recommend/{id}** - Get Recommendations ⭐
```bash
# Get 5 recommendations (default)
curl http://localhost:8000/recommend/1

# Get 10 recommendations
curl "http://localhost:8000/recommend/1?top_n=10"
```

**Query Parameters:**
- `top_n` (default: 5, max: 20) - Number of recommendations

**Response:**
```json
{
  "article_id": 1,
  "article_title": "Why long-lasting power outages...",
  "recommendations": [
    {
      "id": 253,
      "title": "Latest NBA, NHL, CBB, Schedule Adjustments...",
      "category": "sports",
      "source": "Bleacher Report",
      "similarity": 0.1299,
      "published_at": "2026-01-23T22:18:45"
    }
  ],
  "total": 2
}
```

## 🎯 Example Use Cases

### 1. Build a News Feed
```python
import requests

# Get latest technology articles
response = requests.get(
    "http://localhost:8000/articles",
    params={"category": "technology", "page": 1, "page_size": 10}
)
articles = response.json()['articles']
```

### 2. Show "Related Articles"
```python
# User reads article ID 42, show similar articles
response = requests.get(f"http://localhost:8000/recommend/42?top_n=5")
recommendations = response.json()['recommendations']
```

### 3. Search Articles
```python
# Search for articles about "AI"
response = requests.get(
    "http://localhost:8000/articles",
    params={"search": "AI", "page_size": 20}
)
```

## 🔥 ML Pipeline Details

The recommendation engine uses:
- **TF-IDF Vectorization** with 5000 features
- **Bigrams** (1-2 word phrases)
- **Stop words** removed (English)
- **Cosine similarity** for content matching
- **Near-duplicate filtering** (>98% similarity removed)

**How it works:**
1. All article titles + content are vectorized using TF-IDF
2. When you request recommendations for article X:
   - Compute cosine similarity between X and all other articles
   - Filter out self-matches and near-duplicates
   - Return top-N most similar articles
3. Similarity scores range from 0-1 (higher = more similar)

## 📊 Data Overview

- **Total Articles:** 650
- **Categories:** 7 (business, entertainment, general, health, science, sports, technology)
- **Sources:** 187 unique news sources
- **Update Frequency:** Run `docker exec -it news-app python refresh_articles.py` to fetch new articles

## 🛠️ Technical Stack

- **Framework:** FastAPI 0.115.5
- **Server:** Uvicorn with async workers
- **Database:** PostgreSQL 15
- **ML Libraries:** scikit-learn, numpy, pandas
- **Deployment:** Docker Compose

## 🌐 Interactive Documentation

Visit **http://localhost:8000/docs** for:
- Interactive API testing (Swagger UI)
- Automatic request validation
- Response schema documentation
- Try-it-out functionality

## 📝 Resume-Ready Description

> Built a Dockerized news recommendation REST API using FastAPI and PostgreSQL, implementing content-based filtering with TF-IDF vectorization and cosine similarity over 650+ real news articles from 187 sources across 7 categories.

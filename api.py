"""
FastAPI REST API for News Recommendation System
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import psycopg
from recommender_embeddings import NewsRecommender  # Using embedding-based recommender
from config import DB_CONFIG
import os

# Initialize FastAPI
app = FastAPI(
    title="News Recommendation API",
    description="Content-based news recommendation system using TF-IDF",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection string (use 'postgres' hostname inside Docker network)
conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@postgres:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Initialize recommender (lazy loading)
recommender = None

def get_recommender():
    """Get or initialize embedding-based recommender instance"""
    global recommender
    if recommender is None:
        recommender = NewsRecommender(conn_string)
        recommender.load_articles()
        recommender.build_embedding_matrix()  # Build embedding matrix instead of TF-IDF
        recommender.calculate_popularity_scores()  # Cache popularity scores
    return recommender

# Pydantic models
class Article(BaseModel):
    id: int
    title: str
    content: Optional[str]
    category: str
    source: str
    published_at: datetime
    created_at: datetime

class ArticleListResponse(BaseModel):
    articles: List[Article]
    total: int
    page: int
    page_size: int

class Recommendation(BaseModel):
    id: int
    title: str
    category: str
    source: str
    similarity: float
    published_at: datetime

class RecommendationResponse(BaseModel):
    article_id: int
    article_title: str
    recommendations: List[Recommendation]
    total: int

class StatsResponse(BaseModel):
    total_articles: int
    categories: dict
    sources: int

class InteractionRequest(BaseModel):
    article_id: int
    user_id: Optional[str] = "anonymous"  # For demo, allow anonymous tracking
    interaction_type: str = "view"  # view, click, like, dislike
    rating: Optional[float] = None  # 1-5 if provided

class InteractionResponse(BaseModel):
    success: bool
    message: str

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Routes
@app.get("/", include_in_schema=False)
def root():
    """Serve the frontend demo"""
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {
        "message": "News Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "articles": "/articles",
            "article_detail": "/articles/{id}",
            "recommendations": "/recommend/{id}",
            "stats": "/stats"
        }
    }

@app.get("/api")
def api_info():
    """API root endpoint"""
    return {
        "message": "News Recommendation API",
        "version": "1.0.0",
        "endpoints": {
            "articles": "/articles",
            "article_detail": "/articles/{id}",
            "recommendations": "/recommend/{id}",
            "stats": "/stats"
        }
    }

@app.get("/articles", response_model=ArticleListResponse)
def get_articles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title")
):
    """
    Get paginated list of articles with optional filtering.
    """
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Build query
                conditions = []
                params = []
                
                if category:
                    conditions.append("category = %s")
                    params.append(category)
                
                if search:
                    conditions.append("title ILIKE %s")
                    params.append(f"%{search}%")
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                # Get total count
                count_query = f"SELECT COUNT(*) FROM articles {where_clause}"
                cur.execute(count_query, params)
                total = cur.fetchone()[0]
                
                # Get paginated articles
                offset = (page - 1) * page_size
                query = f"""
                    SELECT id, title, content, category, source, published_at, created_at
                    FROM articles
                    {where_clause}
                    ORDER BY published_at DESC
                    LIMIT %s OFFSET %s
                """
                params.extend([page_size, offset])
                
                cur.execute(query, params)
                articles = [
                    Article(
                        id=row[0],
                        title=row[1],
                        content=row[2],
                        category=row[3],
                        source=row[4],
                        published_at=row[5],
                        created_at=row[6]
                    )
                    for row in cur.fetchall()
                ]
                
                return ArticleListResponse(
                    articles=articles,
                    total=total,
                    page=page,
                    page_size=page_size
                )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int):
    """
    Get a single article by ID.
    """
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, content, category, source, published_at, created_at
                    FROM articles
                    WHERE id = %s
                    """,
                    (article_id,)
                )
                row = cur.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Article not found")
                
                return Article(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    category=row[3],
                    source=row[4],
                    published_at=row[5],
                    created_at=row[6]
                )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/recommend/{article_id}", response_model=RecommendationResponse)
def get_recommendations(
    article_id: int,
    top_n: int = Query(5, ge=1, le=20, description="Number of recommendations"),
    use_hybrid: bool = Query(True, description="Use hybrid (content + popularity) recommendations")
):
    """
    Get recommendations for an article.
    
    Supports two modes:
    - Hybrid (default): Combines content similarity (70%) + popularity (30%)
    - Content-only: Pure TF-IDF cosine similarity
    """
    try:
        # Get article details
        rec = get_recommender()
        article = rec.get_article_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get recommendations based on mode
        if use_hybrid:
            recommendations = rec.get_hybrid_recommendations(article_id, top_n=top_n)
        else:
            recommendations = rec.get_similar_articles(article_id, top_n=top_n)
        
        # Return response even if empty (graceful degradation)
        return RecommendationResponse(
            article_id=article_id,
            article_title=article['title'],
            recommendations=[
                Recommendation(
                    id=r['id'],
                    title=r['title'],
                    category=r['category'],
                    source=r['source'],
                    similarity=r.get('hybrid_score', r['similarity']),  # Use hybrid score if available
                    published_at=r['published_at']
                )
                for r in recommendations
            ],
            total=len(recommendations)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Get database statistics.
    """
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Total articles
                cur.execute("SELECT COUNT(*) FROM articles")
                total = cur.fetchone()[0]
                
                # Articles by category
                cur.execute("""
                    SELECT category, COUNT(*) 
                    FROM articles 
                    GROUP BY category 
                    ORDER BY COUNT(*) DESC
                """)
                categories = {row[0]: row[1] for row in cur.fetchall()}
                
                # Unique sources
                cur.execute("SELECT COUNT(DISTINCT source) FROM articles")
                sources = cur.fetchone()[0]
                
                return StatsResponse(
                    total_articles=total,
                    categories=categories,
                    sources=sources
                )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/track", response_model=InteractionResponse)
def track_interaction(interaction: InteractionRequest):
    """
    Track user interaction with articles (views, clicks, ratings)
    This enables collaborative filtering and popularity-based recommendations
    """
    try:
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Verify article exists
                cur.execute("SELECT id FROM articles WHERE id = %s", (interaction.article_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Article not found")
                
                # Insert interaction
                cur.execute("""
                    INSERT INTO interactions 
                    (user_id, article_id, interaction_type, rating, created_at)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (
                    interaction.user_id,
                    interaction.article_id,
                    interaction.interaction_type,
                    interaction.rating
                ))
                conn.commit()
                
                return InteractionResponse(
                    success=True,
                    message=f"Tracked {interaction.interaction_type} for article {interaction.article_id}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track interaction: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

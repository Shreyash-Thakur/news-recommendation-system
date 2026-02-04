"""
Embedding-based content recommendation engine for news articles.

Uses SentenceTransformer embeddings (cached in database) for semantic similarity.
Falls back to TF-IDF if embeddings not available.
"""

import psycopg
import numpy as np
import pandas as pd
import json
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple


class NewsRecommender:
    """Content-based recommendation engine using embeddings"""
    
    def __init__(self, conn_string: str = "postgresql://admin:admin123@postgres:5432/newsdb"):
        """
        Initialize recommender with database connection.
        
        Args:
            conn_string: PostgreSQL connection string
        """
        self.conn_string = conn_string
        self.articles_df = None
        self.embedding_matrix = None
        self.popularity_scores = {}
        
    def load_articles(self) -> pd.DataFrame:
        """
        Load articles with embeddings from database.
        
        Returns:
            DataFrame with article data and embeddings
        """
        conn = psycopg.connect(self.conn_string)
        
        query = """
        SELECT id, title, content, category, source, published_at, embedding
        FROM articles
        WHERE embedding IS NOT NULL
        ORDER BY id
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
            
        conn.close()
        
        if not rows:
            raise ValueError("No articles with embeddings found. Run generate_embeddings.py first.")
        
        self.articles_df = pd.DataFrame(rows, columns=columns)
        print(f"✅ Loaded {len(self.articles_df)} articles with embeddings")
        
        return self.articles_df
    
    def build_embedding_matrix(self) -> np.ndarray:
        """
        Convert stored JSON embeddings to numpy matrix.
        
        Returns:
            Numpy array of shape (n_articles, embedding_dim)
        """
        if self.articles_df is None:
            raise ValueError("Load articles first using load_articles()")
        
        # Parse JSON embeddings into numpy arrays
        embeddings = []
        for emb_json in self.articles_df['embedding']:
            emb_array = np.array(json.loads(emb_json))
            embeddings.append(emb_array)
        
        self.embedding_matrix = np.vstack(embeddings)
        print(f"✅ Built embedding matrix: {self.embedding_matrix.shape}")
        
        return self.embedding_matrix
    
    def calculate_popularity_scores(self) -> Dict[int, float]:
        """
        Calculate popularity scores from interactions table.
        Uses views, clicks, and recency weighting.
        
        Returns:
            Dictionary mapping article_id to popularity score (0-1)
        """
        conn = psycopg.connect(self.conn_string)
        
        query = """
        SELECT 
            article_id,
            COUNT(*) as interaction_count,
            MAX(created_at) as last_interaction,
            EXTRACT(EPOCH FROM (NOW() - MAX(created_at)))/86400 as days_since
        FROM interactions
        WHERE interaction_type IN ('view', 'click')
        GROUP BY article_id
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            results = cur.fetchall()
        
        conn.close()
        
        if not results:
            # Cold start: no interactions yet
            return {aid: 0.0 for aid in self.articles_df['id']}
        
        # Calculate normalized popularity
        max_interactions = max(row[1] for row in results)
        
        scores = {}
        for article_id, count, last_interaction, days_since in results:
            # Recency decay: exponential with 7-day half-life
            recency_weight = np.exp(-days_since / 7.0) if days_since else 1.0
            
            # Popularity = interaction_count * recency
            raw_score = (count / max_interactions) * recency_weight
            scores[article_id] = min(raw_score, 1.0)
        
        # Fill missing articles with 0
        for aid in self.articles_df['id']:
            if aid not in scores:
                scores[aid] = 0.0
        
        self.popularity_scores = scores
        return scores
    
    def get_similar_articles(
        self, 
        article_id: int, 
        top_n: int = 10,
        hybrid_weight: float = 0.7,  # 0.7 content + 0.3 popularity
        category_boost: float = 1.3
    ) -> List[Dict]:
        """
        Get similar articles using embedding-based similarity with hybrid scoring.
        
        Args:
            article_id: ID of source article
            top_n: Number of recommendations to return
            hybrid_weight: Weight for content similarity (1-weight = popularity weight)
            category_boost: Multiplier for same-category articles
            
        Returns:
            List of recommended articles with scores
        """
        if self.embedding_matrix is None:
            raise ValueError("Build embedding matrix first using build_embedding_matrix()")
        
        # Find article index
        try:
            article_idx = self.articles_df[self.articles_df['id'] == article_id].index[0]
        except IndexError:
            return []
        
        # Get source article embedding
        source_embedding = self.embedding_matrix[article_idx].reshape(1, -1)
        
        # Calculate cosine similarity with all articles
        similarities = cosine_similarity(source_embedding, self.embedding_matrix)[0]
        
        # Get source article category
        source_category = self.articles_df.iloc[article_idx]['category']
        
        # Apply category boost
        for idx, row in self.articles_df.iterrows():
            if row['category'] == source_category and idx != article_idx:
                similarities[idx] *= category_boost
        
        # Calculate popularity scores if not cached
        if not self.popularity_scores:
            self.calculate_popularity_scores()
        
        # Hybrid scoring: content + popularity
        hybrid_scores = []
        seen_ids = {article_id}  # Don't recommend the same article
        
        for idx, row in self.articles_df.iterrows():
            if row['id'] in seen_ids:
                continue
            
            content_sim = similarities[idx]
            popularity = self.popularity_scores.get(row['id'], 0.0)
            
            # Hybrid score
            final_score = (hybrid_weight * content_sim) + ((1 - hybrid_weight) * popularity)
            
            hybrid_scores.append({
                'idx': idx,
                'article_id': row['id'],
                'score': final_score,
                'content_similarity': content_sim,
                'popularity': popularity
            })
        
        # Sort by hybrid score
        hybrid_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Build recommendations
        recommendations = []
        for item in hybrid_scores[:top_n]:
            article = self.articles_df.iloc[item['idx']]
            recommendations.append({
                'id': int(article['id']),
                'title': article['title'],
                'category': article['category'],
                'source': article['source'],
                'similarity': float(item['score']),
                'content_similarity': float(item['content_similarity']),
                'popularity_score': float(item['popularity'])
            })
        
        return recommendations


    def get_article_by_id(self, article_id: int) -> Dict:
        """
        Get article details by ID.
        
        Args:
            article_id: Article ID
        
        Returns:
            Dictionary with article details or empty dict if not found
        """
        if self.articles_df is None:
            self.articles_df = self.load_articles()
        
        article = self.articles_df[self.articles_df['id'] == article_id]
        
        if article.empty:
            return {}
        
        row = article.iloc[0]
        return {
            'id': int(row['id']),
            'title': row['title'],
            'content': row.get('content', '')[:200] + '...' if row.get('content') and len(row['content']) > 200 else row.get('content', ''),
            'category': row['category'],
            'source': row['source'],
            'published_at': row['published_at']
        }


def test_recommender():
    """Test the embedding-based recommender"""
    print("🧪 Testing Embedding-based Recommender")
    
    recommender = NewsRecommender()
    
    # Load articles
    articles_df = recommender.load_articles()
    print(f"Loaded {len(articles_df)} articles")
    
    # Build embedding matrix
    recommender.build_embedding_matrix()
    
    # Test recommendation
    if not articles_df.empty:
        test_id = articles_df.iloc[0]['id']
        test_title = articles_df.iloc[0]['title']
        
        print(f"\n📰 Source: {test_title}")
        
        recommendations = recommender.get_similar_articles(test_id, top_n=5)
        
        print(f"\n🎯 Top 5 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. [{rec['category']}] {rec['title'][:60]}...")
            print(f"   Hybrid: {rec['similarity']:.3f} = Content: {rec['content_similarity']:.3f} + Popularity: {rec['popularity_score']:.3f}")


if __name__ == "__main__":
    test_recommender()

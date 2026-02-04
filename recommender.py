"""
TF-IDF based content recommendation engine for news articles.

Uses scikit-learn's TfidfVectorizer to compute article similarity
and recommend related content based on cosine similarity.
"""

import psycopg
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple


class NewsRecommender:
    """Content-based recommendation engine using TF-IDF"""
    
    def __init__(self, conn_string: str = "postgresql://admin:admin123@postgres:5432/newsdb"):
        """
        Initialize recommender with database connection.
        
        Args:
            conn_string: PostgreSQL connection string
        """
        self.conn_string = conn_string
        self.vectorizer = None
        self.tfidf_matrix = None
        self.articles_df = None
        self.popularity_scores = {}  # Cache for popularity scores
        
    def load_articles(self) -> pd.DataFrame:
        """
        Load articles from database into pandas DataFrame.
        
        Returns:
            DataFrame with article data
        """
        conn = psycopg.connect(self.conn_string)
        
        query = """
        SELECT id, title, content, category, source, published_at
        FROM articles
        WHERE content IS NOT NULL AND content != ''
        ORDER BY id
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            data = cur.fetchall()
        
        conn.close()
        
        df = pd.DataFrame(data, columns=columns)
        print(f"✓ Loaded {len(df)} articles from database")
        
        return df
    
    def build_tfidf_matrix(self, max_features: int = 5000) -> None:
        """
        Build TF-IDF matrix from article content.
        
        Args:
            max_features: Maximum number of features (words) to consider
        """
        print("\nBuilding TF-IDF matrix...")
        
        # Load articles
        self.articles_df = self.load_articles()
        
        # Combine title and content (weight title more heavily)
        # Title is repeated 3x for more importance
        self.articles_df['combined_text'] = (
            (self.articles_df['title'].fillna('') + ' ') * 3 + 
            self.articles_df['content'].fillna('')
        )
        
        # Initialize TF-IDF vectorizer with optimized parameters
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 3),  # unigrams, bigrams, and trigrams
            min_df=1,  # keep rare terms (small dataset)
            max_df=0.7,  # more aggressive common word filtering
            sublinear_tf=True  # use log scaling for term frequency
        )
        
        # Fit and transform
        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.articles_df['combined_text']
        )
        
        print(f"✓ TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        print(f"✓ Vocabulary size: {len(self.vectorizer.vocabulary_)}")
    
    def get_similar_articles(
        self, 
        article_id: int, 
        top_n: int = 5,
        min_similarity: float = 0.1
    ) -> List[Dict]:
        """
        Get similar articles based on content similarity.
        
        Args:
            article_id: ID of the article to find recommendations for
            top_n: Number of recommendations to return
            min_similarity: Minimum similarity threshold (0-1)
        
        Returns:
            List of dictionaries with recommended articles
        """
        if self.tfidf_matrix is None:
            raise ValueError("TF-IDF matrix not built. Call build_tfidf_matrix() first.")
        
        # Find article index
        try:
            article_idx = self.articles_df[self.articles_df['id'] == article_id].index[0]
        except IndexError:
            return []
        
        # Get source article category for boosting
        source_category = self.articles_df.iloc[article_idx]['category']
        
        # Compute cosine similarity
        article_vector = self.tfidf_matrix[article_idx]
        similarities = cosine_similarity(article_vector, self.tfidf_matrix)[0]
        
        # Boost same-category articles by 30%
        for idx, article in self.articles_df.iterrows():
            if article['category'] == source_category:
                similarities[idx] *= 1.3
        
        # Get top N similar articles (excluding the article itself)
        similar_indices = similarities.argsort()[::-1]
        
        # Filter by minimum similarity and remove duplicates
        recommendations = []
        seen_ids = set()  # Track article IDs to avoid duplicates
        
        for idx in similar_indices:
            # Skip self-match
            if idx == article_idx:
                continue
            
            similarity_score = similarities[idx]
            
            # Skip near-duplicates (>98% similarity)
            if similarity_score > 0.98:
                continue
            
            # Stop if below minimum threshold
            if similarity_score < min_similarity:
                break
            
            article = self.articles_df.iloc[idx]
            article_id_rec = int(article['id'])
            
            # Skip if we've already seen this article ID (duplicate database entries)
            if article_id_rec in seen_ids:
                continue
            
            seen_ids.add(article_id_rec)
            
            recommendations.append({
                'id': article_id_rec,
                'title': article['title'],
                'category': article['category'],
                'source': article['source'],
                'similarity': float(similarity_score),
                'published_at': article['published_at']
            })
            
            # Stop once we have enough recommendations
            if len(recommendations) >= top_n:
                break
        
        return recommendations
    
    def calculate_popularity_scores(self) -> Dict[int, float]:
        """
        Calculate popularity score for each article based on user interactions.
        
        Factors:
        - View count (40%)
        - Click count (30%)
        - Rating (30%)
        
        Returns:
            Dictionary mapping article_id to normalized popularity score (0-1)
        """
        conn = psycopg.connect(self.conn_string)
        
        # Get interaction stats per article
        query = """
        SELECT 
            article_id,
            COUNT(*) as total_interactions,
            SUM(CASE WHEN interaction_type = 'view' THEN 1 ELSE 0 END) as views,
            SUM(CASE WHEN interaction_type = 'click' THEN 1 ELSE 0 END) as clicks,
            MAX(created_at) as last_interaction,
            AVG(CASE WHEN rating IS NOT NULL THEN rating ELSE 3 END) as avg_rating
        FROM interactions
        GROUP BY article_id
        """
        
        with conn.cursor() as cur:
            cur.execute(query)
            interactions = cur.fetchall()
        
        conn.close()
        
        if not interactions:
            # Cold start: no interactions yet, return uniform scores
            return {int(article_id): 0.5 for article_id in self.articles_df['id']}
        
        # Calculate raw scores
        scores = {}
        max_views = max(row[2] for row in interactions) or 1
        max_clicks = max(row[3] for row in interactions) or 1
        
        for row in interactions:
            article_id = row[0]
            views = row[2]
            clicks = row[3]
            
            # Weighted score: views (40%) + clicks (30%) + rating (30%)
            view_score = views / max_views
            click_score = clicks / max_clicks
            rating_score = (row[5] - 1) / 4  # Normalize rating 1-5 to 0-1
            
            scores[article_id] = (
                0.4 * view_score +
                0.3 * click_score +
                0.3 * rating_score
            )
        
        # Fill in articles with no interactions
        for article_id in self.articles_df['id']:
            if int(article_id) not in scores:
                scores[int(article_id)] = 0.1  # Small baseline for cold articles
        
        # Cache scores
        self.popularity_scores = scores
        
        return scores
    
    def get_hybrid_recommendations(
        self,
        article_id: int,
        top_n: int = 5,
        content_weight: float = 0.7,
        popularity_weight: float = 0.3,
        min_similarity: float = 0.1
    ) -> List[Dict]:
        """
        Get hybrid recommendations combining content similarity and popularity.
        
        Args:
            article_id: ID of the article to find recommendations for
            top_n: Number of recommendations to return
            content_weight: Weight for content-based similarity (default 0.7)
            popularity_weight: Weight for popularity score (default 0.3)
            min_similarity: Minimum content similarity threshold
        
        Returns:
            List of dictionaries with recommended articles and hybrid scores
        """
        # Get content-based recommendations (more than needed)
        content_recs = self.get_similar_articles(
            article_id, 
            top_n=top_n * 3,  # Get extra candidates
            min_similarity=min_similarity
        )
        
        if not content_recs:
            return []
        
        # Calculate popularity scores if not cached
        if not self.popularity_scores:
            self.calculate_popularity_scores()
        
        # Normalize content similarity scores (0-1)
        max_similarity = max(rec['similarity'] for rec in content_recs)
        
        # Calculate hybrid scores
        for rec in content_recs:
            article_id_rec = rec['id']
            
            # Normalize content score
            content_score = rec['similarity'] / max_similarity if max_similarity > 0 else 0
            
            # Get popularity score (default to 0.1 if not found - cold start)
            popularity_score = self.popularity_scores.get(article_id_rec, 0.1)
            
            # Hybrid score
            hybrid_score = (
                content_weight * content_score +
                popularity_weight * popularity_score
            )
            
            rec['hybrid_score'] = float(hybrid_score)
            rec['popularity_score'] = float(popularity_score)
        
        # Sort by hybrid score
        content_recs.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return content_recs[:top_n]
    
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
            'content': row['content'][:200] + '...' if len(row['content']) > 200 else row['content'],
            'category': row['category'],
            'source': row['source'],
            'published_at': row['published_at']
        }
    
    def get_recommendations_by_category(
        self, 
        category: str, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top articles from a specific category.
        
        Args:
            category: Category name
            limit: Number of articles to return
        
        Returns:
            List of article dictionaries
        """
        if self.articles_df is None:
            self.articles_df = self.load_articles()
        
        category_articles = self.articles_df[
            self.articles_df['category'] == category
        ].head(limit)
        
        return [
            {
                'id': int(row['id']),
                'title': row['title'],
                'category': row['category'],
                'source': row['source'],
                'published_at': row['published_at']
            }
            for _, row in category_articles.iterrows()
        ]


def test_recommender():
    """Test the recommendation engine"""
    print("=" * 70)
    print("Testing News Recommendation Engine")
    print("=" * 70)
    
    # Initialize recommender
    recommender = NewsRecommender()
    
    # Build TF-IDF matrix
    recommender.build_tfidf_matrix()
    
    # Get a sample article
    sample_article_id = recommender.articles_df.iloc[0]['id']
    sample_article = recommender.get_article_by_id(sample_article_id)
    
    print("\n" + "=" * 70)
    print("Sample Article:")
    print("=" * 70)
    print(f"ID: {sample_article['id']}")
    print(f"Title: {sample_article['title']}")
    print(f"Category: {sample_article['category']}")
    print(f"Source: {sample_article['source']}")
    
    # Get recommendations
    recommendations = recommender.get_similar_articles(sample_article_id, top_n=5)
    
    print("\n" + "=" * 70)
    print(f"Top 5 Similar Articles:")
    print("=" * 70)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['title']}")
        print(f"   Category: {rec['category']} | Source: {rec['source']}")
        print(f"   Similarity: {rec['similarity']:.3f}")
    
    print("\n" + "=" * 70)
    print("✓ Recommendation engine working successfully!")
    print("=" * 70)


if __name__ == "__main__":
    test_recommender()

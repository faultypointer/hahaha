from dataclasses import dataclass
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dataclasses import asdict

@dataclass
class Video:
    title: str
    description: str
    category: str

class VideoRecommender:
    def __init__(self, title_weight=0.4, description_weight=0.2, category_weight=0.4):
        """Initialize recommendation system with feature weights."""
        self.title_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=5000
        )
        
        self.description_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),
            max_features=10000,
            max_df=0.7
        )
        
        self.category_vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 1)
        )
        
        self.videos: List[Video] = []
        self.title_vectors = None
        self.description_vectors = None
        self.category_vectors = None
        self.weights = {
            'title': title_weight,
            'description': description_weight,
            'category': category_weight
        }
    
    def preprocess_text(self, text: str) -> str:
        """Clean and standardize text."""
        return text.lower().strip()
    
    def fit(self, videos: List[Video]):
        """Fit the recommender with video data."""
        self.videos = videos
        titles = [self.preprocess_text(video.title) for video in videos]
        descriptions = [self.preprocess_text(video.description) for video in videos]
        categories = [self.preprocess_text(video.category) for video in videos]
        
        self.title_vectors = self.title_vectorizer.fit_transform(titles)
        self.description_vectors = self.description_vectorizer.fit_transform(descriptions)
        self.category_vectors = self.category_vectorizer.fit_transform(categories)
    
    def get_recommendations(self, current_video: Video, num_recommendations: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on current video."""
        current_title_vector = self.title_vectorizer.transform([self.preprocess_text(current_video.title)])
        current_desc_vector = self.description_vectorizer.transform([self.preprocess_text(current_video.description)])
        current_category_vector = self.category_vectorizer.transform([self.preprocess_text(current_video.category)])
        
        title_similarities = cosine_similarity(current_title_vector, self.title_vectors).flatten()
        desc_similarities = cosine_similarity(current_desc_vector, self.description_vectors).flatten()
        category_similarities = cosine_similarity(current_category_vector, self.category_vectors).flatten()
        
        combined_similarities = (
            self.weights['title'] * title_similarities +
            self.weights['description'] * desc_similarities +
            self.weights['category'] * category_similarities
        )
        
        similar_indices = combined_similarities.argsort()[::-1]
        recommendations = []
        
        for idx in similar_indices:
            candidate_video = self.videos[idx]
            if (candidate_video.title.lower() == current_video.title.lower() and 
                candidate_video.category.lower() == current_video.category.lower()):
                continue
            
            recommendations.append({
                'video': asdict(candidate_video),
                'similarity_score': round(combined_similarities[idx] * 100, 2)
            })
            
            if len(recommendations) >= num_recommendations:
                break
                
        return recommendations

    def add_videos(self, new_videos: List[Video]):
        """Add new videos and refit the recommender."""
        self.videos.extend(new_videos)
        self.fit(self.videos)

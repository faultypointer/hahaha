from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Video:
    """Class to store video information."""
    title: str
    description: str
    category: str
    
class EnhancedVideoRecommender:
    def __init__(self, title_weight=0.4, description_weight=0.4, category_weight=0.2):
        """
        Initialize the enhanced video recommender with separate vectorizers for each feature.
        
        Args:
            title_weight (float): Weight for title similarity (default: 0.4)
            description_weight (float): Weight for description similarity (default: 0.4)
            category_weight (float): Weight for category similarity (default: 0.2)
        """
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
            max_df=0.7  # Ignore terms that appear in more than 70% of descriptions
        )
        
        self.category_vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 1)  # Only unigrams for categories
        )
        
        self.videos: List[Video] = []
        self.title_vectors = None
        self.description_vectors = None
        self.category_vectors = None
        
        # Weights for different features
        self.weights = {
            'title': title_weight,
            'description': description_weight,
            'category': category_weight
        }
        
    def preprocess_text(self, text: str) -> str:
        """Clean and standardize text."""
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        # Remove excessive whitespace
        text = ' '.join(text.split())
        return text
        
    def fit(self, videos: List[Video]):
        """
        Fit the recommender with available videos.
        
        Args:
            videos (List[Video]): List of Video objects containing title, description, and category
        """
        self.videos = videos
        
        # Extract and preprocess features
        titles = [self.preprocess_text(video.title) for video in videos]
        descriptions = [self.preprocess_text(video.description) for video in videos]
        categories = [self.preprocess_text(video.category) for video in videos]
        
        # Fit and transform each feature
        self.title_vectors = self.title_vectorizer.fit_transform(titles)
        self.description_vectors = self.description_vectorizer.fit_transform(descriptions)
        self.category_vectors = self.category_vectorizer.fit_transform(categories)
    
    def get_recommendations(self, 
                          current_video: Video, 
                          num_recommendations: int = 5,
                          category_filter: Optional[str] = None) -> List[Tuple[Video, float]]:
        """
        Get video recommendations based on current video.
        
        Args:
            current_video (Video): Current video object
            num_recommendations (int): Number of recommendations to return
            category_filter (str, optional): Filter recommendations by category
            
        Returns:
            List[Tuple[Video, float]]: List of (Video, similarity_score) tuples
        """
        # Transform current video features
        current_title_vector = self.title_vectorizer.transform([self.preprocess_text(current_video.title)])
        current_desc_vector = self.description_vectorizer.transform([self.preprocess_text(current_video.description)])
        current_category_vector = self.category_vectorizer.transform([self.preprocess_text(current_video.category)])
        
        # Calculate similarity scores for each feature
        title_similarities = cosine_similarity(current_title_vector, self.title_vectors).flatten()
        desc_similarities = cosine_similarity(current_desc_vector, self.description_vectors).flatten()
        category_similarities = cosine_similarity(current_category_vector, self.category_vectors).flatten()
        
        # Calculate weighted combined similarity
        combined_similarities = (
            self.weights['title'] * title_similarities +
            self.weights['description'] * desc_similarities +
            self.weights['category'] * category_similarities
        )
        
        # Get indices of top similar videos
        similar_indices = combined_similarities.argsort()[::-1]
        
        # Filter and format recommendations
        recommendations = []
        for idx in similar_indices:
            candidate_video = self.videos[idx]
            
            # Skip if it's the current video
            if (candidate_video.title.lower() == current_video.title.lower() and 
                candidate_video.category.lower() == current_video.category.lower()):
                continue
                
            # Apply category filter if specified
            if category_filter and candidate_video.category.lower() != category_filter.lower():
                continue
            
            similarity_score = round(combined_similarities[idx] * 100, 2)
            recommendations.append((candidate_video, similarity_score))
            
            if len(recommendations) >= num_recommendations:
                break
                
        return recommendations

    def add_new_videos(self, new_videos: List[Video]):
        """
        Update the recommender with new videos.
        
        Args:
            new_videos (List[Video]): List of new Video objects to add
        """
        self.videos.extend(new_videos)
        self.fit(self.videos)  # Refit the vectorizers with all videos

def format_recommendations(recommendations: List[Tuple[Video, float]]) -> str:
    """Format recommendations for display."""
    result = "Recommended Videos:\n"
    for i, (video, score) in enumerate(recommendations, 1):
        result += (f"{i}. {video.title}\n"
                  f"   Category: {video.category}\n"
                  f"   Relevance: {score}%\n"
                  f"   Description: {video.description[:100]}...\n\n")
    return result

# Example usage
if __name__ == "__main__":
    # Sample video data
    sample_videos = [
        Video(
            title="Introduction to Python Programming",
            description="Learn the basics of Python programming language. Covers variables, data types, control structures, and functions.",
            category="Programming Basics"
        ),
        Video(
            title="Advanced Python: Object-Oriented Programming",
            description="Master object-oriented programming concepts in Python. Learn about classes, inheritance, and polymorphism.",
            category="Programming Advanced"
        ),
        Video(
            title="Data Structures in Python",
            description="Comprehensive guide to implementing and using data structures in Python. Covers lists, dictionaries, sets, and more.",
            category="Programming Advanced"
        ),
        Video(
            title="Machine Learning Fundamentals",
            description="Introduction to machine learning concepts and algorithms using Python and scikit-learn.",
            category="Data Science"
        ),
        Video(
            title="Python for Data Analysis",
            description="Learn data analysis using Python libraries like Pandas and NumPy. Includes data cleaning and visualization.",
            category="Data Science"
        )
    ]
    
    # Initialize and fit the recommender
    recommender = EnhancedVideoRecommender()
    recommender.fit(sample_videos)
    
    # Example current video
    current_video = Video(
        title="Python Programming Basics",
        description="Introduction to programming concepts using Python. Learn about variables and basic syntax.",
        category="Programming Basics"
    )
    
    # Get recommendations
    recommendations = recommender.get_recommendations(current_video)
    
    # Print formatted recommendations
    print(f"Current Video: {current_video.title}")
    print(f"Category: {current_video.category}")
    print(format_recommendations(recommendations))

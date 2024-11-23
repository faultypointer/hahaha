from flask import Flask, request, jsonify
from recom import Video, VideoRecommender

# Initialize Flask app
app = Flask(__name__)

# Initialize recommender system
recommender = VideoRecommender()

# Sample videos database (replace with your actual database)
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

# Fit the recommender with sample videos on startup
recommender.fit(sample_videos)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get video recommendations based on current video."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'description', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Create Video object from request data
        current_video = Video(
            title=data['title'],
            description=data['description'],
            category=data['category']
        )
        
        # Get number of recommendations (optional)
        num_recommendations = data.get('num_recommendations', 5)
        
        # Get recommendations
        recommendations = recommender.get_recommendations(
            current_video,
            num_recommendations=num_recommendations
        )
        
        return jsonify({
            'status': 'success',
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error processing request: {str(e)}'
        }), 500

@app.route('/videos', methods=['POST'])
def add_videos():
    """Add new videos to the recommendation system."""
    try:
        data = request.get_json()
        
        if 'videos' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing videos array in request'
            }), 400
            
        new_videos = [
            Video(
                title=video['title'],
                description=video['description'],
                category=video['category']
            )
            for video in data['videos']
        ]
        
        # Add new videos and refit recommender
        recommender.add_videos(new_videos)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully added {len(new_videos)} videos',
            'total_videos': len(recommender.videos)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding videos: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

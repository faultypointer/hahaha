import os
import json
import uuid
from flask import Flask, request, jsonify, send_from_directory
from recom import Video, VideoRecommender
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize recommender system
recommender = VideoRecommender()

# Fit the recommender with sample videos on startup
# recommender.fit(sample_videos)

@app.route('/recom/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'})

@app.route('/recom/recommendations', methods=['POST'])
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

@app.route('/recom/videos', methods=['POST'])
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



# Directory to store uploaded videos
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# File to store metadata
METADATA_FILE = 'video_metadata.json'
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w') as f:
        json.dump([], f)

# API to upload videos
@app.route('/upload', methods=['POST'])
def upload_video():
    # Check for file in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Extract metadata
    title = request.form.get('title')
    category = request.form.get('category')
    description = request.form.get('description')

    if not title or not category or not description:
        return jsonify({'error': 'Missing metadata (title, category, description)'}), 400

    # Save file
    filename, file_extension = os.path.splitext(file.filename)
    randomized_filename = f"{filename}_{uuid.uuid4().hex[:8]}{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], randomized_filename)
    file.save(file_path)
    # Save metadata
    with open(METADATA_FILE, 'r+') as f:
        metadata = json.load(f)
        metadata.append({
            'title': title,
            'category': category,
            'description': description,
            'filename': randomized_filename
        })
        f.seek(0)
        json.dump(metadata, f, indent=4)

    return jsonify({'message': 'File uploaded successfully'}), 201

# API to list all videos
@app.route('/videos', methods=['GET'])
def list_videos():
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    return jsonify({'videos': metadata})

# API to retrieve a specific video by filename
@app.route('/videos/<filename>', methods=['GET'])
def get_video(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404


import google.generativeai as genai
gemini_key = 'AIzaSyBR49Xn825p4oBFLYPj2Kz95CzgETn9W7c'
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')
PRE_PROMPT = """
You are acting as a chatbot for an Education website that helps students prepare
for competitive exams. These are courses available on the sites:

There are mock test the students can take. There are also analytical dashboard that shows
the students their performances. Answer the follwoing questions or engage in conversations 

the prompt will also contains past messages between you and students. Use that to give more
appropriate answers. The message starring with `student: <<` and ending with `>>` is the query
by student and between `gemini: <<` and `>>` is by you. When answering you don't need to do it
between `gemini: <<` and `>>`

"""

@app.route('/chatbot', methods=['POST'])
def chatbot():
    prompt_data = request.get_json();
    history = prompt_data['history']
    prompt = ""
    if history == "":
        history = PRE_PROMPT
    history += "student: <<" + prompt_data['prompt'] + ">>\n"
    response = model.generate_content(history)
    history += "gemini: <<" + response.text
    return jsonify({'response': response.text, 'history': history})



if __name__ == '__main__':
    app.run(debug=True, host="")

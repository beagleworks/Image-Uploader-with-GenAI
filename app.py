from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import sqlite3
import requests
from PIL import Image
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
import uuid
from dotenv import load_dotenv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['GENERATED_FOLDER'] = os.path.join(os.getcwd(), 'generated')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Load environment variables from .env file
load_dotenv()

# OpenRouter API key (loaded from .env file)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY, filename TEXT, comment TEXT)''')
    
    # Check if generated_image_filename column exists, if not add it
    c.execute("PRAGMA table_info(images)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'generated_image_filename' not in columns:
        c.execute("ALTER TABLE images ADD COLUMN generated_image_filename TEXT")
        print("Added generated_image_filename column to existing database")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    file = request.files['image']
    comment = request.form.get('comment', '')
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        print(f"Saving file to: {file_path}")
        file.save(file_path)
        print(f"File saved successfully: {os.path.exists(file_path)}")
        
        # Save to database
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO images (filename, comment) VALUES (?, ?)", (filename, comment))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Upload successful', 'filename': filename}), 200
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    filename = data.get('filename')
    comment = data.get('comment')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Create prompt for Gemini 2.5 Flash Image (Nano Banana)
    prompt = f"Based on this image and comment: '{comment}'"
    try:
        # Encode image to base64
        image_base64 = encode_image(file_path)
        
        # Use OpenRouter API for Gemini 2.5 Flash Image (Nano Banana)
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        qjson = {
            "model": "google/gemini-2.5-flash-image-preview:free",
            "messages": [
                # {
                #     "role": "system",
                #     "content": system_prompt
                # },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            # "temperature": temperature,
            "modalities": ["image", "text"]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers = headers,
            json = qjson
        )
        

        if response.status_code != 200:
            return jsonify({'error': f'OpenRouter API error: {response.text}'}), 500
        
        response_data = response.json()

        # Extract generated content
        if 'choices' not in response_data or not response_data['choices']:
            return jsonify({'error': 'No response from model'}), 500
        
        content = response_data['choices'][0]['message']['images'][0]['image_url']['url']
        
        # Assuming the model returns an image description or base64 image
        # For now, since Gemini may not generate images, we'll handle text response
        # If it's base64, decode it; otherwise, treat as text
        
        if content.startswith('data:image'):
            # Extract base64 data
            header, encoded = content.split(',', 1)
            generated_image_data = base64.b64decode(encoded)
        else:
            # If no image, return error or handle differently
            return jsonify({'error': 'Model did not generate an image'}), 500
        
        # Save generated image
        generated_filename = f"generated_{uuid.uuid4().hex}.png"
        generated_path = os.path.join(app.config['GENERATED_FOLDER'], generated_filename)
        os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)
        
        generated_image = Image.open(BytesIO(generated_image_data))
        generated_image.save(generated_path)
        
        # Update database with generated image filename
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE images SET generated_image_filename = ? WHERE filename = ?", (generated_filename, filename))
        conn.commit()
        conn.close()
        
        return jsonify({
            'generated_image': generated_filename,
            'message': 'OpenRouter Gemini 2.5 Flash Image (Nano Banana) generation completed.'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images')
def get_images():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT filename, comment, generated_image_filename FROM images")
    images = c.fetchall()
    conn.close()
    return jsonify([{'filename': img[0], 'comment': img[1], 'generated_image': img[2]} for img in images])

@app.route('/edit_comment/<filename>', methods=['PUT'])
def edit_comment(filename):
    data = request.json
    new_comment = data.get('comment', '')
    
    if not new_comment:
        return jsonify({'error': 'Comment is required'}), 400
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE images SET comment = ? WHERE filename = ?", (new_comment, filename))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Comment updated successfully'}), 200

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    # Get generated image filename before deleting from database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT generated_image_filename FROM images WHERE filename = ?", (filename,))
    result = c.fetchone()
    generated_filename = result[0] if result else None
    
    # Delete from database
    c.execute("DELETE FROM images WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    
    # Delete original image from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete generated image from filesystem
    if generated_filename:
        generated_path = os.path.join(app.config['GENERATED_FOLDER'], generated_filename)
        if os.path.exists(generated_path):
            os.remove(generated_path)
    
    return jsonify({'message': 'Image deleted successfully'}), 200

@app.route('/reset', methods=['POST'])
def reset_database():
    try:
        # Close any existing connections
        conn = sqlite3.connect('database.db')
        conn.close()
        
        # Remove database file
        if os.path.exists('database.db'):
            os.remove('database.db')
        
        # Remove all uploaded files
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # Remove all generated files
        if os.path.exists(app.config['GENERATED_FOLDER']):
            for filename in os.listdir(app.config['GENERATED_FOLDER']):
                file_path = os.path.join(app.config['GENERATED_FOLDER'], filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        # Recreate database and table
        init_db()
        
        return jsonify({'message': 'Database and files reset successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generated/<filename>')
def generated_file(filename):
    file_path = os.path.join(app.config['GENERATED_FOLDER'], filename)
    print(f"Serving generated file: {file_path}, exists: {os.path.exists(file_path)}")
    if not os.path.exists(file_path):
        return jsonify({'error': 'Generated file not found'}), 404
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"Serving uploaded file: {file_path}, exists: {os.path.exists(file_path)}")
    if not os.path.exists(file_path):
        return jsonify({'error': 'Uploaded file not found'}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import sqlite3
import google.genai as genai
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

# Google AI API key (loaded from .env file)
client = genai.Client(api_key=os.getenv('GOOGLE_AI_API_KEY'))

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY, filename TEXT, comment TEXT, generated_image_filename TEXT)''')
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
    
    # Read image file
    with open(file_path, 'rb') as f:
        image_data = f.read()
    
    # Create prompt for Gemini 2.5 Flash Image
    prompt = f"Based on this image and comment: '{comment}', create a creative AI-generated image that captures the essence and enhances the visual appeal."
    
    try:
        # Use Gemini 2.5 Flash Image for image generation
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt, Image.open(file_path)],
        )
        
        # Extract generated image
        generated_image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                generated_image_data = part.inline_data.data
                break
        
        if generated_image_data is None:
            return jsonify({'error': 'No image generated'}), 500
        
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
            'message': 'Gemini 2.5 Flash Image generation completed.'
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    app.run(debug=True)

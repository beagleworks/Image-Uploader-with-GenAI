from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import sqlite3
import google.generativeai as genai
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Google AI API key (set as environment variable)
genai.configure(api_key=os.getenv('GOOGLE_AI_API_KEY'))

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images
                 (id INTEGER PRIMARY KEY, filename TEXT, comment TEXT, gemini_analysis TEXT)''')
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
    
    # Create prompt for Gemini
    prompt = f"Based on this image and comment: '{comment}', describe what a creative AI-generated image should look like. Provide a detailed prompt for image generation."
    
    try:
        # Use Gemini 1.5 Pro for image analysis
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Create image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_data).decode('utf-8')
        }
        
        response = model.generate_content([prompt, image_part])
        analysis_result = response.text
        
        # For now, return the analysis result as text
        # In a full implementation, you would use this analysis to generate an actual image
        
        # Update database with analysis result
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE images SET gemini_analysis = ? WHERE filename = ?", (analysis_result, filename))
        conn.commit()
        conn.close()
        
        return jsonify({
            'analysis': analysis_result,
            'message': 'Gemini Nano analysis completed.'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images')
def get_images():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT filename, comment, gemini_analysis FROM images")
    images = c.fetchall()
    conn.close()
    return jsonify([{'filename': img[0], 'comment': img[1], 'ai_generated_image': img[2]} for img in images])

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_image(filename):
    # Delete from database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM images WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    
    # Delete original image from filesystem
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
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
        
        # Recreate database and table
        init_db()
        
        return jsonify({'message': 'Database and files reset successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"Serving file: {file_path}, exists: {os.path.exists(file_path)}")
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    app.run(debug=True)

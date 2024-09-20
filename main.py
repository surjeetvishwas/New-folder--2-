from flask import Flask, request, render_template, redirect, url_for, flash
from google.cloud import storage
from google.cloud import aiplatform_v1
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'AIzaSyB5IEkAQUC4TVljPiuTz5_lPe-dPQJlkUg'  # Required for flashing messages

# Set Google Cloud Storage bucket name
bucket_name = 'image-upload-app'

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

# Limit file size to 10MB
MAX_CONTENT_LENGTH = 10 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_caption_and_description(image_file_path):
    """
    Calls Google's multi-modal API to generate a caption and description for the image.
    """
    client = aiplatform_v1.PredictionServiceClient()
    endpoint = 'projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/publishers/google/models/multimodal'  # Update your project info
    instance = {"image": {"image_bytes": open(image_file_path, "rb").read()}}
    parameters = {}
    
    response = client.predict(endpoint=endpoint, instances=[instance], parameters=parameters)
    return response.predictions[0]["caption"], response.predictions[0]["description"]

@app.route('/')
def index():
    # Load the color background based on load balancer (blue/green deployment)
    background_color = request.args.get('color', 'blue')  # Load balancer decides split (Project III)
    return render_template('index.html', background_color=background_color)

@app.route('/upload', methods=['POST'])
def upload():
    # Check if the request has a file
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    # Check if the file is selected and has the allowed type
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_path = os.path.join('/tmp', filename)  # Temporarily store the image
        file.save(image_path)

        blob = bucket.blob(filename)
        try:
            # Upload file to Google Cloud Storage
            blob.upload_from_filename(image_path)

            # Generate caption and description
            caption, description = generate_caption_and_description(image_path)

            # Save the description as a .txt file in the same bucket
            text_filename = filename.rsplit('.', 1)[0] + '.txt'
            text_blob = bucket.blob(text_filename)
            text_blob.upload_from_string(f"Caption: {caption}\nDescription: {description}")

            flash('File and caption uploaded successfully!')
        except Exception as e:
            flash(f'An error occurred: {e}')
        finally:
            # Clean up the temp file
            os.remove(image_path)

        return redirect(url_for('index'))
    else:
        flash('Invalid file type! Only images are allowed.')
        return redirect(request.url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

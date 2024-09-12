from flask import Flask, request, render_template
from google.cloud import storage
import os

app = Flask(__name__)

# Set Google Cloud Storage bucket name
bucket_name = 'your-bucket-name'

# Initialize Google Cloud Storage client
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        blob = bucket.blob(file.filename)
        blob.upload_from_file(file)
        return 'File uploaded successfully!'
    return 'No file uploaded!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

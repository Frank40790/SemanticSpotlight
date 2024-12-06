from flask import Flask, render_template, request, redirect, url_for
from markupsafe import Markup
from werkzeug.utils import secure_filename
from embedding_search import *
import os

app = Flask(__name__)

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the uploaded file
            query = request.form['query']
            n = int(request.form['n'])
            use_highlight = request.form.get('use_highlight')  # Check if run_highlight should be used

            if use_highlight:  # If run_highlight is selected
                confidence = float(request.form['confidence'])
                run_highlight(filename, query, confidence)
                # Read the generated HTML file
                with open(f'html_storages/{filename}.html', 'r') as f:
                    result_html = f.read()
                return render_template('index.html', result_html=Markup(result_html))

            else:
                # Call the function to compute relevant sentences
                relevant_sentences = run_get_relevant(filename, query, n)
                return render_template('index.html', sentences=relevant_sentences)

    return render_template('index.html')

if __name__ == '__main__':
    # Create directories if they don't exist
    directories = ["databases", "templates", "html_storages", "uploads"]
    for directory in directories:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                pass

    app.run(debug=True, port=3000)

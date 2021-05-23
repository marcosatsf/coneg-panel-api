import os
from os.path import supports_unicode_filenames
import zipfile
from flask import Flask, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin

#UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
UPLOAD_FOLDER = './uploaded_files'
ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def first_endpoint():
    return ("Tudo OK!", 200)

@app.route("/second_end/<int:valor>")
def second_endpoint(valor):
    return (f"Valor digitado: {valor}", 200)

@app.route('/upload', methods=['POST'])
@cross_origin(origin='*')
def upload_file():
    print(request.files)
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        # zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
        # zip_ref.extractall(UPLOAD_FOLDER)
        # zip_ref.close()
        return redirect(url_for('upload_file',
                                filename=filename))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
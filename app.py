from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
import docx
import re

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
MODIFIED_FOLDER = "modified"
ALLOWED_EXTENSIONS = {"docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MODIFIED_FOLDER"] = MODIFIED_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(MODIFIED_FOLDER):
    os.makedirs(MODIFIED_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_placeholders(doc_path):
    """Extracts placeholders in the order they appear in the document."""
    doc = docx.Document(doc_path)
    pattern = r"\{\{(.*?)\}\}"
    placeholders = []
    seen = set()

    for para in doc.paragraphs:
        matches = re.findall(pattern, para.text)
        for match in matches:
            if match not in seen:
                placeholders.append(match)
                seen.add(match)

    return placeholders

def replace_placeholders(doc_path, replacements):
    """Replaces placeholders in a .docx file with user inputs."""
    doc = docx.Document(doc_path)

    for para in doc.paragraphs:
        for placeholder, value in replacements.items():
            para.text = para.text.replace(f"{{{{{placeholder}}}}}", value)

    modified_path = os.path.join(app.config["MODIFIED_FOLDER"], "modified.docx")
    doc.save(modified_path)
    return modified_path

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]

        if file.filename == "":
            return "No selected file"

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            placeholders = extract_placeholders(file_path)
            return render_template("form.html", placeholders=placeholders, file_name=filename)

    return render_template("upload.html")

@app.route("/fill_form", methods=["POST"])
def fill_form():
    filename = request.form.get("file_name")
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    replacements = {key: request.form[key] for key in request.form if key != "file_name"}

    modified_file = replace_placeholders(file_path, replacements)

    return send_file(modified_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

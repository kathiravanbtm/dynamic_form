from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import docx
import re
from docx import Document

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
MODIFIED_FOLDER = "modified"
ALLOWED_EXTENSIONS = {"docx"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MODIFIED_FOLDER"] = MODIFIED_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MODIFIED_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_placeholders(docx_path):
    """Extract placeholders and categorize them into single inputs, paragraphs, lists, and loops."""
    doc = Document(docx_path)

    single_inputs = set()
    paragraphs = set()
    lists = set()
    loops = {}

    # Regex patterns
    single_line_regex = r"{{\s*([\w\d_]+)\s*}}"  # Matches {{name}}
    paragraph_regex = r"{{\s*paragraph:([\w\d_]+)\s*}}"  # Matches {{paragraph:bio}}
    list_regex = r"{{\s*list:([\w\d_]+)\s*}}"  # Matches {{list:skills}}
    loop_start_regex = r"{loop:([\w\d_]+)}"  # Matches {loop:experiences}
    loop_end_regex = r"{endloop}"  # Matches {endloop}

    in_loop = False
    loop_name = None

    for para in doc.paragraphs:
        text = para.text.strip()

        match_loop_start = re.search(loop_start_regex, text)
        if match_loop_start:
            in_loop = True
            loop_name = match_loop_start.group(1)
            loops[loop_name] = set()
            continue

        if re.search(loop_end_regex, text):
            in_loop = False
            loop_name = None
            continue

        if in_loop and loop_name:
            fields = re.findall(single_line_regex, text) + re.findall(paragraph_regex, text)
            loops[loop_name].update(fields)
            continue

        matches_paragraph = re.findall(paragraph_regex, text)
        matches_list = re.findall(list_regex, text)
        matches_single = re.findall(single_line_regex, text)

        paragraphs.update(matches_paragraph)
        lists.update(matches_list)
        single_inputs.update(matches_single)

    return {
        "single": list(single_inputs),
        "paragraphs": list(paragraphs),
        "lists": list(lists),
        "loops": {key: list(value) for key, value in loops.items()},
    }


def replace_placeholders(doc_path, replacements):
    """Replaces placeholders, including single-line, paragraphs, lists, and loops, in a .docx file."""
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"File not found: {doc_path}")

    doc = docx.Document(doc_path)

    # Process paragraphs
    for para in doc.paragraphs:
        for placeholder, value in replacements.items():
            placeholder_tag = f"{{{{{placeholder}}}}}"
            paragraph_tag = f"{{{{paragraph:{placeholder}}}}}"
            list_tag = f"{{{{list:{placeholder}}}}}"

            if paragraph_tag in para.text:
                para.text = para.text.replace(paragraph_tag, str(value))
            elif list_tag in para.text:
                if isinstance(value, list):
                    formatted_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(value)])
                    para.text = para.text.replace(list_tag, formatted_list)
            elif placeholder_tag in para.text:
                para.text = para.text.replace(placeholder_tag, str(value))

    # Process looping sections
    for placeholder, values in replacements.items():
        if isinstance(values, list) and all(isinstance(item, dict) for item in values):  
            loop_start = f"{{loop:{placeholder}}}"
            loop_end = "{endloop}"

            start_idx, end_idx = None, None
            for i, para in enumerate(doc.paragraphs):
                if loop_start in para.text:
                    start_idx = i
                if loop_end in para.text:
                    end_idx = i
                    break

            if start_idx is not None and end_idx is not None:
                loop_template = [p.text for p in doc.paragraphs[start_idx + 1:end_idx]]
                new_content = []

                for entry in values:  
                    for template_line in loop_template:
                        new_line = template_line
                        for key, val in entry.items():
                            new_line = new_line.replace(f"{{{{{key}}}}}", str(val))
                        new_content.append(new_line)

                doc.paragraphs[start_idx].text = "\n".join(new_content)
                for i in range(end_idx, start_idx, -1):
                    doc.paragraphs.pop(i)

    # Ensure modified directory exists
    os.makedirs(MODIFIED_FOLDER, exist_ok=True)

    modified_path = os.path.join(MODIFIED_FOLDER, "modified.docx")
    doc.save(modified_path)
    return modified_path


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            return redirect(url_for("form", filename=filename))

    return render_template("upload.html")


@app.route("/form")
def form():
    filename = request.args.get("filename")
    if not filename:
        flash("No file selected")
        return redirect(url_for("index"))

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        flash("File not found")
        return redirect(url_for("index"))

    placeholders = extract_placeholders(file_path)
    print("checkingfilename", filename)
    return render_template("form.html", filename=filename, placeholders=placeholders)


@app.route("/fill_form", methods=["POST"])
def fill_form():
    print(request.form)
    filename = request.form.get("file_name")
    print("filename", filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)   
    print("hello. fjile path", file_path)
    if not os.path.exists(file_path):
        flash("File not found")
        return redirect(url_for("index"))

    replacements = {}
    
    for key, value in request.form.items():
        if key not in ["file_name"] and not key.endswith("[]"):
            replacements[key] = value

    for key in request.form:
        if key.endswith("[]"):
            replacements[key[:-2]] = request.form.getlist(key)

    loops_data = {}
    for key in request.form:
        if key.startswith("loop_"):
            loop_name = key[5:]
            loop_entries = request.form.getlist(key)
            loops_data[loop_name] = loop_entries

    replacements.update(loops_data)

    modified_file = replace_placeholders(file_path, replacements)

    return send_file(modified_file, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

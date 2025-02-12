import { TemplateHandler } from "https://cdn.jsdelivr.net/npm/easy-template-x/+esm";
document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("generateDocx").addEventListener("click", handleFormSubmit);
});

/**
 * Handles form submission and processes data into JSON format.
 */
function handleFormSubmit() {
    let formData = new FormData(document.getElementById("dynamicForm"));
    let jsonData = {};

    formData.forEach((value, key) => {
        let keyParts = key.split(/[\[\]]/).filter(Boolean); // Splitting for nested structures
        let ref = jsonData;

        keyParts.forEach((part, i) => {
            if (i === keyParts.length - 1) {
                if (Array.isArray(ref[part])) {
                    ref[part].push(value);
                } else if (ref[part]) {
                    ref[part] = [ref[part], value];
                } else {
                    ref[part] = value;
                }
            } else {
                if (!ref[part]) {
                    // If the next key is numeric, create an array; otherwise, create an object
                    ref[part] = /^\d+$/.test(keyParts[i + 1]) ? [] : {};
                }
                ref = ref[part];
            }
        });
    });

    // Convert objects into proper arrays where needed
    jsonData = forceArrayForLoops(jsonData);

    console.log("Generated JSON:", JSON.stringify(jsonData, null, 4)); // Debugging
    generateDocx(jsonData);
}

// ✅ Ensures all looped data is always an array, even with a single item
function forceArrayForLoops(data) {
    for (let key in data) {
        if (typeof data[key] === "object" && !Array.isArray(data[key])) {
            data[key] = [data[key]]; // Convert single objects to arrays
        }
    }
    return data;
}



/**
 * Converts structured list arrays into array of objects.
 */
function restructureNestedData(data) {
    Object.keys(data).forEach(key => {
        if (typeof data[key] === "object" && !Array.isArray(data[key])) {
            let keys = Object.keys(data[key]);
            if (keys.some(k => Array.isArray(data[key][k]))) {
                let length = data[key][keys[0]].length;
                data[key] = Array.from({ length }, (_, i) => {
                    let obj = {};
                    keys.forEach(k => {
                        obj[k] = data[key][k][i];
                    });
                    return obj;
                });
            }
        }
    });
    return data;
}

/**
 
 * Adds a repeated section dynamically.


/**
 * Fetches the uploaded DOCX template and processes it with `easy-template-x`.
 */
async function generateDocx(data) {
    const handler = new TemplateHandler();
    const fileName = document.getElementById("file_name").value; // Get uploaded file name
    const fileUrl = `/uploads/${fileName}`; // Construct the correct file URL
    
    console.log("Fetching template:", fileUrl);

    try {
        const response = await fetch("/uploads/sample_template.docx");
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    
        console.log("Template fetched successfully.");
        const templateFile = await response.blob();
        const doc = await handler.process(templateFile, data); // Process with JSON data

        // Trigger file download
        saveFile("FilledDocument.docx", doc);

    } catch (error) {
        console.error("Error fetching or processing document:", error);
        alert("Error processing the document. Check console for details.");
    }
}

/**
 * Saves and triggers download of processed DOCX file.
 */
function saveFile(filename, blob) {
    const blobUrl = URL.createObjectURL(blob);
    let link = document.createElement("a");
    link.download = filename;
    link.href = blobUrl;
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
        link.remove();
        window.URL.revokeObjectURL(blobUrl);
    }, 0);
}
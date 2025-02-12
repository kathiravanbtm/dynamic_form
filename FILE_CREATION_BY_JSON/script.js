    import { TemplateHandler } from "https://cdn.jsdelivr.net/npm/easy-template-x/+esm";

    document.addEventListener("DOMContentLoaded", function () {
        document.getElementById("generateDocx").addEventListener("click", generateDocx);
    });

    async function generateDocx() {
        const docxInput = document.getElementById("docxTemplate").files[0];
        const jsonInput = document.getElementById("jsonFile").files[0];
        const jsonTextArea = document.getElementById("jsonInput").value;

        if (!docxInput) {
            alert("Please upload a DOCX template.");
            return;
        }

        let jsonData;
        if (jsonInput) {
            jsonData = await readFileAsJSON(jsonInput);
        } else {
            try {
                jsonData = JSON.parse(jsonTextArea);
            } catch (error) {
                alert("Invalid JSON format.");
                return;
            }
        }   

        processTemplate(docxInput, jsonData);
    }

    async function readFileAsJSON(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(JSON.parse(reader.result));
            reader.onerror = reject;
            reader.readAsText(file);
        });
    }

    async function processTemplate(docxFile, jsonData) {
        const reader = new FileReader();
        reader.onload = async function (event) {
            try {
                const templateData = event.target.result;
                const handler = new TemplateHandler();
                const outputDoc = await handler.process(templateData, jsonData);

                const blob = new Blob([outputDoc], { type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document" });
                saveFile("ProcessedDocument.docx", blob);
            } catch (error) {
                console.error("Error processing document:", error);
                alert("Failed to process document.");
            }
        };
        reader.readAsArrayBuffer(docxFile);
    }

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

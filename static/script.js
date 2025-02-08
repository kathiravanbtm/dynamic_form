document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".add-item").forEach(button => {
        button.addEventListener("click", function () {
            let listId = this.getAttribute("data-list");
            let container = document.getElementById(listId);
            let inputCount = container.querySelectorAll("input").length + 1;

            let newInput = document.createElement("input");
            newInput.type = "text";
            newInput.name = listId + inputCount;
            newInput.required = true;

            let removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.textContent = "−";
            removeButton.classList.add("remove-item");
            removeButton.addEventListener("click", function () {
                container.removeChild(newInput);
                container.removeChild(removeButton);
            });

            container.appendChild(newInput);
            container.appendChild(removeButton);
        });
    });
});

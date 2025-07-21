var editor = ace.edit("editor");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/python");
editor.setOptions({
    fontSize: "14pt",
    showPrintMargin: false,
    wrap: true,
});

document.getElementById("run-button").addEventListener("click", function () {
    var code = editor.getSession().getValue();
    var inputs = document.getElementById("inputs").value;
    fetch("/execute", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ code: code, inputs: inputs }),
    })
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("output").innerText = data.output;
        })
        .catch((error) => {
            console.error("Error:", error);
            document.getElementById("output").innerText =
                "An error occurred while executing the code.";
        });
});

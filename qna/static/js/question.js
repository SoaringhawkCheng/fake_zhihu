var simplemde = new SimpleMDE({
    element: document.getElementById("answer-editor"),
    spellChecker: false,
    status: false,
    toolbar: ["bold", "italic", "|", "heading", "quote", 
    "code", "ordered-list", "unordered-list", "|", "image", 
    "preview"], 
    placeholder: '写回答…'
});
document.getElementById("answer-editor").value = simplemde.value();
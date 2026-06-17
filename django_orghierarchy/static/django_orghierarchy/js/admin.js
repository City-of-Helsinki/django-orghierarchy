document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".orghierarchy-indent[data-indent-level]").forEach(function (el) {
        const level = Number.parseInt(el.dataset.indentLevel, 10);
        const size = Number.parseInt(el.dataset.indentSize, 10) || 20;
        el.style.setProperty("--orghierarchy-indent", (level * size) + "px");
    });
});

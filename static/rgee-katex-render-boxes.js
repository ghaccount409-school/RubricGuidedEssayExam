/**
 * Render LaTeX delimiters in static prose boxes via KaTeX auto-render.
 * Mark containers with data-rgee-katex (server text in element body).
 */
(function () {
  "use strict";

  var KATEX_DELIMS = [
    { left: "$$", right: "$$", display: true },
    { left: "$", right: "$", display: false },
    { left: "\\(", right: "\\)", display: false },
    { left: "\\[", right: "\\]", display: true },
  ];

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function boot() {
    if (typeof renderMathInElement !== "function") return;
    var nodes = document.querySelectorAll("[data-rgee-katex]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var text = el.textContent;
      if (!text || !text.trim() || text.trim() === "—") continue;
      el.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
      try {
        renderMathInElement(el, {
          delimiters: KATEX_DELIMS,
          throwOnError: false,
          strict: false,
        });
      } catch (e) {}
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

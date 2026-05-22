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

  function isDollarEscaped(s, dollarIndex) {
    var bs = 0;
    for (var j = dollarIndex - 1; j >= 0 && s.charAt(j) === "\\"; j--) {
      bs++;
    }
    return bs % 2 === 1;
  }

  /** Keep in sync with static/rgee-math-panel.js */
  function normalizeNewlinesInsideMathDelimiters(s) {
    var src = String(s);
    src = src.replace(/\$\$([\s\S]*?)\$\$/g, function (_, inner) {
      return "$$" + inner.replace(/\r\n|\r|\n/g, " ") + "$$";
    });
    src = src.replace(/\\\[([\s\S]*?)\\\]/g, function (_, inner) {
      return "\\[" + inner.replace(/\r\n|\r|\n/g, " ") + "\\]";
    });
    src = src.replace(/\\\(([\s\S]*?)\\\)/g, function (_, inner) {
      return "\\(" + inner.replace(/\r\n|\r|\n/g, " ") + "\\)";
    });
    var out = "";
    var i = 0;
    var n = src.length;
    while (i < n) {
      var c = src.charAt(i);
      if (c !== "$") {
        out += c;
        i++;
        continue;
      }
      if (i + 1 < n && src.charAt(i + 1) === "$") {
        out += "$$";
        i += 2;
        continue;
      }
      if (isDollarEscaped(src, i)) {
        out += c;
        i++;
        continue;
      }
      var k = i + 1;
      while (k < n) {
        var d = src.charAt(k);
        if (d === "$" && (k + 1 >= n || src.charAt(k + 1) !== "$") && !isDollarEscaped(src, k)) {
          break;
        }
        k++;
      }
      if (k >= n) {
        out += src.slice(i);
        break;
      }
      var inner = src.slice(i + 1, k).replace(/\r\n|\r|\n/g, " ");
      out += "$" + inner + "$";
      i = k + 1;
    }
    return out;
  }

  function prepareMixedTextForKaTeXAutoRender(sourceText) {
    var normalized = normalizeNewlinesInsideMathDelimiters(sourceText || "");
    return escapeHtml(normalized).replace(/\r\n|\r|\n/g, "<br>");
  }

  function boot() {
    if (typeof renderMathInElement !== "function") return;
    var nodes = document.querySelectorAll("[data-rgee-katex]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var text = el.textContent;
      if (!text || !text.trim() || text.trim() === "—") continue;
      el.innerHTML = prepareMixedTextForKaTeXAutoRender(text);
      try {
        renderMathInElement(el, {
          delimiters: KATEX_DELIMS,
          throwOnError: false,
          strict: false,
          trust: false,
          ignoredTags: ["script", "noscript", "style", "textarea", "pre"],
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

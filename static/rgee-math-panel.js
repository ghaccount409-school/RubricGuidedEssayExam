/**
 * KaTeX formula builder: math tools + live KaTeX preview with LaTeX textarea overlay + slot templates.
 * Expects: katex.min.js, contrib/auto-render.min.js (global renderMathInElement).
 */
(function () {
  "use strict";

  var KATEX_DELIMS = [
    { left: "$$", right: "$$", display: true },
    { left: "$", right: "$", display: false },
    { left: "\\(", right: "\\)", display: false },
    { left: "\\[", right: "\\]", display: true },
  ];

  function shouldUseDisplayStyleInPreview(latex) {
    return /\\frac|\\dfrac|\\tfrac|\\cfrac|\\choose|\\over\b|\\genfrac/.test(latex);
  }

  function withDiscretionaryDisplayStyle(latex) {
    var s = String(latex).trim();
    if (!s) return s;
    if (/^\s*\\displaystyle\b/.test(s)) return s;
    if (!shouldUseDisplayStyleInPreview(s)) return s;
    return "\\displaystyle " + s;
  }

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

  /**
   * Find the next math opening delimiter from `from`. Prefer longer opens at the same index ($$ before $).
   */
  function findEarliestOpeningDelimiter(s, from) {
    var candidates = [];
    function tryAdd(left, right, display) {
      var j = s.indexOf(left, from);
      if (j === -1) return;
      if (left === "$") {
        if (j + 1 < s.length && s.charAt(j + 1) === "$") return;
        if (isDollarEscaped(s, j)) return;
      }
      candidates.push({
        pos: j,
        open: left,
        close: right,
        display: !!display,
      });
    }
    tryAdd("$$", "$$", true);
    tryAdd("\\[", "\\]", true);
    tryAdd("\\(", "\\)", false);
    tryAdd("$", "$", false);
    if (candidates.length === 0) return null;
    candidates.sort(function (a, b) {
      if (a.pos !== b.pos) return a.pos - b.pos;
      return b.open.length - a.open.length;
    });
    return candidates[0];
  }

  function findClosingDelimiterPos(s, delim, startInner) {
    if (delim.open === "$$") {
      var k = s.indexOf("$$", startInner);
      while (k !== -1) {
        if (!isDollarEscaped(s, k)) return k;
        k = s.indexOf("$$", k + 2);
      }
      return -1;
    }
    if (delim.open === "\\[") {
      return s.indexOf("\\]", startInner);
    }
    if (delim.open === "\\(") {
      return s.indexOf("\\)", startInner);
    }
    if (delim.open === "$") {
      var i = startInner;
      var n = s.length;
      while (i < n) {
        var c = s.charAt(i);
        if (c === "$" && (i + 1 >= n || s.charAt(i + 1) !== "$") && !isDollarEscaped(s, i)) {
          return i;
        }
        i++;
      }
      return -1;
    }
    return -1;
  }

  /**
   * Essay preview: prose as normal text + delimited regions rendered with KaTeX (not raw LaTeX).
   */
  function buildEssayPreviewHtml(text) {
    var parts = [];
    var i = 0;
    var n = text.length;
    while (i < n) {
      var delim = findEarliestOpeningDelimiter(text, i);
      if (!delim) {
        parts.push({ t: "text", s: text.slice(i) });
        break;
      }
      if (delim.pos > i) {
        parts.push({ t: "text", s: text.slice(i, delim.pos) });
      }
      var innerStart = delim.pos + delim.open.length;
      var closePos = findClosingDelimiterPos(text, delim, innerStart);
      if (closePos === -1) {
        parts.push({ t: "text", s: text.slice(delim.pos) });
        break;
      }
      parts.push({
        t: "math",
        s: text.slice(innerStart, closePos).trim(),
        display: delim.display,
      });
      i = closePos + delim.close.length;
    }
    var out = "";
    for (var p = 0; p < parts.length; p++) {
      if (parts[p].t === "text") {
        out += '<span class="rgee-essay-preview-text">';
        out += escapeHtml(parts[p].s).replace(/\r\n|\r|\n/g, "<br>");
        out += "</span>";
      } else {
        var latex = parts[p].s;
        if (!latex) {
          out += '<span class="rgee-essay-preview-math rgee-essay-preview-math--empty" aria-hidden="true"></span>';
          continue;
        }
        var toRender = parts[p].display ? latex : withDiscretionaryDisplayStyle(latex);
        try {
          out +=
            '<span class="rgee-essay-preview-math">' +
            katex.renderToString(toRender, {
              displayMode: parts[p].display,
              throwOnError: false,
              strict: false,
            }) +
            "</span>";
        } catch (eM) {
          out +=
            '<span class="rgee-essay-preview-math rgee-essay-preview-math--error" title="LaTeX error">' +
            escapeHtml(latex) +
            "</span>";
        }
      }
    }
    return '<div class="rgee-essay-preview-inner">' + out + "</div>";
  }

  function debounce(fn, ms) {
    var t;
    return function () {
      var ctx = this;
      var args = arguments;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(ctx, args);
      }, ms);
    };
  }

  function insertAtCursor(textarea, text) {
    if (!textarea || typeof text !== "string") return;
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var val = textarea.value;
    textarea.value = val.slice(0, start) + text + val.slice(end);
    var pos = start + text.length;
    textarea.selectionStart = textarea.selectionEnd = pos;
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function usesExplicitMathDelimiters(t) {
    var s = String(t);
    if (/\$\$/.test(s)) return true;
    if (/\\\[[\s\S]*\\\]/.test(s)) return true;
    if (/\\\([\s\S]*\\\)/.test(s)) return true;
    var unescaped = s.replace(/\\\$/g, "");
    var n = (unescaped.match(/\$/g) || []).length;
    return n >= 2;
  }

  /**
   * Bare LaTeX from the builder renders in the essay preview only inside delimiters.
   * If the snippet is not already delimited, wrap it as inline ($…$) or display ($$…$$).
   */
  function ensureEssayMathDelimiters(latex) {
    var s = String(latex);
    if (!s.trim()) return s;
    if (usesExplicitMathDelimiters(s)) return s;
    var core = s.trim();
    if (/\r\n|\r|\n/.test(core)) {
      return "$$\n" + core + "\n$$";
    }
    return "$" + core + "$";
  }

  function renderAnswerPreview(container, sourceText) {
    if (!container) return;
    var raw = String(sourceText || "");
    var normalized = normalizeNewlinesInsideMathDelimiters(raw);
    if (typeof katex !== "undefined" && typeof katex.renderToString === "function") {
      try {
        container.innerHTML = buildEssayPreviewHtml(normalized);
        return;
      } catch (e0) {}
    }
    if (typeof renderMathInElement === "function") {
      container.innerHTML = prepareMixedTextForKaTeXAutoRender(raw);
      try {
        renderMathInElement(container, {
          delimiters: KATEX_DELIMS,
          throwOnError: false,
          strict: false,
          trust: false,
          ignoredTags: ["script", "noscript", "style", "textarea", "pre"],
        });
      } catch (e1) {
        container.appendChild(document.createTextNode(" (preview error)"));
      }
      return;
    }
    container.textContent = raw;
  }

  function renderBuilderPreview(container, sourceText) {
    if (!container) return;
    var raw = String(sourceText || "");
    var trimmed = raw.trim().replace(/\r\n|\r|\n/g, " ");
    if (!trimmed) {
      container.innerHTML = "";
      return;
    }

    if (usesExplicitMathDelimiters(raw)) {
      renderAnswerPreview(container, raw);
      return;
    }

    if (typeof katex !== "undefined" && typeof katex.renderToString === "function") {
      try {
        var toRender = withDiscretionaryDisplayStyle(trimmed);
        container.innerHTML = katex.renderToString(toRender, {
          displayMode: true,
          throwOnError: false,
          strict: false,
        });
        return;
      } catch (e) {}
    }

    if (typeof renderMathInElement === "function") {
      renderAnswerPreview(container, raw);
    } else {
      container.textContent = raw;
    }
  }

  /** Mini SVG pictographs for visual-layout toolbar (boxes = number slots). */
  var VISUAL_PICTO = {
    frac:
      '<svg class="latex-picto-svg" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><rect x="5" y="4" width="30" height="11" rx="3" fill="currentColor" opacity="0.2"/><line x1="4" y1="20" x2="36" y2="20" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><rect x="5" y="25" width="30" height="11" rx="3" fill="currentColor" opacity="0.2"/></svg>',
    matrix2:
      '<svg class="latex-picto-svg" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><text x="1" y="26" font-size="22" fill="currentColor" opacity="0.35" font-weight="300">(</text><rect x="10" y="7" width="9" height="9" rx="2" fill="currentColor" opacity="0.2"/><rect x="21" y="7" width="9" height="9" rx="2" fill="currentColor" opacity="0.2"/><rect x="10" y="18" width="9" height="9" rx="2" fill="currentColor" opacity="0.2"/><rect x="21" y="18" width="9" height="9" rx="2" fill="currentColor" opacity="0.2"/><text x="30" y="26" font-size="22" fill="currentColor" opacity="0.35" font-weight="300">)</text></svg>',
    matrix3:
      '<svg class="latex-picto-svg" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><text x="0" y="27" font-size="20" fill="currentColor" opacity="0.32" font-weight="300">(</text><rect x="7" y="5" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="16" y="5" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="25" y="5" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="7" y="14" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="16" y="14" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="25" y="14" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="7" y="23" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="16" y="23" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><rect x="25" y="23" width="7" height="7" rx="1.5" fill="currentColor" opacity="0.18"/><text x="33" y="27" font-size="20" fill="currentColor" opacity="0.32" font-weight="300">)</text></svg>',
    sqrt:
      '<svg class="latex-picto-svg" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><path d="M 6 34 L 9 18 L 14 12 L 34 12" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><rect x="16" y="10" width="20" height="14" rx="2.5" fill="currentColor" opacity="0.2"/></svg>',
    power:
      '<svg class="latex-picto-svg" viewBox="0 0 40 40" aria-hidden="true" focusable="false"><rect x="6" y="16" width="22" height="14" rx="3" fill="currentColor" opacity="0.22"/><rect x="26" y="6" width="10" height="10" rx="2" fill="currentColor" opacity="0.28"/></svg>',
  };

  var SYMBOL_PAGES = [
    {
      title: "Layouts",
      titleA11y: "Visual layout templates",
      layoutsPage: true,
      tools: [
        { visualOpen: "frac", title: "Fraction — two number boxes with a division bar", picto: VISUAL_PICTO.frac },
        { visualOpen: "matrix2", title: "2 by 2 matrix — four number boxes", picto: VISUAL_PICTO.matrix2 },
        { visualOpen: "matrix3", title: "3 by 3 matrix — nine number boxes", picto: VISUAL_PICTO.matrix3 },
        { visualOpen: "sqrt", title: "Square root — one box inside the root", picto: VISUAL_PICTO.sqrt },
        { visualOpen: "power", title: "Power — base box and exponent box", picto: VISUAL_PICTO.power },
      ],
    },
    {
      title: "Arithmetic",
      tools: [
        { label: "+", insert: "+", title: "Plus" },
        { label: "−", insert: "-", title: "Minus" },
        { label: "×", insert: "\\times", title: "Times" },
        { label: "·", insert: "\\cdot", title: "Dot multiply" },
        { label: "*", insert: "\\ast", title: "Asterisk multiply" },
        { label: "÷", insert: "\\div", title: "Division sign (obelus)" },
        { label: "/", insert: "/", title: "Slash (e.g. a/b)" },
        { label: "=", insert: "=", title: "Equals" },
        { label: "<", insert: "<", title: "Less than" },
        { label: ">", insert: ">", title: "Greater than" },
        { label: "≤", insert: "\\leq", title: "Less or equal" },
        { label: "≥", insert: "\\geq", title: "Greater or equal" },
        { label: "≠", insert: "\\neq", title: "Not equal" },
        { label: "≈", insert: "\\approx", title: "Approximately equal" },
        { label: "≡", insert: "\\equiv", title: "Equivalent / congruent" },
        { label: "±", insert: "\\pm", title: "Plus-minus" },
        { label: "∓", insert: "\\mp", title: "Minus-plus" },
        { label: "(", insert: "(", title: "Open parenthesis" },
        { label: ")", insert: ")", title: "Close parenthesis" },
        { label: "[", insert: "[", title: "Open bracket" },
        { label: "]", insert: "]", title: "Close bracket" },
        { label: "{", insert: "\\{", title: "Open brace (in math)" },
        { label: "}", insert: "\\}", title: "Close brace (in math)" },
        { label: "|", insert: "|", title: "Vertical bar" },
        { label: ":", insert: "\\colon", title: "Colon (ratio)" },
        { label: ",", insert: ",", title: "Comma" },
        { label: ".", insert: ".", title: "Decimal point" },
        { label: "%", insert: "\\%", title: "Percent" },
        { label: "!", insert: "!", title: "Factorial" },
      ],
    },
    {
      title: "Structures",
      tools: [
        { label: "√", insert: "\\sqrt{}", title: "Square root" },
        { label: "ⁿ√", insert: "\\sqrt[n]{}", title: "nth root (replace n)" },
        { label: "xⁿ", insert: "^{}", title: "Superscript" },
        { label: "xₙ", insert: "_{}", title: "Subscript" },
        { label: "Σ", insert: "\\sum_{}^{}", title: "Summation" },
        { label: "Π", insert: "\\prod_{}^{}", title: "Product" },
        { label: "∫", insert: "\\int_{}^{}", title: "Integral" },
        { label: "lim", insert: "\\lim_{x \\to \\infty}", title: "Limit (edit variable and target)" },
        {
          label: "matrix",
          insert: "\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}",
          title: "2×2 matrix (pmatrix)",
        },
        {
          label: "bmatrix",
          insert: "\\begin{bmatrix} \\quad & \\quad \\\\ \\quad & \\quad \\end{bmatrix}",
          title: "Bracket matrix",
        },
        {
          label: "cases",
          insert: "\\begin{cases} \\quad & \\text{if } \\\\ \\quad & \\text{if } \\end{cases}",
          title: "Cases",
        },
        { label: "text", insert: "\\text{}", title: "Roman text inside math" },
      ],
    },
    {
      title: "Delimiters",
      tools: [
        { label: "( )", insert: "\\left( \\right)", title: "Scaled parentheses" },
        { label: "[ ]", insert: "\\left[ \\right]", title: "Scaled brackets" },
        { label: "{ }", insert: "\\left\\{ \\right\\}", title: "Scaled braces" },
        { label: "| |", insert: "\\left| \\right|", title: "Absolute value" },
        { label: "‖ ‖", insert: "\\left\\| \\right\\|", title: "Norm" },
        { label: "⌊ ⌋", insert: "\\left\\lfloor \\right\\rfloor", title: "Floor" },
        { label: "⌈ ⌉", insert: "\\left\\lceil \\right\\rceil", title: "Ceiling" },
        { label: "⟨ ⟩", insert: "\\langle \\rangle", title: "Angle brackets" },
      ],
    },
    {
      title: "Relations & sets",
      tools: [
        { label: "∝", insert: "\\propto", title: "Proportional" },
        { label: "∞", insert: "\\infty", title: "Infinity" },
        { label: "∂", insert: "\\partial", title: "Partial" },
        { label: "∇", insert: "\\nabla", title: "Nabla" },
        { label: "∀", insert: "\\forall", title: "For all" },
        { label: "∃", insert: "\\exists", title: "Exists" },
        { label: "∈", insert: "\\in", title: "Element of" },
        { label: "∉", insert: "\\notin", title: "Not in" },
        { label: "⊂", insert: "\\subset", title: "Subset" },
        { label: "⊆", insert: "\\subseteq", title: "Subseteq" },
        { label: "∪", insert: "\\cup", title: "Union" },
        { label: "∩", insert: "\\cap", title: "Intersection" },
        { label: "∅", insert: "\\emptyset", title: "Empty set" },
        { label: "°", insert: "^\\circ", title: "Degrees" },
      ],
    },
    {
      title: "Arrows",
      tools: [
        { label: "→", insert: "\\rightarrow", title: "Right arrow" },
        { label: "⇒", insert: "\\Rightarrow", title: "Implies" },
        { label: "←", insert: "\\leftarrow", title: "Left arrow" },
        { label: "⇐", insert: "\\Leftarrow", title: "Left double" },
        { label: "↔", insert: "\\leftrightarrow", title: "Bidirectional" },
        { label: "⇔", insert: "\\Leftrightarrow", title: "Iff" },
        { label: "↦", insert: "\\mapsto", title: "Maps to" },
        { label: "↑", insert: "\\uparrow", title: "Up" },
        { label: "↓", insert: "\\downarrow", title: "Down" },
      ],
    },
    {
      title: "Greek (lower)",
      tools: [
        { label: "α", insert: "\\alpha", title: "alpha" },
        { label: "β", insert: "\\beta", title: "beta" },
        { label: "γ", insert: "\\gamma", title: "gamma" },
        { label: "δ", insert: "\\delta", title: "delta" },
        { label: "ε", insert: "\\varepsilon", title: "varepsilon" },
        { label: "ζ", insert: "\\zeta", title: "zeta" },
        { label: "η", insert: "\\eta", title: "eta" },
        { label: "θ", insert: "\\theta", title: "theta" },
        { label: "λ", insert: "\\lambda", title: "lambda" },
        { label: "μ", insert: "\\mu", title: "mu" },
        { label: "π", insert: "\\pi", title: "pi" },
        { label: "σ", insert: "\\sigma", title: "sigma" },
        { label: "φ", insert: "\\phi", title: "phi" },
        { label: "ω", insert: "\\omega", title: "omega" },
      ],
    },
    {
      title: "Greek caps & trig",
      tools: [
        { label: "Γ", insert: "\\Gamma", title: "Gamma" },
        { label: "Δ", insert: "\\Delta", title: "Delta" },
        { label: "Θ", insert: "\\Theta", title: "Theta" },
        { label: "Λ", insert: "\\Lambda", title: "Lambda" },
        { label: "Σ", insert: "\\Sigma", title: "Sigma" },
        { label: "Φ", insert: "\\Phi", title: "Phi" },
        { label: "Ω", insert: "\\Omega", title: "Omega" },
        { label: "sin", insert: "\\sin", title: "sin" },
        { label: "cos", insert: "\\cos", title: "cos" },
        { label: "tan", insert: "\\tan", title: "tan" },
        { label: "cot", insert: "\\cot", title: "cot" },
        { label: "sec", insert: "\\sec", title: "sec" },
        { label: "csc", insert: "\\csc", title: "csc" },
        { label: "ln", insert: "\\ln", title: "natural log" },
        { label: "log", insert: "\\log", title: "log" },
        { label: "exp", insert: "\\exp", title: "exp" },
      ],
    },
    {
      title: "Blackboard & layout",
      tools: [
        { label: "ℝ", insert: "\\mathbb{R}", title: "Real numbers" },
        { label: "ℕ", insert: "\\mathbb{N}", title: "Natural numbers" },
        { label: "ℤ", insert: "\\mathbb{Z}", title: "Integers" },
        { label: "ℚ", insert: "\\mathbb{Q}", title: "Rationals" },
        { label: "ℂ", insert: "\\mathbb{C}", title: "Complex" },
        { label: "x̂", insert: "\\hat{}", title: "Hat" },
        { label: "x̄", insert: "\\bar{}", title: "Bar" },
        { label: "x⃗", insert: "\\vec{}", title: "Vector arrow" },
        { label: "‾", insert: "\\overline{}", title: "Overline" },
        { label: "_", insert: "\\underline{}", title: "Underline" },
        { label: "⋯", insert: "\\cdots", title: "Centered dots" },
        { label: "…", insert: "\\ldots", title: "Lower dots" },
        { label: "\\,", insert: "\\,", title: "Thin space" },
        { label: "\\;", insert: "\\;", title: "Thick space" },
        { label: "quad", insert: "\\quad", title: "Quad space" },
        { label: "$$", insert: "$$", title: "Display math delimiter (pair manually)" },
        { label: "$", insert: "$", title: "Inline math delimiter" },
        { label: "\\(", insert: "\\(", title: "Inline (open); pair with \\)" },
        { label: "\\[", insert: "\\[", title: "Display (open); pair with \\]" },
      ],
    },
  ];

  /** Toolbar inserts that open the slot workspace instead of raw paste-at-cursor. */
  var LATEX_WRAP_ONE = {
    hat: "\\hat",
    bar: "\\bar",
    vec: "\\vec",
    overline: "\\overline",
    underline: "\\underline",
  };

  /** Which math toolbar control has the builder preview armed (toggle). */
  var gActiveBuilderToolbarKey = null;

  function clearToolbarBuilderActiveHighlight(root) {
    if (!root) return;
    var prev = root.querySelectorAll(".latex-tool-btn--builder-active");
    for (var j = 0; j < prev.length; j++) {
      prev[j].classList.remove("latex-tool-btn--builder-active");
      prev[j].setAttribute("aria-pressed", "false");
    }
  }

  /**
   * When inactive: builder + slot boxes are disabled; visual template cleared.
   * LaTeX in the builder is left for copy until edited again.
   */
  function applyBuilderPreviewInteractionEnabled(builder, enabled) {
    var stack = document.getElementById("latex-builder-preview-stack");
    var panel = document.getElementById("builder-preview-panel");
    var mathRoot = document.getElementById("math-visual-root");
    if (stack) {
      stack.classList.toggle("latex-builder-preview-stack--inactive", !enabled);
      stack.setAttribute("aria-disabled", enabled ? "false" : "true");
    }
    if (panel) {
      panel.classList.toggle("math-builder-preview-panel--inactive", !enabled);
    }
    if (builder) {
      builder.disabled = !enabled;
      builder.setAttribute("aria-disabled", enabled ? "false" : "true");
      if (!enabled) {
        try {
          builder.blur();
        } catch (eB) {}
      }
    }
    if (mathRoot) {
      var slots = mathRoot.querySelectorAll(".math-visual-slot");
      for (var s = 0; s < slots.length; s++) {
        slots[s].disabled = !enabled;
      }
      if (!enabled) {
        mathRoot.innerHTML = "";
        mathRoot.removeAttribute("data-template");
      }
    }
  }

  function setToolbarBuilderArmed(root, key, activeBtn, builder, armed) {
    clearToolbarBuilderActiveHighlight(root);
    gActiveBuilderToolbarKey = armed ? key : null;
    if (activeBtn && armed) {
      activeBtn.classList.add("latex-tool-btn--builder-active");
      activeBtn.setAttribute("aria-pressed", "true");
    }
    applyBuilderPreviewInteractionEnabled(builder, !!armed);
  }

  function mapInsertToVisual(insert) {
    if (!insert || typeof insert !== "string") return null;
    var s = insert.replace(/\r\n|\r/g, "\n").trim();
    if (s === "\\frac{}{}" || s === "\\dfrac{}{}" || s === "\\tfrac{}{}") return "frac";
    if (s === "\\sqrt{}") return "sqrt";
    if (s === "\\sqrt[n]{}" || /^\\sqrt\[[^\]]*\]\{\}$/.test(s)) return "sqrtn";
    if (s === "^{}") return "power";
    if (s === "_{}") return "sub";
    if (s === "\\sum_{}^{}") return "sum";
    if (s === "\\prod_{}^{}") return "prod";
    if (s === "\\int_{}^{}") return "int";
    if (s.indexOf("\\lim_{") === 0) return "lim";
    if (s.indexOf("\\begin{pmatrix}") !== -1) {
      var amp = (s.match(/&/g) || []).length;
      if (amp >= 6) return "matrix3";
      return "matrix2";
    }
    if (s.indexOf("\\begin{bmatrix}") !== -1) return "bmatrix2";
    if (s.indexOf("\\begin{cases}") !== -1) return "cases";
    if (s === "\\text{}") return "text";
    if (s === "\\hat{}") return "hat";
    if (s === "\\bar{}") return "bar";
    if (s === "\\vec{}") return "vec";
    if (s === "\\overline{}") return "overline";
    if (s === "\\underline{}") return "underline";
    return null;
  }

  function buildPagedToolbar(root, builder) {
    if (!root || !builder) return;
    root.innerHTML = "";
    root.className = "latex-toolbar latex-toolbar-paged";

    var viewport = document.createElement("div");
    viewport.className = "latex-tool-pages-viewport";

    var strip = document.createElement("div");
    strip.className = "latex-tool-pages-strip";

    SYMBOL_PAGES.forEach(function (pageDef, idx) {
      var page = document.createElement("div");
      page.className = "latex-tool-page";
      page.hidden = idx !== 0;
      page.setAttribute("data-page-index", String(idx));
      page.setAttribute("role", "group");
      page.setAttribute("aria-label", pageDef.titleA11y || pageDef.title);
      if (pageDef.layoutsPage) page.classList.add("latex-tool-page--layouts");

      var titleEl = document.createElement("div");
      titleEl.className = "latex-tool-page-title";
      titleEl.textContent = pageDef.title;

      var grid = document.createElement("div");
      grid.className = "latex-tool-grid";

      pageDef.tools.forEach(function (t, toolIdx) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "btn btn-secondary latex-tool-btn";
        b.setAttribute("aria-pressed", "false");
        var toolKey = "p" + idx + "_t" + toolIdx;
        if (t.visualOpen) {
          b.className += " latex-tool-btn--pictograph";
          b.innerHTML = t.picto || "";
          b.setAttribute("aria-label", t.title);
          b.addEventListener("click", function () {
            if (gActiveBuilderToolbarKey === toolKey) {
              setToolbarBuilderArmed(root, null, null, builder, false);
              return;
            }
            setToolbarBuilderArmed(root, toolKey, b, builder, true);
            if (typeof window.rgeeOpenMathVisual === "function") {
              window.rgeeOpenMathVisual(t.visualOpen);
            }
          });
        } else {
          b.textContent = t.label;
          b.title = t.title || t.insert;
          b.addEventListener("click", function () {
            var vId = mapInsertToVisual(t.insert);
            if (vId && typeof window.rgeeOpenMathVisual === "function") {
              if (gActiveBuilderToolbarKey === toolKey) {
                setToolbarBuilderArmed(root, null, null, builder, false);
                return;
              }
              setToolbarBuilderArmed(root, toolKey, b, builder, true);
              window.rgeeOpenMathVisual(vId);
            } else {
              if (gActiveBuilderToolbarKey === toolKey) {
                setToolbarBuilderArmed(root, null, null, builder, false);
                return;
              }
              setToolbarBuilderArmed(root, toolKey, b, builder, true);
              var mrPlain = document.getElementById("math-visual-root");
              if (mrPlain) {
                mrPlain.innerHTML = "";
                mrPlain.removeAttribute("data-template");
              }
              insertAtCursor(builder, t.insert);
            }
          });
        }
        grid.appendChild(b);
      });

      page.appendChild(titleEl);
      page.appendChild(grid);
      strip.appendChild(page);
    });

    viewport.appendChild(strip);

    var nav = document.createElement("div");
    nav.className = "latex-tool-page-nav";

    var prev = document.createElement("button");
    prev.type = "button";
    prev.className = "btn btn-secondary latex-page-nav-btn";
    prev.setAttribute("aria-label", "Previous symbol page");
    prev.innerHTML = "&#8592;";

    var indicator = document.createElement("span");
    indicator.className = "latex-tool-page-indicator";

    var next = document.createElement("button");
    next.type = "button";
    next.className = "btn btn-secondary latex-page-nav-btn";
    next.setAttribute("aria-label", "Next symbol page");
    next.innerHTML = "&#8594;";

    var currentPage = 0;
    var total = SYMBOL_PAGES.length;

    function updateIndicator() {
      indicator.textContent = currentPage + 1 + " / " + total + " · " + SYMBOL_PAGES[currentPage].title;
    }

    function setPage(i) {
      currentPage = ((i % total) + total) % total;
      var pages = strip.querySelectorAll(".latex-tool-page");
      for (var j = 0; j < pages.length; j++) {
        pages[j].hidden = j !== currentPage;
      }
      updateIndicator();
      setToolbarBuilderArmed(root, null, null, builder, false);
    }

    prev.addEventListener("click", function () {
      setPage(currentPage - 1);
    });
    next.addEventListener("click", function () {
      setPage(currentPage + 1);
    });

    nav.appendChild(prev);
    nav.appendChild(indicator);
    nav.appendChild(next);

    if (total <= 1) {
      nav.hidden = true;
    }

    root.appendChild(viewport);
    root.appendChild(nav);
    setPage(0);
  }

  /**
   * Wolfram-style visual templates: slot inputs compile to LaTeX in the builder.
   */
  function initMathVisualWorkbench(builder) {
    var root = document.getElementById("math-visual-root");
    if (!root || !builder) return;

    function latexCell(v) {
      var t = String(v || "").trim();
      return t || "{}";
    }

    function syncToBuilder() {
      if (builder.disabled) return;
      var t = root.getAttribute("data-template") || "";
      var latex = "";
      var slots;
      var r;
      var c;
      if (t === "frac") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex = "\\frac{" + latexCell(slots[0] ? slots[0].value : "") + "}{" + latexCell(slots[1] ? slots[1].value : "") + "}";
      } else if (t === "matrix2") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex =
          "\\begin{pmatrix} " +
          latexCell(slots[0].value) +
          " & " +
          latexCell(slots[1].value) +
          " \\\\ " +
          latexCell(slots[2].value) +
          " & " +
          latexCell(slots[3].value) +
          " \\end{pmatrix}";
      } else if (t === "bmatrix2") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex =
          "\\begin{bmatrix} " +
          latexCell(slots[0].value) +
          " & " +
          latexCell(slots[1].value) +
          " \\\\ " +
          latexCell(slots[2].value) +
          " & " +
          latexCell(slots[3].value) +
          " \\end{bmatrix}";
      } else if (t === "matrix3") {
        slots = root.querySelectorAll(".math-visual-slot");
        var rows = [];
        for (r = 0; r < 3; r++) {
          var row = [];
          for (c = 0; c < 3; c++) {
            row.push(latexCell(slots[r * 3 + c].value));
          }
          rows.push(row.join(" & "));
        }
        latex = "\\begin{pmatrix} " + rows.join(" \\\\ ") + " \\end{pmatrix}";
      } else if (t === "sqrt") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex = "\\sqrt{" + latexCell(slots[0] ? slots[0].value : "") + "}";
      } else if (t === "sqrtn") {
        slots = root.querySelectorAll(".math-visual-slot");
        var nStr2 = String(slots[0] ? slots[0].value : "").trim();
        var innerSqrt = String(slots[1] ? slots[1].value : "").trim();
        latex = nStr2 ? "\\sqrt[" + nStr2 + "]{" + innerSqrt + "}" : "\\sqrt{" + innerSqrt + "}";
      } else if (t === "power") {
        slots = root.querySelectorAll(".math-visual-slot");
        var bRaw = String(slots[0] ? slots[0].value : "").trim();
        var eRaw = String(slots[1] ? slots[1].value : "").trim();
        if (eRaw) {
          latex = (bRaw || "\\square") + "^{" + eRaw + "}";
        } else {
          latex = bRaw || "{}";
        }
      } else if (t === "sub") {
        slots = root.querySelectorAll(".math-visual-slot");
        var baseS = String(slots[0] ? slots[0].value : "").trim();
        var subS = String(slots[1] ? slots[1].value : "").trim();
        if (subS) {
          latex = (baseS || "\\square") + "_{" + subS + "}";
        } else {
          latex = baseS || "{}";
        }
      } else if (t === "sum" || t === "prod" || t === "int") {
        slots = root.querySelectorAll(".math-visual-slot");
        var opTok = t === "sum" ? "\\sum" : t === "prod" ? "\\prod" : "\\int";
        var lo = String(slots[0] ? slots[0].value : "").trim();
        var hi = String(slots[1] ? slots[1].value : "").trim();
        var tail = String(slots[2] ? slots[2].value : "").trim();
        latex = opTok + "_{" + lo + "}^{" + hi + "}" + (tail ? " " + tail : "");
      } else if (t === "lim") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex = "\\lim_{" + String(slots[0] ? slots[0].value : "").trim() + "}";
      } else if (t === "cases") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex =
          "\\begin{cases} " +
          latexCell(slots[0].value) +
          " & " +
          latexCell(slots[1].value) +
          " \\\\ " +
          latexCell(slots[2].value) +
          " & " +
          latexCell(slots[3].value) +
          " \\end{cases}";
      } else if (t === "text") {
        slots = root.querySelectorAll(".math-visual-slot");
        latex = "\\text{" + String(slots[0] ? slots[0].value : "").trim() + "}";
      } else if (LATEX_WRAP_ONE[t]) {
        slots = root.querySelectorAll(".math-visual-slot");
        latex = LATEX_WRAP_ONE[t] + "{" + String(slots[0] ? slots[0].value : "").trim() + "}";
      } else {
        return;
      }
      builder.value = latex;
      builder.dispatchEvent(new Event("input", { bubbles: true }));
    }

    function makeSlot(ariaLabel) {
      var inp = document.createElement("input");
      inp.type = "text";
      inp.className = "math-visual-slot";
      inp.setAttribute("aria-label", ariaLabel);
      inp.setAttribute("inputmode", "text");
      inp.autocomplete = "off";
      inp.spellcheck = false;
      inp.addEventListener("input", syncToBuilder);
      inp.addEventListener("change", syncToBuilder);
      return inp;
    }

    function renderTemplate(id) {
      root.setAttribute("data-template", id);
      root.innerHTML = "";

      if (id === "frac") {
        var wrap = document.createElement("div");
        wrap.className = "math-visual-fraction";
        var num = document.createElement("div");
        num.className = "math-visual-fraction-num";
        num.appendChild(makeSlot("Numerator"));
        var bar = document.createElement("div");
        bar.className = "math-visual-fraction-bar";
        bar.setAttribute("aria-hidden", "true");
        var den = document.createElement("div");
        den.className = "math-visual-fraction-den";
        den.appendChild(makeSlot("Denominator"));
        wrap.appendChild(num);
        wrap.appendChild(bar);
        wrap.appendChild(den);
        root.appendChild(wrap);
      } else if (id === "matrix2") {
        var mw = document.createElement("div");
        mw.className = "math-visual-matrix-wrap";
        var lb = document.createElement("span");
        lb.className = "math-visual-bracket";
        lb.setAttribute("aria-hidden", "true");
        lb.textContent = "(";
        var tbl = document.createElement("table");
        tbl.className = "math-visual-matrix";
        tbl.setAttribute("role", "grid");
        for (var r2 = 0; r2 < 2; r2++) {
          var tr = document.createElement("tr");
          for (var c2 = 0; c2 < 2; c2++) {
            var td = document.createElement("td");
            td.appendChild(makeSlot("Row " + (r2 + 1) + ", column " + (c2 + 1)));
            tr.appendChild(td);
          }
          tbl.appendChild(tr);
        }
        var rb = document.createElement("span");
        rb.className = "math-visual-bracket";
        rb.setAttribute("aria-hidden", "true");
        rb.textContent = ")";
        mw.appendChild(lb);
        mw.appendChild(tbl);
        mw.appendChild(rb);
        root.appendChild(mw);
      } else if (id === "bmatrix2") {
        var mwb = document.createElement("div");
        mwb.className = "math-visual-matrix-wrap";
        var lbb = document.createElement("span");
        lbb.className = "math-visual-bracket";
        lbb.setAttribute("aria-hidden", "true");
        lbb.textContent = "[";
        var tblb = document.createElement("table");
        tblb.className = "math-visual-matrix";
        tblb.setAttribute("role", "grid");
        for (var rbI = 0; rbI < 2; rbI++) {
          var trb = document.createElement("tr");
          for (var cbI = 0; cbI < 2; cbI++) {
            var tdb = document.createElement("td");
            tdb.appendChild(makeSlot("Row " + (rbI + 1) + ", column " + (cbI + 1)));
            trb.appendChild(tdb);
          }
          tblb.appendChild(trb);
        }
        var rbb = document.createElement("span");
        rbb.className = "math-visual-bracket";
        rbb.setAttribute("aria-hidden", "true");
        rbb.textContent = "]";
        mwb.appendChild(lbb);
        mwb.appendChild(tblb);
        mwb.appendChild(rbb);
        root.appendChild(mwb);
      } else if (id === "matrix3") {
        var mw3 = document.createElement("div");
        mw3.className = "math-visual-matrix-wrap";
        var lb3 = document.createElement("span");
        lb3.className = "math-visual-bracket";
        lb3.setAttribute("aria-hidden", "true");
        lb3.textContent = "(";
        var tbl3 = document.createElement("table");
        tbl3.className = "math-visual-matrix";
        tbl3.setAttribute("role", "grid");
        for (var r3 = 0; r3 < 3; r3++) {
          var tr3 = document.createElement("tr");
          for (var c3 = 0; c3 < 3; c3++) {
            var td3 = document.createElement("td");
            td3.appendChild(makeSlot("Row " + (r3 + 1) + ", column " + (c3 + 1)));
            tr3.appendChild(td3);
          }
          tbl3.appendChild(tr3);
        }
        var rb3 = document.createElement("span");
        rb3.className = "math-visual-bracket";
        rb3.setAttribute("aria-hidden", "true");
        rb3.textContent = ")";
        mw3.appendChild(lb3);
        mw3.appendChild(tbl3);
        mw3.appendChild(rb3);
        root.appendChild(mw3);
      } else if (id === "sqrt") {
        var sw = document.createElement("div");
        sw.className = "math-visual-sqrt-wrap";
        var sym = document.createElement("span");
        sym.className = "math-visual-sqrt-symbol";
        sym.textContent = "√";
        sym.setAttribute("aria-hidden", "true");
        var box = document.createElement("div");
        box.className = "math-visual-sqrt-inner";
        box.appendChild(makeSlot("Radicand (inside the square root)"));
        sw.appendChild(sym);
        sw.appendChild(box);
        root.appendChild(sw);
      } else if (id === "power") {
        var pw = document.createElement("div");
        pw.className = "math-visual-power-wrap";
        var baseWrap = document.createElement("div");
        baseWrap.className = "math-visual-power-base";
        baseWrap.appendChild(makeSlot("Base"));
        var expWrap = document.createElement("div");
        expWrap.className = "math-visual-power-exp";
        expWrap.appendChild(makeSlot("Exponent"));
        pw.appendChild(baseWrap);
        pw.appendChild(expWrap);
        root.appendChild(pw);
      } else if (id === "sqrtn") {
        var snr = document.createElement("div");
        snr.className = "math-visual-sqrtn-row";
        var idxWrap = document.createElement("div");
        idxWrap.className = "math-visual-sqrtn-index";
        idxWrap.appendChild(makeSlot("Root index (nth)"));
        var radWrap = document.createElement("div");
        radWrap.className = "math-visual-sqrt-inner math-visual-sqrt-inner--nth";
        radWrap.appendChild(makeSlot("Radicand"));
        snr.appendChild(idxWrap);
        snr.appendChild(radWrap);
        root.appendChild(snr);
      } else if (id === "sub") {
        var subWrap = document.createElement("div");
        subWrap.className = "math-visual-sub-wrap";
        var baseRow = document.createElement("div");
        baseRow.className = "math-visual-sub-base";
        baseRow.appendChild(makeSlot("Base"));
        var subRow = document.createElement("div");
        subRow.className = "math-visual-sub-lower";
        subRow.appendChild(makeSlot("Subscript"));
        subWrap.appendChild(baseRow);
        subWrap.appendChild(subRow);
        root.appendChild(subWrap);
      } else if (id === "sum" || id === "prod" || id === "int") {
        var opRow = document.createElement("div");
        opRow.className = "math-visual-oprow";
        var big = document.createElement("span");
        big.className = "math-visual-bigop";
        big.setAttribute("aria-hidden", "true");
        big.textContent = id === "sum" ? "∑" : id === "prod" ? "∏" : "∫";
        var limCol = document.createElement("div");
        limCol.className = "math-visual-limits-col";
        var lr1 = document.createElement("div");
        lr1.className = "math-visual-limit-row";
        lr1.appendChild(makeSlot("Lower limit (subscript)"));
        var lr2 = document.createElement("div");
        lr2.className = "math-visual-limit-row";
        lr2.appendChild(makeSlot("Upper limit (superscript)"));
        limCol.appendChild(lr1);
        limCol.appendChild(lr2);
        var bodyOp = document.createElement("div");
        bodyOp.className = "math-visual-oprow-body";
        bodyOp.appendChild(makeSlot("Expression after operator"));
        opRow.appendChild(big);
        opRow.appendChild(limCol);
        opRow.appendChild(bodyOp);
        root.appendChild(opRow);
      } else if (id === "lim") {
        var lw = document.createElement("div");
        lw.className = "math-visual-lim-wrap";
        var limKw = document.createElement("span");
        limKw.className = "math-visual-lim-keyword";
        limKw.textContent = "lim";
        limKw.setAttribute("aria-hidden", "true");
        var under = document.createElement("div");
        under.className = "math-visual-lim-under";
        var limSlot = makeSlot("Under limit, e.g. x \\to \\infty");
        limSlot.value = "x \\to \\infty";
        under.appendChild(limSlot);
        lw.appendChild(limKw);
        lw.appendChild(under);
        root.appendChild(lw);
      } else if (id === "cases") {
        var cw = document.createElement("div");
        cw.className = "math-visual-cases-wrap";
        var lbc = document.createElement("span");
        lbc.className = "math-visual-bracket math-visual-bracket--cases";
        lbc.setAttribute("aria-hidden", "true");
        lbc.textContent = "{";
        var tblc = document.createElement("table");
        tblc.className = "math-visual-matrix math-visual-matrix--cases";
        tblc.setAttribute("role", "grid");
        for (var rc = 0; rc < 2; rc++) {
          var trc = document.createElement("tr");
          for (var cc = 0; cc < 2; cc++) {
            var tdc = document.createElement("td");
            tdc.appendChild(makeSlot("Cases row " + (rc + 1) + ", column " + (cc + 1)));
            trc.appendChild(tdc);
          }
          tblc.appendChild(trc);
        }
        cw.appendChild(lbc);
        cw.appendChild(tblc);
        root.appendChild(cw);
      } else if (id === "text") {
        var tw = document.createElement("div");
        tw.className = "math-visual-text-wrap";
        tw.appendChild(makeSlot("Text inside \\text{…}"));
        root.appendChild(tw);
      } else if (LATEX_WRAP_ONE[id]) {
        var ww = document.createElement("div");
        ww.className = "math-visual-wrap-one";
        ww.appendChild(makeSlot("Argument for " + id));
        root.appendChild(ww);
      }

      syncToBuilder();
      var first = root.querySelector(".math-visual-slot");
      if (first) first.focus();
    }

    window.rgeeOpenMathVisual = function (id) {
      renderTemplate(id);
      var panel = document.getElementById("builder-preview-panel");
      var scrollEl = panel || root;
      try {
        scrollEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
      } catch (e2) {
        scrollEl.scrollIntoView();
      }
    };
  }

  function boot() {
    var answer = document.getElementById("answer");
    var builder = document.getElementById("latex-builder-input");
    var builderPrev = document.getElementById("latex-builder-preview");
    var toolbarRoot = document.getElementById("latex-toolbar-root");
    var previewStack = document.getElementById("latex-builder-preview-stack");
    var answerPreview = document.getElementById("answer-katex-preview");
    if (!answer || !answerPreview || !builder || !builderPrev || !toolbarRoot) return;

    applyBuilderPreviewInteractionEnabled(builder, false);

    function syncPreviewEditorSize() {
      if (!previewStack) return;
      requestAnimationFrame(function () {
        var kh = builderPrev.scrollHeight;
        var th = builder.scrollHeight;
        var minH = 72;
        var h = Math.max(minH, kh, th);
        builder.style.minHeight = h + "px";
        builderPrev.style.minHeight = h + "px";
        builder.style.height = "auto";
        var h2 = Math.max(minH, builder.scrollHeight, builderPrev.scrollHeight);
        builder.style.minHeight = h2 + "px";
        builder.style.height = h2 + "px";
        builderPrev.style.minHeight = h2 + "px";
      });
    }

    initMathVisualWorkbench(builder);
    buildPagedToolbar(toolbarRoot, builder);

    var runBuilderPreview = debounce(function () {
      renderBuilderPreview(builderPrev, builder.value);
      syncPreviewEditorSize();
    }, 150);
    builder.addEventListener("input", function () {
      runBuilderPreview();
      syncPreviewEditorSize();
    });
    runBuilderPreview();
    syncPreviewEditorSize();

    var runAnswerPreview = debounce(function () {
      renderAnswerPreview(answerPreview, answer.value);
    }, 200);
    answer.addEventListener("input", runAnswerPreview);
    runAnswerPreview();

    var onResizeSync = debounce(function () {
      syncPreviewEditorSize();
    }, 150);
    window.addEventListener("resize", onResizeSync);

    var copyBtn = document.getElementById("latex-copy-btn");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var v = builder.value;
        if (!v) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(v).catch(function () {});
        } else {
          builder.select();
          try {
            document.execCommand("copy");
          } catch (e1) {}
        }
      });
    }

    var insertBtn = document.getElementById("latex-insert-btn");
    if (insertBtn) {
      insertBtn.addEventListener("click", function () {
        var v = builder.value;
        if (!v || !String(v).trim()) return;
        insertAtCursor(answer, ensureEssayMathDelimiters(v));
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

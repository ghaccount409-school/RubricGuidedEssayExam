/**
 * KaTeX formula builder (side panel) + live preview for the exam answer textarea.
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

  /** When these appear, prepend \\displaystyle so \\frac etc. get a clear horizontal bar in preview. */
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

  /** Essay box: prose + optional $...$ / $$...$$ (auto-render only finds delimited math). */
  function renderAnswerPreview(container, sourceText) {
    if (!container) return;
    if (typeof renderMathInElement !== "function") {
      container.textContent = sourceText || "";
      return;
    }
    container.innerHTML = escapeHtml(sourceText || "").replace(/\n/g, "<br>");
    try {
      renderMathInElement(container, {
        delimiters: KATEX_DELIMS,
        throwOnError: false,
        strict: false,
      });
    } catch (e) {
      container.appendChild(document.createTextNode(" (preview error)"));
    }
  }

  /**
   * Formula workspace: treat whole textarea as one display-math expression when the student
   * has not added $ / $$ / \\( / \\[ delimiters (toolbar inserts are almost always "raw" LaTeX).
   */
  function renderBuilderPreview(container, sourceText) {
    if (!container) return;
    var raw = String(sourceText || "");
    var trimmed = raw.trim();
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

  /**
   * Paginated symbol picker: each page is a title + grid of buttons.
   */
  var SYMBOL_PAGES = [
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
        {
          label: "a⁄b",
          insert: "\\frac{}{}",
          title: "Fraction with horizontal bar (preview auto-emphasizes bar when needed)",
        },
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
      page.setAttribute("aria-label", pageDef.title);

      var titleEl = document.createElement("div");
      titleEl.className = "latex-tool-page-title";
      titleEl.textContent = pageDef.title;

      var grid = document.createElement("div");
      grid.className = "latex-tool-grid";

      pageDef.tools.forEach(function (t) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "btn btn-secondary latex-tool-btn";
        b.textContent = t.label;
        b.title = t.title || t.insert;
        b.addEventListener("click", function () {
          insertAtCursor(builder, t.insert);
        });
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

  function boot() {
    var answer = document.getElementById("answer");
    var preview = document.getElementById("answer-katex-preview");
    var builder = document.getElementById("latex-builder-input");
    var builderPrev = document.getElementById("latex-builder-preview");
    var toolbarRoot = document.getElementById("latex-toolbar-root");
    if (!answer || !preview || !builder || !builderPrev || !toolbarRoot) return;

    buildPagedToolbar(toolbarRoot, builder);

    var runAnswerPreview = debounce(function () {
      renderAnswerPreview(preview, answer.value);
    }, 200);
    answer.addEventListener("input", runAnswerPreview);
    runAnswerPreview();

    var runBuilderPreview = debounce(function () {
      renderBuilderPreview(builderPrev, builder.value);
    }, 150);
    builder.addEventListener("input", runBuilderPreview);
    runBuilderPreview();

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
          } catch (e2) {}
        }
      });
    }

    var insertBtn = document.getElementById("latex-insert-btn");
    if (insertBtn) {
      insertBtn.addEventListener("click", function () {
        var v = builder.value;
        if (!v) return;
        insertAtCursor(answer, v);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

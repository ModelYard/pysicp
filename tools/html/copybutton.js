// Copy buttons for code blocks.
//
// For a REPL transcript, copy what a reader would TYPE: the prompted lines,
// with `>>> ` and `... ` removed, and the interpreter's output left out. That
// is the rule sphinx-copybutton implements (only_copy_prompt_lines +
// remove_prompts) and what docs.python.org uses; this is a dependency-free
// version of it. Any other block is copied verbatim.
//
// Deliberately a CLASSIC script, not an ES module: browsers refuse to load
// `type="module"` over file://, and the book is often opened by double-clicking
// the HTML. The CommonJS export at the bottom is what lets node test it.

(function () {
  'use strict';

  var PROMPT = /^(>>> ?|\.\.\. ?)/;

  function copyableText(source) {
    var lines = source.replace(/\n$/, '').split('\n');
    var prompted = lines.filter(function (line) { return PROMPT.test(line); });

    // No prompts: not a transcript, so the whole block is what you want.
    if (prompted.length === 0) return source.replace(/\n$/, '');

    // Prompted: input lines only, stripped. Output would be a syntax error if
    // pasted back into a REPL.
    return prompted.map(function (line) { return line.replace(PROMPT, ''); }).join('\n');
  }

  // navigator.clipboard needs a secure context, which file:// is not in every
  // browser, so keep the legacy path as a fallback.
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      var area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.top = '-9999px';
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(area);
      ok ? resolve() : reject(new Error('copy failed'));
    });
  }

  // Some transcripts have no prompt at all -- Scheme's do not -- so output is
  // identified by markup instead (span.go, emitted by the pandoc filter).
  // Prompts win when present, being the more precise signal.
  function copyableFromElement(code) {
    var text = code.textContent;
    var lines = text.replace(/\n$/, '').split('\n');
    var hasPrompt = lines.some(function (line) { return PROMPT.test(line); });
    if (hasPrompt) return copyableText(text);

    if (code.querySelector('.go')) {
      var clone = code.cloneNode(true);
      var outputs = clone.querySelectorAll('.go');
      for (var i = 0; i < outputs.length; i++) {
        outputs[i].parentNode.removeChild(outputs[i]);
      }
      return clone.textContent.replace(/\n$/, '');
    }

    return copyableText(text);
  }

  function addButton(pre) {
    if (pre.querySelector('.copy-button')) return;
    var code = pre.querySelector('code') || pre;

    // A block that is nothing but interpreter output has nothing to type, so
    // it gets no button rather than a button that copies an empty string.
    if (copyableFromElement(code).trim() === '') return;
    var button = document.createElement('button');
    button.className = 'copy-button';
    button.type = 'button';
    button.textContent = 'Copy';
    button.setAttribute('aria-label', 'Copy code to clipboard');

    button.addEventListener('click', function () {
      copyText(copyableFromElement(code)).then(
        function () { button.textContent = 'Copied'; },
        function () { button.textContent = 'Failed'; }
      );
      setTimeout(function () { button.textContent = 'Copy'; }, 1500);
    });

    pre.appendChild(button);
  }

  function init() {
    var blocks = document.querySelectorAll('pre');
    for (var i = 0; i < blocks.length; i++) addButton(blocks[i]);
  }

  if (typeof document !== 'undefined') {
    // The script may be injected after the document has already parsed.
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { copyableText: copyableText };
  }
})();

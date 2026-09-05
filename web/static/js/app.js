(function () {
  "use strict";

  document.querySelectorAll(".chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      var input = document.getElementById("text-input");
      if (input) input.value = chip.dataset.fill || chip.textContent;
      if (input) input.focus();
    });
  });

  var form = document.getElementById("analyze-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      var textarea = document.getElementById("text-input");
      if (textarea && !textarea.value.trim()) {
        e.preventDefault();
        textarea.focus();
        textarea.style.borderColor = "#dc2626";
        setTimeout(function () {
          textarea.style.borderColor = "";
        }, 2000);
        return;
      }

      var btn = document.getElementById("analyze-btn");
      var label = btn.querySelector(".btn-label");
      var spinner = btn.querySelector(".btn-spinner");
      btn.disabled = true;
      label.textContent = "Analyzing…";
      if (spinner) spinner.classList.remove("hidden");
    });

    // Ctrl+Enter keyboard shortcut to submit form
    var textarea = document.getElementById("text-input");
    if (textarea) {
      textarea.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
          e.preventDefault();
          form.submit();
        }
      });
    }
  }
})();

function copyJson(button) {
  var pre = document.getElementById("json-output");
  if (!pre) return;

  var text = pre.textContent;
  navigator.clipboard.writeText(text).then(function () {
    var originalText = button.textContent;
    button.textContent = "Copied!";
    button.disabled = true;
    setTimeout(function () {
      button.textContent = originalText;
      button.disabled = false;
    }, 2000);
  }).catch(function () {
    // Fallback for older browsers
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);

    var originalText = button.textContent;
    button.textContent = "Copied!";
    button.disabled = true;
    setTimeout(function () {
      button.textContent = originalText;
      button.disabled = false;
    }, 2000);
  });
}
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
    form.addEventListener("submit", function () {
      var btn = document.getElementById("analyze-btn");
      var label = btn.querySelector(".btn-label");
      var spinner = btn.querySelector(".btn-spinner");
      btn.disabled = true;
      label.textContent = "Analyzing…";
      if (spinner) spinner.classList.remove("hidden");
    });
  }
})();
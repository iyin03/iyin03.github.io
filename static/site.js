// Small interface behaviors that run for everyone, motion or not.
(function () {
  // Copy email: shown only where the clipboard API exists; the mailto link
  // beside it always works.
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    if (!navigator.clipboard) return;
    btn.hidden = false;
    var status = btn.parentNode.querySelector(".copy-status");
    var timer;
    btn.addEventListener("click", function () {
      navigator.clipboard.writeText(btn.dataset.copy).then(function () {
        btn.textContent = "Copied";
        if (status) status.textContent = "Email address copied";
        clearTimeout(timer);
        timer = setTimeout(function () {
          btn.textContent = "Copy email";
          if (status) status.textContent = "";
        }, 2000);
      });
    });
  });
})();

document.addEventListener("DOMContentLoaded", function () {
  // Mobile sidebar drawer
  var sidebar = document.querySelector(".sidebar");
  var backdrop = document.querySelector(".sidebar-backdrop");
  if (sidebar && !backdrop) {
    backdrop = document.createElement("div");
    backdrop.className = "sidebar-backdrop";
    document.body.appendChild(backdrop);
  }
  function setSidebar(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("open", open);
    if (backdrop) backdrop.classList.toggle("show", open);
    document.body.style.overflow = open ? "hidden" : "";
  }
  document.querySelectorAll(".sidebar-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setSidebar(!sidebar.classList.contains("open"));
    });
  });
  if (backdrop) {
    backdrop.addEventListener("click", function () { setSidebar(false); });
  }
  document.querySelectorAll(".sidebar .nav-item").forEach(function (item) {
    item.addEventListener("click", function () { setSidebar(false); });
  });
  window.addEventListener("resize", function () {
    if (window.innerWidth >= 992) setSidebar(false);
  });

  // Auto-dismiss flash messages after a few seconds
  document.querySelectorAll(".alert-dismissible").forEach(function (alert) {
    setTimeout(function () {
      alert.classList.remove("show");
      setTimeout(function () { alert.remove(); }, 300);
    }, 4500);
  });

  // Dropzone file-input feedback + client-side size check
  document.querySelectorAll(".dropzone input[type=file]").forEach(function (input) {
    input.addEventListener("change", function () {
      var dz = input.closest(".dropzone");
      var label = dz.querySelector(".dz-label");
      if (input.files && input.files.length) {
        var file = input.files[0];
        var maxMb = parseFloat(input.dataset.maxSizeMb || "1") || 1;
        if (file.size > maxMb * 1024 * 1024) {
          label.textContent = "Too large! Max " + maxMb + " MB (" + (file.size / 1048576).toFixed(2) + " MB)";
          dz.classList.add("has-file", "too-large");
          input.setCustomValidity("File is larger than " + maxMb + " MB");
        } else {
          label.textContent = file.name;
          dz.classList.add("has-file");
          dz.classList.remove("too-large");
          input.setCustomValidity("");
        }
      } else {
        label.textContent = "Click to choose a PDF resume";
        dz.classList.remove("has-file", "too-large");
        input.setCustomValidity("");
      }
    });
  });

  // Confirm dialogs for destructive forms
  document.querySelectorAll("form.confirm-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var msg = form.dataset.confirm || "Are you sure?";
      if (!window.confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});

(function () {
  // Finds all elements with .countdown[data-start="ISO8601"] and ticks them once per second.
  function pad(n) { return String(n).padStart(2, "0"); }

  function tick(el) {
    const iso = el.getAttribute("data-start");
    if (!iso) return;
    const start = new Date(iso);
    const now = new Date();
    let diff = Math.max(0, start - now);

    const s = Math.floor(diff / 1000) % 60;
    const m = Math.floor(diff / (1000 * 60)) % 60;
    const h = Math.floor(diff / (1000 * 60 * 60)) % 24;
    const d = Math.floor(diff / (1000 * 60 * 60 * 24));

    const out = el.querySelector(".cd-out");
    if (!out) return;
    if (diff <= 0) {
      out.textContent = "Live now";
      return;
    }
    out.textContent = `${d}d ${pad(h)}h ${pad(m)}m ${pad(s)}s`;
  }

  function start() {
    const els = Array.from(document.querySelectorAll(".countdown[data-start]"));
    if (!els.length) return;
    els.forEach(el => tick(el));
    setInterval(() => els.forEach(el => tick(el)), 1000);
  }

  if (document.readyState !== "loading") start();
  else document.addEventListener("DOMContentLoaded", start);
})();

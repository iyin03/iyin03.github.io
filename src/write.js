// The site's one animation: the name is written stroke by stroke, then the seal is pressed.
// Inlined into the home page. The glyphs start hidden only when motion is welcome
// (see styles.css); masks are attached just for the writing and removed after,
// because masked SVG is expensive to repaint while the page scrolls.
(function () {
  if (!window.matchMedia("(prefers-reduced-motion: no-preference)").matches) return;
  var svg = document.querySelector(".brush-svg");
  var seal = document.querySelector(".seal");
  if (!svg) return;
  if (!svg.animate) return done();

  var TOTAL = 2300;      // ms of brushwork across the whole name
  var LIFT = 70;         // pause between strokes, as the brush lifts
  var NEXT_CHAR = 220;   // pause before the next character
  var START = 300;

  var masked = svg.querySelectorAll("[data-mask]");
  masked.forEach(function (u) { u.setAttribute("mask", u.dataset.mask); });
  svg.classList.add("writing");

  var strokes = svg.querySelectorAll(".stroke");
  var totalLen = 0;
  strokes.forEach(function (s) { totalLen += +s.dataset.len; });

  // Mask polylines live in <defs>, one mask per character, in stroke order.
  var t = START;
  svg.querySelectorAll("mask").forEach(function (mask, ci) {
    if (ci) t += NEXT_CHAR;
    mask.querySelectorAll(".stroke").forEach(function (s) {
      var d = Math.max(110, (+s.dataset.len / totalLen) * TOTAL);
      s.animate(
        [
          { opacity: 1, strokeDashoffset: 1 },
          { opacity: 1, strokeDashoffset: 0 }
        ],
        { duration: d, delay: t, easing: "cubic-bezier(.35,0,.25,1)", fill: "forwards" }
      );
      t += d + LIFT;
    });
  });

  // Let the ink settle into the edges the strokes missed, then press the seal.
  var last;
  svg.querySelectorAll(".settle").forEach(function (g) {
    last = g.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 380, delay: t, easing: "ease-out", fill: "forwards" });
  });
  if (seal) {
    seal.animate(
      [
        { opacity: 0, transform: "scale(1.08)" },
        { opacity: 1, transform: "scale(1)" }
      ],
      { duration: 220, delay: t + 260, easing: "cubic-bezier(.2,.8,.3,1)", fill: "both" }
    ).onfinish = done;
  } else if (last) {
    last.onfinish = done;
  }

  function done() {
    masked.forEach(function (u) { u.removeAttribute("mask"); });
    svg.classList.remove("writing");
    svg.classList.add("written");
    if (seal) seal.classList.add("pressed");
    document.documentElement.dataset.written = "";
    document.dispatchEvent(new Event("brush:written"));
  }
})();

// Motion: Lenis smooth scrolling, section markers brushed on as each page opens,
// and the Vanta ink-wash fog behind the home page name.
// Nothing here runs for visitors who prefer reduced motion, and nothing hides
// content until this script has started, so the page is fully readable without it.
(function () {
  if (!window.gsap || !window.ScrollTrigger) return;
  if (!window.matchMedia("(prefers-reduced-motion: no-preference)").matches) return;

  gsap.registerPlugin(ScrollTrigger);

  // Smooth scrolling: Lenis eases wheel input toward its target. It runs on GSAP's
  // ticker so ScrollTrigger always reads the same position Lenis is drawing. The
  // easing is exponential with a fixed duration, so reversing direction mid-glide
  // (say, at the bottom of a page) retargets smoothly instead of snapping.
  // Touch keeps native momentum scrolling, which phones already do well.
  if (window.Lenis) {
    var lenis = new Lenis({
      duration: 1.1,
      easing: function (t) { return Math.min(1, 1.001 - Math.pow(2, -10 * t)); },
      smoothWheel: true,
      wheelMultiplier: 0.9,
      syncTouch: false,
      anchors: { offset: -16 },
      autoRaf: false
    });
    window.lenis = lenis;
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add(function (time) { lenis.raf(time * 1000); });
    gsap.ticker.lagSmoothing(0);

    // Keep the skip link moving keyboard focus, not just the view.
    var skip = document.querySelector(".skip");
    var main = document.getElementById("main");
    if (skip && main) {
      skip.addEventListener("click", function (e) {
        e.preventDefault();
        main.setAttribute("tabindex", "-1");
        main.focus({ preventScroll: true });
        lenis.scrollTo(main, { immediate: true });
      });
    }
  }

  var mm = gsap.matchMedia();

  // 1. Section markers are brushed on, one character at a time, in reading
  //    direction: top to bottom in the vertical rail, left to right on phones.
  mm.add(
    { vertical: "(min-width: 40.0625rem)", horizontal: "(max-width: 40rem)" },
    function (ctx) {
      var hidden = ctx.conditions.vertical ? "inset(0 0 100% 0)" : "inset(0 100% 0 0)";
      gsap.utils.toArray(".marker").forEach(function (marker) {
        gsap.fromTo(
          marker.querySelectorAll(".mk"),
          { clipPath: hidden, opacity: 0.35 },
          {
            clipPath: "inset(0 0 0% 0)",
            opacity: 1,
            duration: 0.45,
            ease: "power2.inOut",
            stagger: 0.28,
            scrollTrigger: { trigger: marker, start: "top 85%", once: true }
          }
        );
      });
    }
  );

  // 2. Ink-wash fog behind the hero (Vanta + three.js, ~150 KB gzipped). Wide
  //    screens only, loaded after the name is written so it never delays the
  //    page, and skipped on data-saver or without WebGL. Vanta stops drawing
  //    while the hero is scrolled out of view.
  var fogEl = document.querySelector(".ink-fog");
  var wide = window.matchMedia("(min-width: 60rem)");
  var saveData = navigator.connection && navigator.connection.saveData;
  if (fogEl && wide.matches && !saveData && hasWebGL()) {
    if ("written" in document.documentElement.dataset) startFog();
    else document.addEventListener("brush:written", startFog, { once: true });
  }

  function startFog() {
    load("/vendor/three.r134.min.js", function () {
      load("/vendor/vanta.fog.min.js", function () {
        if (!window.VANTA || !VANTA.FOG) return;
        VANTA.FOG({
          el: fogEl,
          THREE: window.THREE,
          mouseControls: true,
          touchControls: false,
          gyroControls: false,
          highlightColor: 0xffffff,
          midtoneColor: 0xd0d3c7,
          lowlightColor: 0xa8ad9e,
          baseColor: 0xffffff,
          blurFactor: 0.75,
          speed: 0.7,
          zoom: 0.7
        });
        requestAnimationFrame(function () { fogEl.classList.add("is-on"); });
      });
    });
  }

  function load(src, onload) {
    var s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = onload;
    document.head.appendChild(s);
  }

  function hasWebGL() {
    try {
      var c = document.createElement("canvas");
      return !!(c.getContext("webgl") || c.getContext("experimental-webgl"));
    } catch (e) {
      return false;
    }
  }
})();

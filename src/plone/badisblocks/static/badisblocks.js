/* plone.badisblocks — Classic UI block behaviour.
 *
 * Progressive enhancement for the carousel block (@type carousel). The block is
 * server-rendered as a horizontal scroll-snap track; Volto drives it with JS
 * (Embla) and so do we here. This wires the prev/next arrows and the dot
 * navigation to the scrollable viewport, marks the active dot, and disables the
 * arrows at the ends. The wrapper gets an `is-enhanced` class so the controls
 * are only shown once JS has taken over (without JS the viewport stays
 * scrollable/swipeable with a visible scrollbar — see badisblocks.css).
 */
(function () {
  "use strict";

  function setupCarousel(wrapper) {
    var viewport = wrapper.querySelector(".carousel-viewport");
    var container = wrapper.querySelector(".carousel-container");
    if (!viewport || !container) {
      return;
    }
    var slides = Array.prototype.slice.call(container.children);
    if (!slides.length) {
      return;
    }
    var prev = wrapper.querySelector(".carousel-button-prev");
    var next = wrapper.querySelector(".carousel-button-next");
    var dots = Array.prototype.slice.call(wrapper.querySelectorAll(".carousel-dot"));

    function step() {
      // Distance between consecutive slide starts (slide width + gap).
      if (slides.length > 1) {
        return slides[1].offsetLeft - slides[0].offsetLeft;
      }
      return slides[0].offsetWidth || 1;
    }

    function currentIndex() {
      return Math.round(viewport.scrollLeft / step());
    }

    function scrollToIndex(index) {
      var bounded = Math.max(0, Math.min(slides.length - 1, index));
      viewport.scrollTo({ left: bounded * step(), behavior: "smooth" });
    }

    function update() {
      var index = currentIndex();
      var maxScroll = container.scrollWidth - viewport.clientWidth;
      if (prev) {
        prev.disabled = viewport.scrollLeft <= 1;
      }
      if (next) {
        next.disabled = viewport.scrollLeft >= maxScroll - 1;
      }
      dots.forEach(function (dot, i) {
        var active = i === index;
        dot.classList.toggle("is-active", active);
        dot.setAttribute("aria-current", active ? "true" : "false");
      });
    }

    if (prev) {
      prev.addEventListener("click", function () {
        scrollToIndex(currentIndex() - 1);
      });
    }
    if (next) {
      next.addEventListener("click", function () {
        scrollToIndex(currentIndex() + 1);
      });
    }
    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function () {
        scrollToIndex(i);
      });
    });

    var frame;
    viewport.addEventListener("scroll", function () {
      if (frame) {
        window.cancelAnimationFrame(frame);
      }
      frame = window.requestAnimationFrame(update);
    });
    window.addEventListener("resize", update);

    wrapper.classList.add("is-enhanced");
    update();
  }

  function init() {
    var wrappers = document.querySelectorAll(".block.carousel .carousel-wrapper");
    Array.prototype.forEach.call(wrappers, setupCarousel);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

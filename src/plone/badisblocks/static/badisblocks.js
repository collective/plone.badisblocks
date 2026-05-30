/* plone.badisblocks — Classic UI block behaviour.
 *
 * Progressive enhancement for the carousel (@type carousel) and slider
 * (@type slider) blocks. Both are server-rendered as a horizontal scroll-snap
 * track; Volto drives them with JS (Embla) and so do we here. `setupScroller`
 * wires the prev/next arrows and the dot navigation to the scrollable viewport,
 * marks the active dot, and disables the arrows at the ends. The wrapper gets an
 * `is-enhanced` class so the controls are only shown once JS has taken over
 * (without JS the viewport stays scrollable/swipeable with a visible scrollbar —
 * see badisblocks.css).
 *
 * Progressive enhancement for the event calendar block (@type eventCalendar):
 * the filter is a plain GET form that works without JS (full page reload). When
 * JS is on, we intercept submit/change/input and instead fetch the block view
 * standalone (`<context>/@@block-eventCalendar?block_id=…&event_from=…`) and swap
 * the `.event-calendar-results` fragment in place — so all the date/search logic
 * stays server-side and there's a single source of truth.
 *
 * Progressive enhancement for the search block (@type search): same pattern as
 * the event calendar. The faceted filter is a plain GET form (text input, facet
 * <select>s, sort) that works without JS; when JS is on we fetch the block view
 * standalone (`<context>/@@block-search?block_id=…&SearchableText=…`) and swap
 * the `.search-block-results` fragment in place.
 */
(function () {
  "use strict";

  // Shared scroll-snap enhancement for the carousel (@type carousel) and slider
  // (@type slider) blocks. Both server-render their slides into a horizontally
  // scrollable track; this wires the prev/next arrows and dot navigation, marks
  // the active dot, and disables the arrows at the ends. ``prefix`` selects the
  // block's class names (e.g. "carousel" -> .carousel-viewport, .carousel-dot …).
  function setupScroller(wrapper, prefix) {
    var viewport = wrapper.querySelector("." + prefix + "-viewport");
    var container = wrapper.querySelector("." + prefix + "-container");
    if (!viewport || !container) {
      return;
    }
    var slides = Array.prototype.slice.call(container.children);
    if (!slides.length) {
      return;
    }
    var prev = wrapper.querySelector("." + prefix + "-button-prev");
    var next = wrapper.querySelector("." + prefix + "-button-next");
    var dots = Array.prototype.slice.call(
      wrapper.querySelectorAll("." + prefix + "-dot")
    );

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

  var EVENT_FILTER_FIELDS = ["event_from", "event_to", "event_search"];

  function setupEventCalendar(block) {
    var form = block.querySelector(".event-calendar-search");
    var results = block.querySelector(".event-calendar-results");
    var blockUrl = block.getAttribute("data-block-url");
    var blockId = block.getAttribute("data-block-id");
    if (!form || !results || !blockUrl) {
      return;
    }

    var controller;

    function syncLocation() {
      // Reflect the active filter in the URL bar so it stays shareable and the
      // no-JS GET fallback keeps working on reload.
      try {
        var pageUrl = new URL(window.location.href);
        EVENT_FILTER_FIELDS.forEach(function (name) {
          var field = form.elements[name];
          var value = field ? field.value : "";
          if (value) {
            pageUrl.searchParams.set(name, value);
          } else {
            pageUrl.searchParams.delete(name);
          }
        });
        window.history.replaceState({}, "", pageUrl);
      } catch (e) {
        /* history/URL unsupported — ignore, results still update */
      }
    }

    function run() {
      var params = new URLSearchParams(new FormData(form));
      if (blockId) {
        params.set("block_id", blockId);
      }
      if (controller) {
        controller.abort();
      }
      controller = new AbortController();
      block.classList.add("is-loading");
      fetch(blockUrl + "?" + params.toString(), {
        signal: controller.signal,
        headers: { "X-Requested-With": "fetch" },
        credentials: "same-origin",
      })
        .then(function (response) {
          return response.text();
        })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, "text/html");
          var fresh = doc.querySelector(".event-calendar-results");
          if (fresh) {
            results.replaceWith(fresh);
            results = block.querySelector(".event-calendar-results");
          }
          block.classList.remove("is-loading");
          syncLocation();
        })
        .catch(function (error) {
          if (error && error.name === "AbortError") {
            return;
          }
          block.classList.remove("is-loading");
        });
    }

    var timer;
    function schedule() {
      window.clearTimeout(timer);
      timer = window.setTimeout(run, 300);
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      window.clearTimeout(timer);
      run();
    });
    form.addEventListener("change", schedule);
    var search = form.querySelector('input[type="search"]');
    if (search) {
      search.addEventListener("input", schedule);
    }
    var reset = form.querySelector(".reset-button");
    if (reset) {
      reset.addEventListener("click", function (event) {
        event.preventDefault();
        EVENT_FILTER_FIELDS.forEach(function (name) {
          if (form.elements[name]) {
            form.elements[name].value = "";
          }
        });
        run();
      });
    }

    block.classList.add("is-enhanced");
  }

  function setupSearch(block) {
    var form = block.querySelector(".search-block-form");
    var results = block.querySelector(".search-block-results");
    var blockUrl = block.getAttribute("data-block-url");
    var blockId = block.getAttribute("data-block-id");
    if (!form || !results || !blockUrl) {
      return;
    }

    var controller;

    function syncLocation() {
      // Reflect the active filter in the URL bar so it stays shareable and the
      // no-JS GET fallback keeps working on reload.
      try {
        var pageUrl = new URL(window.location.href);
        var names = {};
        Array.prototype.forEach.call(form.elements, function (el) {
          if (el.name) {
            names[el.name] = true;
          }
        });
        Object.keys(names).forEach(function (name) {
          pageUrl.searchParams.delete(name);
        });
        new FormData(form).forEach(function (value, name) {
          if (value) {
            pageUrl.searchParams.append(name, value);
          }
        });
        window.history.replaceState({}, "", pageUrl);
      } catch (e) {
        /* history/URL unsupported — ignore, results still update */
      }
    }

    function run() {
      var params = new URLSearchParams(new FormData(form));
      if (blockId) {
        params.set("block_id", blockId);
      }
      if (controller) {
        controller.abort();
      }
      controller = new AbortController();
      block.classList.add("is-loading");
      fetch(blockUrl + "?" + params.toString(), {
        signal: controller.signal,
        headers: { "X-Requested-With": "fetch" },
        credentials: "same-origin",
      })
        .then(function (response) {
          return response.text();
        })
        .then(function (html) {
          var doc = new DOMParser().parseFromString(html, "text/html");
          var fresh = doc.querySelector(".search-block-results");
          if (fresh) {
            results.replaceWith(fresh);
            results = block.querySelector(".search-block-results");
          }
          block.classList.remove("is-loading");
          syncLocation();
        })
        .catch(function (error) {
          if (error && error.name === "AbortError") {
            return;
          }
          block.classList.remove("is-loading");
        });
    }

    var timer;
    function schedule() {
      window.clearTimeout(timer);
      timer = window.setTimeout(run, 300);
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      window.clearTimeout(timer);
      run();
    });
    form.addEventListener("change", schedule);
    var search = form.querySelector('input[type="search"]');
    if (search) {
      search.addEventListener("input", schedule);
    }
    var reset = form.querySelector(".reset-button");
    if (reset) {
      reset.addEventListener("click", function (event) {
        event.preventDefault();
        form.reset();
        run();
      });
    }

    block.classList.add("is-enhanced");
  }

  function init() {
    var carousels = document.querySelectorAll(".block.carousel .carousel-wrapper");
    Array.prototype.forEach.call(carousels, function (wrapper) {
      setupScroller(wrapper, "carousel");
    });
    var sliders = document.querySelectorAll(".block.slider .slider-wrapper");
    Array.prototype.forEach.call(sliders, function (wrapper) {
      setupScroller(wrapper, "slider");
    });
    var calendars = document.querySelectorAll(".block.eventCalendar[data-event-calendar]");
    Array.prototype.forEach.call(calendars, setupEventCalendar);
    var searchBlocks = document.querySelectorAll(".block.search[data-search-block]");
    Array.prototype.forEach.call(searchBlocks, setupSearch);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

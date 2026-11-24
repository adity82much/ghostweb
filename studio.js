/* Native adaptations of RareUI's Scroll Progress, Step Player and Animated
   Counter. See README for references. No React or animation runtime required. */
(function () {
  "use strict";

  var motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var $ = function (id) { return document.getElementById(id); };

  function animate(element, frames, options) {
    if (motion.matches || !element.animate) { return; }
    element.getAnimations().forEach(function (animation) { animation.cancel(); });
    element.animate(frames, options || {duration: 320, easing: "cubic-bezier(.22,1,.36,1)"});
  }

  /* File tabs lift a new manuscript into view. Existing tab semantics and
     keyboard behavior stay in index.html; this only supplies the transition. */
  var panels = Array.prototype.slice.call(document.querySelectorAll(".panel"));
  var previousPanel = 0;
  var pageObserver = new MutationObserver(function (records) {
    records.forEach(function (record) {
      var panel = record.target;
      if (panel.hidden) { return; }
      var next = panels.indexOf(panel);
      if (next === previousPanel) { return; }
      var direction = next > previousPanel ? 1 : -1;
      animate(panel, [
        {opacity: .55, transform: "translateX(" + direction * 12 + "px)"},
        {opacity: 1, transform: "translateX(0)"}
      ]);
      var preview = panel.querySelector(".mock, .serp");
      if (preview) {
        animate(preview, [
          {transform: "translateY(10px) rotate(" + direction * .8 + "deg)"},
          {transform: "translateY(0) rotate(0)"}
        ], {duration: 480, easing: "cubic-bezier(.22,1,.36,1)"});
      }
      previousPanel = next;
    });
  });
  panels.forEach(function (panel) {
    pageObserver.observe(panel, {attributes: true, attributeFilter: ["hidden"]});
  });

  /* Each digit has one real text node; the departing face is a CSS pseudo-
     element. Text remains copyable and assistive technology gets one value. */
  function counter(element) {
    var previous = element.textContent.trim();
    var visible = false;

    function paint(value, from, roll) {
      if (!/^\d+%?$/.test(value)) { return; }
      var width = value.replace(/\D/g, "").length;
      var old = from.replace(/\D/g, "").padStart(width, "0").slice(-width);
      var position = 0;
      element.classList.add("rolling-counter");
      element.setAttribute("role", "img");
      element.setAttribute("aria-label", value);
      var fragment = document.createDocumentFragment();
      value.split("").forEach(function (character) {
        if (!/\d/.test(character)) {
          fragment.appendChild(document.createTextNode(character));
          return;
        }
        var digit = document.createElement("span");
        digit.className = "rolling-digit";
        digit.setAttribute("aria-hidden", "true");
        var before = old.charAt(position++) || "0";
        digit.setAttribute("data-before", before);
        var face = document.createElement("span");
        face.className = "digit-face";
        face.textContent = character;
        digit.appendChild(face);
        if (roll && !motion.matches && before !== character) {
          digit.classList.add("is-rolling");
          digit.style.setProperty("--digit-delay", position * 24 + "ms");
          if (+value.replace(/\D/g, "") < +from.replace(/\D/g, "")) {
            digit.classList.add("roll-down");
          }
        }
        fragment.appendChild(digit);
      });
      element.replaceChildren(fragment);
    }

    paint(previous, previous, false);
    new MutationObserver(function () {
      var value = element.textContent.trim();
      if (value === previous) { return; }
      var from = previous;
      previous = value;
      paint(value, from, visible);
    }).observe(element, {childList: true, subtree: true, characterData: true});

    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          visible = true;
          paint(previous, "0", true);
          element.setAttribute("data-counter-visible", "true");
          observer.disconnect();
        }
      }, {threshold: .8});
      observer.observe(element);
    } else {
      visible = true;
      element.setAttribute("data-counter-visible", "true");
    }
  }
  document.querySelectorAll(".score-top b, #vWords, #vSent").forEach(counter);

  /* A small reading-progress pill unfolds into the actual chapter index. */
  var sources = Array.prototype.slice.call(document.querySelectorAll("#navLinks [data-goto]"));
  var chapters = sources.map(function (button) {
    return {id: button.getAttribute("data-goto"), label: button.textContent, element: $(button.getAttribute("data-goto"))};
  });
  var index = document.createElement("aside");
  index.className = "reading-index";
  index.id = "readingIndex";
  index.setAttribute("aria-label", "Reading navigation");
  index.hidden = true;
  index.innerHTML = '<button type="button" class="reading-toggle" id="readingToggle" aria-expanded="false" aria-controls="readingChapters">' +
    '<svg viewBox="0 0 24 24" aria-hidden="true"><circle class="reading-ring-track" cx="12" cy="12" r="9"/>' +
    '<circle class="reading-ring" cx="12" cy="12" r="9" pathLength="100"/></svg>' +
    '<span id="readingLabel">Contents</span><span class="reading-percent" id="readingPercent">0%</span>' +
    '<span class="reading-cross" aria-hidden="true">+</span></button>' +
    '<nav id="readingChapters" aria-label="Chapter index" hidden></nav>';
  document.body.appendChild(index);
  var toggle = $("readingToggle");
  var list = $("readingChapters");
  var ring = index.querySelector(".reading-ring");
  var label = $("readingLabel");
  var percent = $("readingPercent");
  var links = chapters.map(function (chapter, i) {
    var button = document.createElement("button");
    button.type = "button";
    button.setAttribute("data-goto", chapter.id);
    var number = document.createElement("span");
    number.className = "chapter-number";
    number.textContent = String(i + 1).padStart(2, "0");
    var title = document.createElement("span");
    title.textContent = chapter.label;
    button.appendChild(number);
    button.appendChild(title);
    list.appendChild(button);
    return button;
  });

  function openIndex(open, restoreFocus) {
    if (restoreFocus) { toggle.focus({preventScroll: true}); }
    toggle.setAttribute("aria-expanded", String(open));
    index.classList.toggle("is-open", open);
    list.hidden = !open;
    if (open) {
      index.hidden = false;
      animate(list, [{opacity: 0, transform: "translateY(8px)"}, {opacity: 1, transform: "translateY(0)"}]);
    }
  }
  toggle.addEventListener("click", function () {
    openIndex(toggle.getAttribute("aria-expanded") !== "true", false);
  });
  list.addEventListener("click", function (event) {
    if (event.target.closest("[data-goto]")) { openIndex(false, true); }
  });
  index.addEventListener("keydown", function (event) {
    if (event.key === "Escape") { openIndex(false, true); }
    var at = links.indexOf(document.activeElement);
    var next;
    if (event.key === "ArrowDown") { next = links[(at + 1) % links.length]; }
    if (event.key === "ArrowUp") { next = links[(at - 1 + links.length) % links.length]; }
    if (event.key === "Home") { next = links[0]; }
    if (event.key === "End") { next = links[links.length - 1]; }
    if (next) {
      event.preventDefault();
      openIndex(true, false);
      next.focus();
    }
  });
  document.addEventListener("pointerdown", function (event) {
    if (!index.contains(event.target)) { openIndex(false, false); }
  });
  document.addEventListener("focusin", function (event) {
    if (!index.contains(event.target)) { openIndex(false, false); }
    queueIndex();
  });
  var queued = false;
  function updateIndex() {
    var height = document.documentElement.scrollHeight - innerHeight;
    var progress = height > 0 ? Math.max(0, Math.min(100, Math.round(scrollY / height * 100))) : 0;
    var active = -1;
    chapters.forEach(function (chapter, i) {
      if (chapter.element.getBoundingClientRect().top <= 120) { active = i; }
    });
    var current = active < 0 ? "Contents" : chapters[active].label;
    if (label.textContent !== current) {
      label.textContent = current;
      animate(label, [{opacity: .3, transform: "translateY(5px)"}, {opacity: 1, transform: "translateY(0)"}]);
    }
    percent.textContent = progress + "%";
    ring.style.strokeDashoffset = 100 - progress;
    toggle.setAttribute("aria-label", "Page index, " + progress + "% read, " + current);
    links.forEach(function (button, i) {
      if (i === active) { button.setAttribute("aria-current", "location"); }
      else { button.removeAttribute("aria-current"); }
    });
    var editing = document.activeElement && document.activeElement.closest(".form-card");
    index.hidden = !!editing || (scrollY < 200 && toggle.getAttribute("aria-expanded") !== "true");
    queued = false;
  }
  function queueIndex() {
    if (!queued) { queued = true; requestAnimationFrame(updateIndex); }
  }
  window.addEventListener("scroll", queueIndex, {passive: true});
  window.addEventListener("resize", queueIndex);
  if ("ResizeObserver" in window) { new ResizeObserver(queueIndex).observe(document.body); }
  updateIndex();

  /* Reader-controlled process player: no autoplay, no moving content, and no
     audio. The original four cards remain visible and can always be skimmed. */
  var player = $("processPlayer");
  var steps = Array.prototype.slice.call(document.querySelectorAll(".step"));
  player.hidden = false;
  player.setAttribute("data-playing", "false");
  player.innerHTML = '<span class="process-player-label" id="processPlayerLabel"></span>' +
    '<div class="process-transport"><div class="process-track" role="group" aria-label="Process steps"></div>' +
    '<button type="button" class="process-control" id="processControl" aria-label="Play process walkthrough">' +
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path/></svg></button></div>';
  var track = player.querySelector(".process-track");
  var control = $("processControl");
  var glyph = control.querySelector("path");
  var currentStep = 0;
  var playing = false;
  var finished = false;
  var elapsed = 0;
  var last = null;
  var frame = 0;
  var duration = 4500;
  var stepButtons = steps.map(function (step, i) {
    step.id = "process-step-" + i;
    var button = document.createElement("button");
    button.type = "button";
    button.className = "process-seek";
    button.setAttribute("aria-label", "Step " + (i + 1) + ": " + step.querySelector("h3").textContent);
    button.setAttribute("aria-controls", step.id);
    button.innerHTML = '<span class="process-dot" aria-hidden="true"><i></i></span>';
    button.addEventListener("click", function () { selectStep(i); });
    button.addEventListener("keydown", function (event) {
      var next;
      if (event.key === "ArrowRight") { next = (i + 1) % steps.length; }
      if (event.key === "ArrowLeft") { next = (i - 1 + steps.length) % steps.length; }
      if (event.key === "Home") { next = 0; }
      if (event.key === "End") { next = steps.length - 1; }
      if (next !== undefined) { event.preventDefault(); selectStep(next); stepButtons[next].focus(); }
    });
    track.appendChild(button);
    return button;
  });

  function renderPlayer() {
    player.setAttribute("data-playing", String(playing));
    player.setAttribute("data-finished", String(finished));
    $("processPlayerLabel").textContent = steps[currentStep].querySelector("h3").textContent;
    control.setAttribute("aria-label", finished ? "Replay process walkthrough" : playing ? "Pause process walkthrough" : "Play process walkthrough");
    glyph.setAttribute("d", finished ? "M20 7v5h-5M20 12a8 8 0 1 0-2 5" : playing ? "M8 6v12M16 6v12" : "M9 6l9 6-9 6z");
    stepButtons.forEach(function (button, i) {
      button.setAttribute("data-state", i < currentStep ? "past" : i === currentStep ? "active" : "pending");
      if (i === currentStep) { button.setAttribute("aria-current", "step"); }
      else { button.removeAttribute("aria-current"); }
      steps[i].classList.toggle("is-current", i === currentStep);
    });
    updateFill();
  }
  function updateFill() {
    stepButtons[currentStep].querySelector("i").style.transform = "scaleX(" + elapsed / duration + ")";
  }
  function selectStep(i) {
    currentStep = i;
    elapsed = 0;
    last = null;
    finished = false;
    renderPlayer();
  }
  function pause() {
    playing = false;
    last = null;
    cancelAnimationFrame(frame);
    renderPlayer();
  }
  function tick(now) {
    if (!playing) { return; }
    if (last !== null) { elapsed = Math.min(duration, elapsed + now - last); }
    last = now;
    updateFill();
    if (elapsed >= duration) {
      if (currentStep === steps.length - 1) {
        finished = true;
        pause();
        return;
      }
      selectStep(currentStep + 1);
    }
    frame = requestAnimationFrame(tick);
  }
  control.addEventListener("click", function () {
    if (playing) { pause(); return; }
    if (finished) { selectStep(0); }
    playing = true;
    last = null;
    renderPlayer();
    frame = requestAnimationFrame(tick);
  });
  document.addEventListener("visibilitychange", function () { if (document.hidden) { pause(); } });
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting && playing) { pause(); }
    }).observe($("process"));
  }
  motion.addEventListener("change", function () { if (motion.matches) { pause(); } });
  renderPlayer();
})();

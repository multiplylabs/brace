// The clips and posters contain the reviewed crops and redactions.
(() => {
  const exists = (url) => fetch(url, { method: "HEAD", cache: "no-cache" }).then((r) => r.ok, () => false);
  for (const a of document.querySelectorAll("a[data-soon]")) {
    a.setAttribute("aria-disabled", "true");
    a.tabIndex = -1;
    if (!a.hasAttribute("data-probe")) continue;
    exists(a.getAttribute("href")).then((ok) => {
      if (!ok) return;
      a.removeAttribute("data-soon");
      a.removeAttribute("aria-disabled");
      a.removeAttribute("tabindex");
    });
  }

  const motion = matchMedia("(prefers-reduced-motion: reduce)");
  const hero = document.querySelector(".hero-bg");
  const visible = new Set();
  const loops = new Set();
  const autoPlays = (video) => video === hero || !motion.matches;
  const onScreen = new IntersectionObserver((entries) => {
    for (const { target, isIntersecting } of entries) {
      if (isIntersecting) visible.add(target); else visible.delete(target);
      if (isIntersecting && autoPlays(target) && !document.hidden) target.play().catch(() => {});
      else target.pause();
    }
  }, { threshold: 0.5 });
  const updatePlayback = () => {
    for (const video of loops) {
      if (autoPlays(video) && !document.hidden && visible.has(video)) video.play().catch(() => {});
      else video.pause();
    }
  };
  motion.addEventListener("change", updatePlayback);
  document.addEventListener("visibilitychange", updatePlayback);
  if (hero) {
    const playlist = hero.dataset.playlist?.trim().split(/\s+/) ?? [];
    if (playlist.length) {
      let clipIndex = 0;
      const selectClip = () => {
        const clip = playlist[clipIndex];
        hero.dataset.clip = clip;
        hero.poster = `assets/video/${clip}.jpg`;
        hero.src = `assets/video/${clip}.mp4`;
        hero.load();
      };
      hero.loop = false;
      selectClip();
      hero.addEventListener("ended", () => {
        clipIndex = (clipIndex + 1) % playlist.length;
        selectClip();
        if (!document.hidden && visible.has(hero)) hero.play().catch(() => {});
      });
    }
    loops.add(hero);
    onScreen.observe(hero);
  }

  const connectReferenceStages = (slot, video) => {
    const explainer = slot.closest("[data-reference-explainer]");
    if (!explainer) return;
    const stages = [...explainer.querySelectorAll(".transform-stages button")];
    const description = explainer.querySelector("[data-transform-description]");
    const diagram = explainer.querySelector(".method-figure");
    let active = null;
    const updateStage = () => {
      const current = stages.filter((button) => Number(button.dataset.time) <= video.currentTime).at(-1) ?? stages[0];
      if (current === active) return;
      active = current;
      for (const button of stages) {
        if (button === current) button.setAttribute("aria-current", "step");
        else button.removeAttribute("aria-current");
      }
      description.textContent = current.dataset.description;
      diagram.dataset.transformPanel = current.dataset.panel;
    };
    video.addEventListener("timeupdate", updateStage);
    video.addEventListener("seeking", updateStage);
    video.addEventListener("loadedmetadata", () => {
      for (const button of stages) button.disabled = false;
    });
    for (const button of stages) {
      button.addEventListener("click", () => {
        video.currentTime = Number(button.dataset.time);
        updateStage();
        video.play().catch(() => {});
      });
    }
    updateStage();
  };

  // A player is created when its slot comes within a screen of the viewport, not at page load:
  // twenty-odd clips probed and opened at once is what made the page slow to settle. The probe
  // for the clip and its poster run together, and the clip itself is not fetched until it is in
  // view (`preload="none"` with the poster shown), so the page's own weight is the posters.
  const mount = (slot) => {
    const base = `assets/video/${slot.dataset.video}`;
    Promise.all([exists(`${base}.mp4`), exists(`${base}.jpg`)]).then(([available, poster]) => {
      if (!available) {
        slot.querySelector(".label .caps").textContent = "Video unavailable";
        return;
      }
      const video = document.createElement("video");
      connectReferenceStages(slot, video);
      video.src = `${base}.mp4`;
      video.controls = true;
      video.playsInline = true;
      video.preload = poster ? "none" : "metadata";
      if (poster) video.poster = `${base}.jpg`;
      video.setAttribute("aria-label", slot.querySelector(".title-sm")?.textContent ?? "Robot demonstration");
      if (slot.hasAttribute("data-autoplay")) {
        video.muted = true;
        video.loop = true;
        loops.add(video);
        onScreen.observe(video);
      }
      slot.querySelector(".frame").replaceWith(video);
    });
  };
  const nearViewport = new IntersectionObserver((entries) => {
    for (const { target, isIntersecting } of entries) {
      if (!isIntersecting) continue;
      nearViewport.unobserve(target);
      mount(target);
    }
  }, { rootMargin: "100% 0px" });
  for (const slot of document.querySelectorAll("[data-video]")) nearViewport.observe(slot);

  const results = document.querySelector("[data-results-explorer]");
  if (results) {
    const setting = results.querySelector("#result-setting");
    const metric = results.querySelector("#result-metric");
    const write = (key, value) => { results.querySelector(`[data-result-${key}]`).textContent = value; };
    fetch("assets/data/results.json").then((response) => {
      if (!response.ok) throw new Error("Results data unavailable");
      return response.json();
    }).then(({ settings }) => {
      const update = () => {
        const selected = settings[setting.value];
        for (const option of metric.options) option.disabled = !selected.metrics[option.value];
        if (!selected.metrics[metric.value]) metric.value = "tracking";
        const comparison = selected.metrics[metric.value];
        const image = results.querySelector("[data-result-image]");
        results.querySelector("[data-result-mobile]").srcset = comparison.mobile_image;
        image.src = comparison.image;
        image.alt = comparison.alt;
        results.querySelector("[data-result-link]").href = comparison.image;
        write("title", comparison.title);
        write("direction", comparison.direction);
        write("setting-title", selected.title);
        write("condition", selected.condition);
        write("point", selected.point);
        write("ours", comparison.ours);
        write("baseline", comparison.baseline);
        write("baseline-value", comparison.baseline_value);
      };
      setting.addEventListener("change", update);
      metric.addEventListener("change", update);
      update();
      setting.disabled = metric.disabled = false;
    }).catch(() => {
      // The initial comparison and expandable full results still work without the data file.
      results.querySelector(".result-controls").hidden = true;
    });
  }
})();

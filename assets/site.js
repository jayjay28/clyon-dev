/* clyon.dev — the intro types the name; sections open without a reload.
   The cursor only shows while something is being typed, blinks where it
   stopped, then leaves. */
(() => {
  const d = document.documentElement, $ = id => document.getElementById(id);
  const site = $("site"), stage = $("stage"), out = $("out"), path = $("path"),
        menu = $("menu"), latest = $("latest"), content = $("content"), caret = $("caret");
  const TEXT = "clyon.dev", SECS = ["blogs", "life", "projects"];
  const RM = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const page = d.dataset.page;
  let isPost = page === "post" || page === "404";
  let current = page === "home" ? null : (d.dataset.sec || null);
  let seq = 0, introRunning = false;
  let visited = false;
  try { visited = localStorage.getItem("clyon-visited") === "1"; } catch (e) {}

  const wait = ms => new Promise(r => setTimeout(r, ms));
  const fontOf = el => parseFloat(getComputedStyle(el).fontSize);

  /* ---------- the cursor ---------- */
  function endRect(el) {
    const r = document.createRange(); r.selectNodeContents(el); r.collapse(false);
    const rs = r.getClientRects(), rect = rs.length ? rs[rs.length - 1] : r.getBoundingClientRect();
    return rect.height ? rect : el.getBoundingClientRect();
  }
  function caretAtEnd(el, glide) {
    const r = endRect(el), fs = fontOf(el);
    caret.classList.toggle("glide", !!glide);
    Object.assign(caret.style, { left: r.right + fs * .05 + "px", top: r.top + r.height / 2 - .475 * fs + "px", width: .55 * fs + "px", height: .95 * fs + "px" });
  }
  const caretOn = () => { caret.classList.remove("blink"); caret.classList.add("on"); };
  const caretOff = () => caret.classList.remove("blink", "on");
  function blinkThenLeave() {
    const me = seq;
    caretAtEnd(path.textContent ? path : out);
    caret.classList.add("on", "blink");
    setTimeout(() => { if (me === seq) caretOff(); }, 2100);
  }
  const paintName = n => {
    const s = TEXT.slice(0, n), i = s.indexOf(".");
    out.innerHTML = i < 0 ? s : `${s.slice(0, i)}<span class="dev">${s.slice(i)}</span>`;
  };
  async function typeInto(el, text, me, speed = 1) {
    for (const ch of text) {
      if (!RM) await wait((ch === "/" ? 220 : 60 + Math.random() * 90) * speed);
      if (me !== seq) return false;
      el.textContent += ch; caretAtEnd(el);
    }
    return true;
  }
  async function backspace(el, me) {
    while (el.textContent.length) {
      if (!RM) await wait(45);
      if (me !== seq) return false;
      el.textContent = el.textContent.slice(0, -1);
      caretAtEnd(el.textContent ? el : out);
    }
    return true;
  }

  /* ---------- intro (home only) ---------- */
  function finishIntro() {
    introRunning = false;
    paintName(TEXT.length); d.classList.add("typing-started");
    menu.classList.remove("in"); menu.classList.add("shown");
    if (latest) latest.classList.add("in");
  }
  async function intro(fast) {
    const me = ++seq, k = fast ? .5 : 1;
    introRunning = true;
    paintName(0); d.classList.add("typing-started");
    caretAtEnd(out); caretOn();
    await wait(RM ? 0 : 350 * k);
    for (let i = 0; i < TEXT.length; i++) {
      if (!RM) await wait((TEXT[i] === "." ? 380 : 70 + Math.random() * 110) * k);
      if (me !== seq) return;
      paintName(i + 1); caretAtEnd(out);
    }
    caret.classList.add("blink");
    await wait(RM ? 0 : 420 * k); if (me !== seq) return;
    void menu.offsetWidth; menu.classList.add("in");
    await wait(RM ? 0 : 900); if (me !== seq) return;
    if (latest) latest.classList.add("in");
    await wait(RM ? 0 : 800); if (me !== seq) return;
    caretOff(); introRunning = false;
    try { localStorage.setItem("clyon-visited", "1"); } catch (e) {}
  }
  function skip() { seq++; finishIntro(); blinkThenLeave(); }

  /* ---------- sections ---------- */
  function flip(change) {
    const els = [stage, menu], first = els.map(e => e.getBoundingClientRect());
    change();
    if (RM) return;
    els.forEach((e, i) => {
      const f = first[i], l = e.getBoundingClientRect(), s = f.width / l.width;
      e.animate([{ transformOrigin: "0 0", transform: `translate(${f.left - l.left}px,${f.top - l.top}px) scale(${s})` },
                 { transformOrigin: "0 0", transform: "none" }], { duration: 680, easing: "cubic-bezier(.2,.8,.2,1)" });
    });
  }
  const setActive = sec => menu.querySelectorAll("a[data-sec]").forEach(a => {
    const on = a.dataset.sec === sec; a.classList.toggle("on", on);
    on ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current");
  });
  function show(sec, delay) {
    setActive(sec);
    content.style.setProperty("--d", delay + "ms");
    content.innerHTML = $("t-" + sec).innerHTML; content.hidden = false;
    document.title = sec[0].toUpperCase() + sec.slice(1) + " · clyon.dev";
    if (sec === "projects") playProjects(delay);
  }
  async function route(sec) {
    if (sec && !SECS.includes(sec)) sec = null;
    if (sec === current && !isPost) return;
    const me = ++seq, prev = current;
    isPost = false; current = sec;
    if (page === "home" && prev === null) finishIntro();
    caretOff();
    if (sec && !prev) {
      flip(() => { site.classList.add("docked"); show(sec, 380); scrollTo(0, 0); });
      await wait(RM ? 0 : 700); if (me !== seq) return;
      caretAtEnd(out); caretOn(); await wait(RM ? 0 : 160);
      if (!await typeInto(path, "/" + sec, me, .8)) return;
    } else if (sec) {
      if (sec !== prev) { caretAtEnd(path.textContent ? path : out); caretOn(); if (!await backspace(path, me)) return; }
      show(sec, 0); scrollTo(0, 0);
      if (path.textContent !== "/" + sec && !await typeInto(path, "/" + sec, me, .8)) return;
    } else {
      if (path.textContent) { caretAtEnd(path); caretOn(); if (!await backspace(path, me)) return; caretOff(); }
      d.classList.add("intro", "typing-started");
      if (latest) latest.classList.remove("in");
      flip(() => { content.hidden = true; setActive(null); site.classList.remove("docked"); scrollTo(0, 0); });
      document.title = "clyon.dev";
      await wait(RM ? 0 : 450); if (me !== seq) return;
      if (latest) latest.classList.add("in");
    }
    if (me !== seq) return;
    await wait(RM ? 0 : 180); if (me !== seq) return;
    blinkThenLeave();
  }
  function go(sec) {
    try { history.pushState(null, "", sec ? `/${sec}/` : "/"); } catch (e) {}
    route(sec);
  }
  addEventListener("popstate", () => {
    const p = location.pathname, m = p.match(/^\/(blogs|life|projects)\/?$/);
    if (p === "/" || p === "/index.html") route(null);
    else if (m) route(m[1]);
    else location.reload();
  });
  document.addEventListener("click", e => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest("a[data-sec]");
    if (a) { e.preventDefault(); go(a.dataset.sec); return; }
    if (e.target.closest("#stage")) { e.preventDefault(); if (current || isPost) go(null); }
  });

  /* ---------- project logos: the mark animates, the name types in its own font ---------- */
  const XDOT = '<svg viewBox="0 0 20 20"><g stroke="#00E5A0" stroke-width="4.2" stroke-linecap="round"><line x1="3" y1="3" x2="17" y2="17"/><line x1="17" y1="3" x2="3" y2="17"/></g></svg>';
  const unitsFor = name => name === "Math Blitz" ? [..."Math Bl", `<span class="idot">ı${XDOT}</span>`, ..."tz"] : [...name];
  async function typeCard(card, me) {
    const nm = card.querySelector(".pname"), units = unitsFor(nm.dataset.name);
    card.classList.remove("play"); void card.offsetWidth; card.classList.add("play");
    if (RM) { nm.innerHTML = units.join(""); return; }
    nm.innerHTML = '<span class="pcaret"></span>';
    await wait(card.classList.contains("le") ? 900 : 500);
    let html = "";
    for (const u of units) {
      if (me !== seq || !card.isConnected) return;
      html += u; nm.innerHTML = html + '<span class="pcaret"></span>';
      await wait(55 + Math.random() * 70);
    }
    nm.querySelector(".pcaret").classList.add("blink");
    await wait(1100);
    if (card.isConnected) nm.innerHTML = html;
  }
  async function playProjects(delay) {
    const me = seq, cards = [...content.querySelectorAll(".pcard")];
    if (!RM) cards.forEach(c => { c.querySelector(".pname").innerHTML = ""; });
    await wait(delay + 200);
    for (const c of cards) { if (me !== seq) return; typeCard(c, me); await wait(700); }
  }
  content.addEventListener("pointerenter", e => {
    const c = e.target.closest && e.target.closest(".pcard");
    if (c && e.target === c && !c.dataset.busy) { c.dataset.busy = 1; typeCard(c, seq).finally(() => delete c.dataset.busy); }
  }, true);

  /* ---------- start ---------- */
  const outside = e => !(e.target.closest && e.target.closest(".menu,.latest,#stage,a"));
  addEventListener("keydown", () => { if (introRunning) skip(); });
  addEventListener("pointerdown", e => { if (introRunning && outside(e)) skip(); });

  if (page === "home") {
    const legacy = location.hash.slice(1);   // old clyon.dev/#blogs links
    if (SECS.includes(legacy)) {
      try { history.replaceState(null, "", `/${legacy}/`); } catch (e) {}
      finishIntro(); current = legacy; site.classList.add("docked");
      show(legacy, 0); path.textContent = "/" + legacy;
    } else intro(visited);
  } else if (current === "projects") playProjects(0);
})();

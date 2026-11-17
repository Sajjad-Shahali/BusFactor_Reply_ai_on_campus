/* BusFactor guided tour: a tiny 3D robot (CSS 3D, no library) walks to each part of the app and writes the help in a
   thought cloud above its head. It runs in the page itself (st.html with JavaScript) or from a zero-height iframe on older
   Streamlit versions; either way it reaches the app through W/D below. Everything shown comes from __CONFIG__ (steps,
   translated text, colours); text is inserted with textContent, never as HTML. */
(function () {
  const W = window.frameElement ? window.parent : window;
  const D = W.document;
  const CFG = __CONFIG__;
  const REDUCED = !!(W.matchMedia && W.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const sig = JSON.stringify([CFG.steps.map(s => s.title + s.text), CFG.ui]);

  let startAt = 0, hadTour = false;
  if (W.__bfTour) {
    if (W.__bfTour.sig === sig) return;          // the same tour is already running (Streamlit re-ran the script)
    hadTour = true; startAt = W.__bfTour.idx || 0;               // e.g. the language changed: keep the place, redraw in the new language
    W.__bfTour.destroy(false);
  }

  const C = CFG.colors;
  const css = `
  #bft-root { position: fixed; inset: 0; z-index: 2147483000; pointer-events: none; font-family: "IBM Plex Sans", system-ui, sans-serif; }
  #bft-veil { position: fixed; inset: 0; background: rgba(8,6,4,.38); -webkit-backdrop-filter: blur(7px); backdrop-filter: blur(7px);
              opacity: 0; transition: opacity .55s ease; pointer-events: none; }
  #bft-veil.on { opacity: 1; }
  #bft-robot.jump .scene { animation: bftJump 1.05s cubic-bezier(.3,.1,.5,1) both; }
  @keyframes bftJump { 0% { transform: translateY(-115vh) rotate(-12deg); } 52% { transform: translateY(0) scale(1.08,.88); }
    64% { transform: translateY(-34px) scale(.96,1.05); } 80% { transform: translateY(0) scale(1.05,.93); } 100% { transform: none; } }
  #bft-hl { position: fixed; border: 3px solid ${C.hi}; border-radius: 12px; box-shadow: 0 0 0 4px ${C.glow}, 0 0 28px ${C.glow};
            transition: all .35s ease; opacity: 0; pointer-events: none; }
  #bft-hl.on { opacity: 1; animation: bftPulse 1.6s ease-in-out infinite; }
  @keyframes bftPulse { 50% { box-shadow: 0 0 0 8px ${C.glow}, 0 0 36px ${C.glow}; } }
  #bft-robot { position: fixed; left: 0; top: 0; width: 70px; height: 96px; pointer-events: none; will-change: transform; }
  #bft-robot .scene { position: absolute; inset: 0; perspective: 420px; }
  #bft-robot .robo { position: absolute; left: 5px; top: 0; width: 60px; height: 90px; transform-style: preserve-3d;
                     transform: rotateX(-8deg) rotateY(var(--face, 0deg)); transition: transform .5s ease; }
  #bft-robot .shadow { position: absolute; left: 8px; bottom: 0; width: 54px; height: 12px; border-radius: 50%;
                       background: radial-gradient(closest-side, rgba(0,0,0,.45), transparent); }
  .bfc { position: absolute; transform-style: preserve-3d; }
  .bfc .f { position: absolute; backface-visibility: hidden; }
  .eye { position: absolute; width: 6px; height: 6px; border-radius: 50%; background: ${C.eye}; box-shadow: 0 0 6px ${C.eye}; }
  .part-body { animation: bftBob 2.4s ease-in-out infinite; transform-style: preserve-3d; }
  .walking .part-body { animation: bftStep .36s ease-in-out infinite; }
  .arm, .leg { transform-origin: 50% 0; }
  .walking .armL, .walking .legR { animation: bftSwingA .36s ease-in-out infinite; }
  .walking .armR, .walking .legL { animation: bftSwingB .36s ease-in-out infinite; }
  .talking .armR { animation: bftWave 1.1s ease-in-out infinite; transform-origin: 50% 0; }
  .ant { animation: bftBlink 1.8s steps(2) infinite; }
  @keyframes bftBob { 50% { transform: translateY(-2px); } }
  @keyframes bftStep { 50% { transform: translateY(-4px); } }
  @keyframes bftSwingA { 0%,100% { transform: rotateX(-34deg); } 50% { transform: rotateX(34deg); } }
  @keyframes bftSwingB { 0%,100% { transform: rotateX(34deg); } 50% { transform: rotateX(-34deg); } }
  @keyframes bftWave { 0%,100% { transform: rotateX(-10deg) rotateZ(-8deg); } 50% { transform: rotateX(-150deg) rotateZ(8deg); } }
  @keyframes bftBlink { 50% { filter: brightness(1.7); } }
  #bft-bubble { position: fixed; width: 340px; max-width: calc(100vw - 24px); background: ${C.bubble}; color: ${C.bubbleText};
                border-radius: 22px; padding: 14px 16px 12px; pointer-events: auto; box-shadow: 0 10px 34px rgba(0,0,0,.5);
                transition: opacity .18s ease, transform .22s ease; opacity: 0; transform: scale(.92); transform-origin: 40px 100%;
                pointer-events: none; }
  #bft-bubble.on { opacity: 1; transform: none; pointer-events: auto; }
  #bft-bubble .tail { position: absolute; border-radius: 50%; background: ${C.bubble}; box-shadow: 0 4px 10px rgba(0,0,0,.35); }
  #bft-bubble .tail.a { width: 14px; height: 14px; } #bft-bubble .tail.b { width: 8px; height: 8px; }
  #bft-bubble h3 { margin: 0 0 6px; font: 700 15px/1.25 "Bricolage Grotesque", "IBM Plex Sans", system-ui, sans-serif; color: ${C.bubbleText}; }
  #bft-bubble p { margin: 0 0 10px; font-size: 14px; line-height: 1.5; min-height: 3em; color: ${C.bubbleText}; }
  #bft-bubble p .pen { display: inline-block; animation: bftPen .5s steps(2) infinite; }
  @keyframes bftPen { 50% { opacity: 0; } }
  #bft-bubble .row { display: flex; align-items: center; gap: 8px; }
  #bft-bubble .count { flex: 1; font-size: 12px; opacity: .75; white-space: nowrap; }
  #bft-bubble button { font: 600 13px/1 inherit; border: 0; border-radius: 999px; padding: 8px 12px; white-space: nowrap; cursor: pointer;
                       background: transparent; color: ${C.bubbleText}; border: 1px solid ${C.bubbleText}55; }
  #bft-bubble button.primary { background: ${C.accent}; color: ${C.onAccent}; border-color: ${C.accent}; }
  #bft-bubble button:focus-visible { outline: 3px solid ${C.accent}; outline-offset: 2px; }
  #bft-bubble button.link { border: 0; text-decoration: underline; padding: 8px 4px; opacity: .8; }
  @media (prefers-reduced-motion: reduce) {
    #bft-hl.on, #bft-robot.jump .scene, .part-body, .walking .part-body, .walking .arm, .walking .leg, .talking .armR, .ant { animation: none !important; }
    #bft-bubble, #bft-hl, #bft-veil, #bft-robot .robo { transition: none !important; }
  }`;
  const style = D.createElement('style'); style.id = 'bft-style'; style.textContent = css; D.head.appendChild(style);

  const root = D.createElement('div'); root.id = 'bft-root';
  const veil = D.createElement('div'); veil.id = 'bft-veil';
  const hl = D.createElement('div'); hl.id = 'bft-hl';
  const robot = D.createElement('div'); robot.id = 'bft-robot'; robot.setAttribute('aria-hidden', 'true');
  const bubble = D.createElement('div'); bubble.id = 'bft-bubble'; bubble.setAttribute('role', 'dialog');
  bubble.setAttribute('aria-label', CFG.ui.dialog); bubble.setAttribute('aria-live', 'polite');
  root.append(veil, hl, robot, bubble); D.body.appendChild(root);

  /* ---------- the robot: boxes built from six faces each ---------- */
  function shade(hex, f) {
    const n = parseInt(hex.slice(1), 16);
    const c = v => Math.max(0, Math.min(255, Math.round(v * f)));
    return 'rgb(' + c(n >> 16) + ',' + c((n >> 8) & 255) + ',' + c(n & 255) + ')';
  }
  function cube(w, h, d, color, cls, left, top, z) {
    const el = D.createElement('div'); el.className = 'bfc ' + (cls || '');
    el.style.cssText = 'width:' + w + 'px;height:' + h + 'px;left:' + left + 'px;top:' + top + 'px;' +
      (z ? 'transform:translateZ(' + z + 'px);' : '');
    const faces = [
      ['front', w, h, 'translateZ(' + d / 2 + 'px)', 1.0], ['back', w, h, 'rotateY(180deg) translateZ(' + d / 2 + 'px)', .62],
      ['right', d, h, 'rotateY(90deg) translateZ(' + w / 2 + 'px)', .8], ['left', d, h, 'rotateY(-90deg) translateZ(' + w / 2 + 'px)', .72],
      ['top', w, d, 'rotateX(90deg) translateZ(' + d / 2 + 'px)', 1.18], ['bottom', w, d, 'rotateX(-90deg) translateZ(' + h / 2 + 'px)', .5]];
    faces.forEach(([name, fw, fh, tr, f]) => {
      const face = D.createElement('div'); face.className = 'f ' + name;
      face.style.cssText = 'width:' + fw + 'px;height:' + fh + 'px;left:' + (w - fw) / 2 + 'px;top:' + (h - fh) / 2 + 'px;' +
        'transform:' + tr + ';background:' + shade(color, f) + ';' + (name === 'front' ? 'border-radius:3px;' : '');
      el.appendChild(face);
    });
    return el;
  }
  (function buildRobot() {
    const scene = D.createElement('div'); scene.className = 'scene';
    const sh = D.createElement('div'); sh.className = 'shadow';
    const robo = D.createElement('div'); robo.className = 'robo';
    const body = D.createElement('div'); body.className = 'part-body bfc';
    body.style.cssText = 'left:0;top:0;width:60px;height:90px;';
    const head = cube(30, 24, 24, C.robot, 'head', 15, 14, 0);
    const plate = cube(24, 14, 2, C.plate, '', 3, 5, 12.5); head.appendChild(plate);
    const eyeL = D.createElement('div'); eyeL.className = 'eye'; eyeL.style.cssText = 'left:6px;top:8px;transform:translateZ(14px);';
    const eyeR = D.createElement('div'); eyeR.className = 'eye'; eyeR.style.cssText = 'left:18px;top:8px;transform:translateZ(14px);';
    head.append(eyeL, eyeR);
    const ant = cube(3, 9, 3, C.plate, '', 13.5, 5, 0);
    const ball = cube(7, 7, 7, C.eye, 'ant', 11.5, 0, 0);
    const torso = cube(32, 28, 20, C.robot, '', 14, 40, 0);
    const chest = cube(10, 8, 2, C.eye, 'ant', 11, 8, 10.5); torso.appendChild(chest);
    const armL = cube(8, 24, 8, C.robot2, 'arm armL', 6, 41, 0), armR = cube(8, 24, 8, C.robot2, 'arm armR', 46, 41, 0);
    const legL = cube(11, 22, 11, C.robot2, 'leg legL', 17, 68, 0), legR = cube(11, 22, 11, C.robot2, 'leg legR', 32, 68, 0);
    body.append(legL, legR, torso, armL, armR, head, ant, ball);
    robo.appendChild(body); scene.append(sh, robo); robot.appendChild(scene);
  })();

  /* ---------- finding things in the app ---------- */
  function visible(el) { const r = el.getBoundingClientRect(); return r.width > 4 && r.height > 4; }
  function find(step) {
    if (!step.css) return null;
    const matches = [].slice.call(D.querySelectorAll(step.css)).filter(visible);
    if (!step.match) return matches[0] || null;
    const words = [].concat(step.match).map(w => w.toLowerCase());
    return matches.find(el => words.some(w => (el.textContent || '').toLowerCase().indexOf(w) >= 0)) || null;
  }
  function navLabels() { return [].slice.call(D.querySelectorAll('[data-testid="stSidebar"] [role="radiogroup"] label')); }
  function activePage() {
    const labels = navLabels();
    const i = labels.findIndex(l => { const input = l.querySelector('input'); return input && input.checked; });
    return i;
  }
  function goToPage(i) {
    const labels = navLabels();
    if (labels[i] && activePage() !== i) { labels[i].click(); return true; }
    return false;
  }
  function waitFor(step, ms) {
    return new Promise(resolve => {
      const t0 = Date.now();
      (function poll() {
        const el = find(step);
        if (el || Date.now() - t0 > ms) { resolve(el); return; }
        setTimeout(poll, 140);
      })();
    });
  }

  /* ---------- placing the robot, the highlight and the cloud ---------- */
  const RW = 70, RH = 96, BW = 340;
  let cur = { x: Math.max(20, W.innerWidth - 120), y: Math.max(60, W.innerHeight - 140) };
  let target = null, idx = startAt, typing = null, walkTimer = null, token = 0, destroyed = false;

  function place(x, y) { robot.style.transform = 'translate(' + Math.round(x) + 'px,' + Math.round(y) + 'px)'; cur = { x: x, y: y }; }
  place(cur.x, cur.y);
  let entering = !REDUCED && !hadTour && startAt === 0;   // first time: the robot jumps in over a blurred page
  if (entering) robot.style.visibility = 'hidden';

  function standPoint(r) {
    const vw = W.innerWidth, vh = W.innerHeight, m = 8;
    const cand = [
      { x: r.right + 14, y: r.top + r.height / 2 - RH / 2 },
      { x: r.left - RW - 14, y: r.top + r.height / 2 - RH / 2 },
      { x: r.left + 12, y: r.bottom + 10 },
      { x: r.left + 12, y: r.top - RH - 10 },
    ];
    const fits = p => p.x >= m && p.y >= m + 4 && p.x + RW <= vw - m && p.y + RH <= vh - m;
    const ok = cand.find(fits);
    const p = ok || { x: Math.min(Math.max(m, r.left), vw - RW - m), y: Math.min(Math.max(m + 4, r.bottom - RH), vh - RH - m) };
    return p;
  }
  function placeBubble() {
    const vw = W.innerWidth, vh = W.innerHeight, bh = bubble.offsetHeight || 170;
    let left = cur.x + RW / 2 - 40, top = cur.y - bh - 30, below = false;
    if (top < 8) { top = cur.y + RH + 26; below = true; }
    left = Math.min(Math.max(8, left), vw - BW - 8);
    top = Math.min(Math.max(8, top), vh - bh - 8);
    bubble.style.left = left + 'px'; bubble.style.top = top + 'px';
    [].slice.call(bubble.querySelectorAll('.tail')).forEach(t => t.remove());
    const cx = Math.min(Math.max(14, cur.x + RW / 2 - left), BW - 14);
    const a = D.createElement('div'), b = D.createElement('div'); a.className = 'tail a'; b.className = 'tail b';
    if (below) { a.style.cssText = 'left:' + cx + 'px;top:-8px;'; b.style.cssText = 'left:' + (cx - 4) + 'px;top:-18px;'; }
    else { a.style.cssText = 'left:' + cx + 'px;bottom:-9px;'; b.style.cssText = 'left:' + (cx - 4) + 'px;bottom:-19px;'; }
    bubble.append(a, b);
  }
  function highlight() {
    if (!target || !D.body.contains(target)) { hl.classList.remove('on'); return; }
    const r = target.getBoundingClientRect();
    hl.style.left = (r.left - 6) + 'px'; hl.style.top = (r.top - 6) + 'px';
    hl.style.width = (r.width + 12) + 'px'; hl.style.height = (r.height + 12) + 'px';
    hl.classList.add('on');
  }
  function walkTo(p, done) {
    const dx = p.x - cur.x, dy = p.y - cur.y, dist = Math.hypot(dx, dy);
    robot.style.setProperty('--face', (dx > 8 ? 38 : dx < -8 ? -38 : 0) + 'deg');
    robot.querySelector('.robo').style.setProperty('--face', (dx > 8 ? 38 : dx < -8 ? -38 : 0) + 'deg');
    if (REDUCED || dist < 6) { place(p.x, p.y); done(); return; }
    const ms = Math.min(1700, 450 + dist * 1.6);
    robot.style.transition = 'transform ' + ms + 'ms cubic-bezier(.45,.05,.3,1)';
    robot.classList.add('walking');
    place(p.x, p.y);
    clearTimeout(walkTimer);
    walkTimer = setTimeout(function () { robot.classList.remove('walking'); robot.style.transition = ''; done(); }, ms + 40);
  }

  /* ---------- the thought cloud and its writing effect ---------- */
  function renderBubble(step, writing) {
    bubble.textContent = '';
    const h = D.createElement('h3'); h.textContent = step.title;
    const p = D.createElement('p');
    const row = D.createElement('div'); row.className = 'row';
    const count = D.createElement('span'); count.className = 'count';
    count.textContent = CFG.ui.step.replace('{n}', idx + 1).replace('{m}', CFG.steps.length);
    const skip = D.createElement('button'); skip.className = 'link'; skip.type = 'button'; skip.textContent = idx === CFG.steps.length - 1 ? '' : CFG.ui.skip;
    skip.onclick = function () { finish(); };
    const back = D.createElement('button'); back.type = 'button'; back.textContent = CFG.ui.back; back.disabled = idx === 0; back.style.opacity = idx === 0 ? .4 : 1;
    back.onclick = function () { go(idx - 1); };
    const next = D.createElement('button'); next.type = 'button'; next.className = 'primary';
    next.textContent = idx === CFG.steps.length - 1 ? CFG.ui.finish : CFG.ui.next;
    next.onclick = function () { idx === CFG.steps.length - 1 ? finish() : go(idx + 1); };
    row.append(count, skip, back, next);
    bubble.append(h, p, row);
    p.textContent = step.text; p.style.minHeight = p.offsetHeight + 'px';   // reserve the full height first: the cloud never grows over the robot
    placeBubble();
    void bubble.offsetWidth;          // so the pop-in animates from the new spot
    bubble.classList.add('on');
    write(p, step.text, writing);
    return next;
  }
  function write(p, text, writing) {
    clearInterval(typing);
    const pen = D.createElement('span'); pen.className = 'pen'; pen.textContent = ' ✍';
    if (!writing || REDUCED) { p.textContent = text; return; }
    let i = 0; p.textContent = ''; const node = D.createTextNode(''); p.append(node, pen);
    robot.classList.add('talking');
    typing = setInterval(function () {
      i += 2; node.nodeValue = text.slice(0, i);
      if (i >= text.length) { clearInterval(typing); pen.remove(); robot.classList.remove('talking'); }
    }, 22);
  }

  /* ---------- the tour ---------- */
  async function go(n) {
    if (destroyed) return;
    idx = Math.max(0, Math.min(CFG.steps.length - 1, n)); W.__bfTour.idx = idx;
    const my = ++token, step = CFG.steps[idx];
    clearInterval(typing); robot.classList.remove('talking'); hl.classList.remove('on');
    veil.classList.toggle('on', !step.css);   // the page is blurred only while the robot talks in the middle (first and last step)
    bubble.classList.remove('on');   // close the cloud while the robot walks; it opens again at the new spot
    bubble.setAttribute('aria-busy', 'true');
    if (step.page !== null && step.page !== undefined) {
      if (goToPage(step.page)) await new Promise(r => setTimeout(r, 450));
    }
    target = step.css ? await waitFor(step, 7000) : null;
    if (destroyed || my !== token) return;
    let p;
    if (target) {
      target.scrollIntoView({ block: 'center', behavior: REDUCED ? 'auto' : 'smooth' });
      await new Promise(r => setTimeout(r, REDUCED ? 0 : 380));
      if (destroyed || my !== token) return;
      p = standPoint(target.getBoundingClientRect());
    } else {
      p = { x: Math.max(20, W.innerWidth / 2 - RW / 2), y: Math.max(120, W.innerHeight / 2 - 40) };
    }
    const arrived = function () {
      if (destroyed || my !== token) return;
      highlight();
      bubble.removeAttribute('aria-busy');
      const next = renderBubble(step, true);
      next.focus({ preventScroll: true });
      W.__bfTour.report.push({ step: step.id, found: !!target });
    };
    if (entering) {
      entering = false; place(p.x, p.y);
      robot.style.visibility = ''; robot.classList.add('jump');
      walkTimer = setTimeout(function () { robot.classList.remove('jump'); arrived(); }, 1100);
    } else walkTo(p, arrived);
  }
  function finish() {
    const stop = D.querySelector('.st-key-tour-stop button');
    destroy(true);
    if (stop) stop.click();          // tells the app the tour is over (the sidebar button)
  }
  function destroy(full) {
    destroyed = true; clearInterval(typing); clearTimeout(walkTimer);
    W.removeEventListener('keydown', onKey, true); W.removeEventListener('resize', onResize); D.removeEventListener('click', onStopClick, true);
    clearInterval(follow); root.remove(); style.remove();
    if (full) delete W.__bfTour;
  }
  function onKey(e) {
    if (e.key === 'Escape') { e.preventDefault(); finish(); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); idx === CFG.steps.length - 1 ? finish() : go(idx + 1); }
    else if (e.key === 'ArrowLeft' && idx > 0) { e.preventDefault(); go(idx - 1); }
  }
  function onResize() { highlight(); placeBubble(); }
  // The sidebar "Stop the tutorial" button (or the app dropping the tour) must remove the robot too: the script lives in
  // the page and would otherwise outlive the Streamlit element that started it.
  function onStopClick(e) { if (e.target && e.target.closest && e.target.closest('.st-key-tour-stop')) destroy(true); }
  D.addEventListener('click', onStopClick, true);
  function loaderAlive() { return W.frameElement ? W.frameElement.isConnected : !!D.getElementById('bf-tour-loader'); }
  let missing = 0;
  W.addEventListener('keydown', onKey, true); W.addEventListener('resize', onResize);
  const follow = setInterval(function () {
    if (destroyed) return;
    missing = loaderAlive() ? 0 : missing + 1;
    if (missing >= 4) { destroy(true); return; }      // the app no longer asks for the tour (about 1.6 s, so a quick re-run does not end it)
    highlight();
  }, 400);   // the page may move under the highlight

  W.__bfTour = { sig: sig, idx: idx, report: [], destroy: destroy, go: go, finish: finish };
  go(startAt);
})();

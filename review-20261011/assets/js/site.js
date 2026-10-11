// からあげやカリッジュ徳島
// 1) 最初の画面：揚げている動画 → 網で上げたところで竹ざるの写真がせり上がり、キャッチを押す（1回だけ）
// 2) 13回の数字の中の唐揚げが、スクロールに合わせて少し動く
// 3) 味えらび（6つの札で竹ざるの中身が変わる）
// 4) 画面の下のバーから開くお店えらび
// 5) メニューのお店しぼり
// スクリプトが無くても、動きを減らす設定でも、全部の情報は最初から見える（CSS の .js / .motion で分けている）
(() => {
  const root = document.documentElement;
  const motion = root.classList.contains('motion');

  // ---------- 1) 最初の画面 ----------
  const hero = document.querySelector('.hero');
  if (hero) {
    const video = hero.querySelector('.hero__video');
    const replay = hero.querySelector('[data-intro-play]');
    let done = false;
    let timers = [];
    const clearTimers = () => { timers.forEach(clearTimeout); timers = []; };
    const stamp = () => {
      if (done) return;
      done = true;
      clearTimers();
      hero.classList.remove('intro-playing');
      hero.classList.add('is-lifted');
      if (video) video.pause();
      timers.push(setTimeout(() => hero.classList.add('is-stamped'), motion ? 380 : 0));
    };
    const playIntro = () => {
      if (!video) return;
      clearTimers();
      done = false;
      hero.classList.remove('is-lifted', 'is-stamped');
      hero.classList.add('intro-playing');
      const src = matchMedia('(min-width: 900px)').matches ? video.dataset.srcHd : video.dataset.src;
      if (video.error || video.getAttribute('src') !== src) video.src = src;
      else video.currentTime = 0;
      video.muted = true;
      let started = false;
      const onPlaying = () => { started = true; };
      video.addEventListener('playing', onPlaying, { once: true });
      const p = video.play();
      if (p && p.catch) p.catch(stamp);
      timers.push(setTimeout(() => { video.removeEventListener('playing', onPlaying); if (!started) stamp(); }, 4000));
      timers.push(setTimeout(stamp, 10000));
    };
    if (video) {
      video.addEventListener('timeupdate', () => {
        if (video.duration && video.currentTime >= video.duration - 0.35) stamp();
      });
      video.addEventListener('ended', stamp);
      video.addEventListener('error', stamp);
    }
    hero.addEventListener('click', (e) => { if (!e.target.closest('a, button')) stamp(); });
    if (replay) replay.addEventListener('click', playIntro);
    if (!motion || !video) {
      hero.classList.add('is-lifted', 'is-stamped');
      done = true;
    } else {
      // 見た回数にかかわらずページを開いたら再生。端末が動きを減らす設定なら手動再生にする。
      playIntro();
    }
  }

  // ---------- 2) 13回の数字の中の唐揚げ ----------
  const taste = document.querySelector('.taste');
  if (taste && motion) {
    const num = taste.querySelector('.taste__num');
    let ticking = false;
    const update = () => {
      ticking = false;
      const r = taste.getBoundingClientRect();
      const vh = innerHeight;
      const p = Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
      num.style.setProperty('--bgp', `${20 + p * 60}%`);
    };
    addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
  }

  // ---------- 2.2) 文字の帯：下へ読むと左へ、戻ると右へ ----------
  const band = document.querySelector('[data-band] .band__track');
  // ---------- 2.3) 13回の舞台：唐揚げの写真が「13」の形に抜けていく ----------
  const award = document.querySelector('[data-award]');
  const clamp01 = (v) => Math.min(1, Math.max(0, v));
  const seg = (p, a, b) => { const t = clamp01((p - a) / (b - a)); return t * t * (3 - 2 * t); };
  if (motion && (band || award)) {
    let ticking2 = false;
    const onScroll = () => {
      ticking2 = false;
      if (award) {
        const r = award.getBoundingClientRect();
        const p = clamp01(-r.top / (r.height - innerHeight));
        const ph = 1 - seg(p, 0.08, 0.42);
        award.style.setProperty('--ph', ph.toFixed(3));
        award.style.setProperty('--ns', (1 + 0.55 * ph).toFixed(3));
        award.style.setProperty('--no', (0.35 + 0.65 * seg(p, 0.1, 0.4)).toFixed(3));
        award.style.setProperty('--u', seg(p, 0.42, 0.6).toFixed(3));
        award.style.setProperty('--l', seg(p, 0.58, 0.8).toFixed(3));
      }
    };
    addEventListener('scroll', () => { if (!ticking2) { ticking2 = true; requestAnimationFrame(onScroll); } }, { passive: true });
    // 帯はいつもゆっくり流れ続け（1秒に約40px）、スクロールすると速くなる。下へ読むと左へ、戻ると右へ
    if (band) {
      let x = 0, dir = 1, lastY = scrollY, boost = 0, last = performance.now();
      const loop = (now) => {
        const dt = Math.min(0.05, (now - last) / 1000); last = now;
        const dy = scrollY - lastY; lastY = scrollY;
        if (dy) { dir = dy > 0 ? 1 : -1; boost = Math.min(900, boost + Math.abs(dy) * 6); }
        boost *= 0.9;
        const w = band.firstElementChild.getBoundingClientRect().width || 1;
        x -= dir * (40 + boost) * dt;
        x = ((x % w) - w) % w;
        band.style.setProperty('--bx', `${x.toFixed(1)}px`);
        requestAnimationFrame(loop);
      };
      requestAnimationFrame(loop);
    }
    addEventListener('resize', onScroll);
    onScroll();
  }

  // ---------- 2.5) スクロールで現れる（.rv） ----------
  const rvs = document.querySelectorAll('.rv');
  if (motion && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -12% 0px' });
    rvs.forEach((el) => io.observe(el));
  } else rvs.forEach((el) => el.classList.add('is-in'));

  // ---------- 3) 味えらび ----------
  document.querySelectorAll('[data-picker]').forEach((picker) => {
    const items = [...picker.querySelectorAll('[data-flavor]')];
    const figs = [...picker.querySelectorAll('[data-fig]')];
    const select = (id) => {
      items.forEach((li) => {
        const on = li.dataset.flavor === id;
        li.classList.toggle('is-on', on);
        li.querySelector('.flavor__btn').setAttribute('aria-pressed', String(on));
      });
      figs.forEach((f) => f.classList.toggle('is-on', f.dataset.fig === id));
    };
    items.forEach((li) => li.querySelector('.flavor__btn').addEventListener('click', () => select(li.dataset.flavor)));
  });

  // ---------- 4) お店えらび ----------
  let lastFocus = null;
  const close = () => {
    document.querySelectorAll('.sheet.is-open').forEach((s) => s.classList.remove('is-open'));
    if (location.hash.startsWith('#sheet-')) history.replaceState(null, '', location.pathname + location.search);
    if (lastFocus) lastFocus.focus();
  };
  const open = (id, from) => {
    const s = document.getElementById(id);
    if (!s) return;
    lastFocus = from || null;
    s.classList.add('is-open');
    const first = s.querySelector('.sheet__row, .sheet__close');
    if (first) first.focus();
  };
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-sheet]');
    if (t) { e.preventDefault(); open(t.dataset.sheet, t); return; }
    if (e.target.closest('[data-close]')) { e.preventDefault(); close(); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

  // ---------- 5) メニューのお店しぼり ----------
  const filter = document.querySelector('[data-filter]');
  if (filter) {
    filter.hidden = false;
    filter.addEventListener('click', (e) => {
      const b = e.target.closest('[data-store]');
      if (!b) return;
      filter.querySelectorAll('[data-store]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      if (b.dataset.store === 'all') delete document.body.dataset.store;
      else document.body.dataset.store = b.dataset.store;
    });
  }
})();

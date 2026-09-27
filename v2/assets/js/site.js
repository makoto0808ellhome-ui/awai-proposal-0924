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
  const force = /[?&]motion=force/.test(location.search);

  // ---------- 1) 最初の画面 ----------
  const hero = document.querySelector('.hero');
  if (hero) {
    const video = hero.querySelector('.hero__video');
    let done = false;
    const stamp = () => {
      if (done) return;
      done = true;
      hero.classList.add('is-lifted');
      setTimeout(() => hero.classList.add('is-stamped'), 380);
      try { sessionStorage.setItem('kariju-intro', '1'); } catch (e) { /* 使えなくても困らない */ }
    };
    let seen = false;
    try { seen = sessionStorage.getItem('kariju-intro') === '1'; } catch (e) { /* 何もしない */ }
    if (!motion || !video || (seen && !force)) {
      hero.classList.add('is-lifted', 'is-stamped');
      if (video) video.removeAttribute('src');
    } else {
      // 広い画面は元の大きさ（720×1280）の版、スマホは軽い版
      video.src = matchMedia('(min-width: 900px)').matches ? video.dataset.srcHd : video.dataset.src;
      // 網が手前まで上がりきる少し前（残り0.35秒）で切り替える
      video.addEventListener('timeupdate', () => {
        if (video.duration && video.currentTime >= video.duration - 0.35) stamp();
      });
      video.addEventListener('ended', stamp);
      video.addEventListener('error', stamp);
      hero.addEventListener('click', (e) => { if (!e.target.closest('a')) stamp(); });
      const p = video.play();
      if (p && p.catch) p.catch(stamp);
      // 回線が遅いときは待たせすぎない：4秒たっても動き出さなければ写真を出す（待つ間は最初の1コマを見せている）
      let started = false;
      video.addEventListener('playing', () => { started = true; }, { once: true });
      setTimeout(() => { if (!started) stamp(); }, 4000);
      setTimeout(stamp, 10000);
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

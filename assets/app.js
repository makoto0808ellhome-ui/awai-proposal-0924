(() => {
  'use strict';
  const base = new URL('.', document.currentScript.src);
  const dependencies = [
    {name:'gsap',url:'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js',integrity:'sha384-g4NTh/Iv5PPU4xPyhEWqPcwtNXOvdaDI8LLnyYfyNZOjKJeYQyjzQ9X5275eBjpt'},
    {name:'ScrollTrigger',url:'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js',integrity:'sha384-Z3REaz79l2IaAZqJsSABtTbhjgOUYyV3p90XNnAPCSHg3EMTz1fouunq9WZRtj3d'},
    {name:'lenis',url:'https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js',integrity:'sha384-B2WBjDzEjJpYvhmi2UyEn7rektqkf5suS6sNoyyrf0EBAwBHdkiXxIlU0V5Ru2ed'}
  ];
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let context, lenis, ticker;
  const restore = () => {
    if (context) context.revert();
    if (lenis) lenis.destroy();
    if (ticker && window.gsap) gsap.ticker.remove(ticker);
    context = lenis = ticker = null;
    document.querySelectorAll('[data-price]').forEach(el => el.textContent = Number(el.dataset.price).toLocaleString('ja-JP'));
  };
  function loadScript(dep, local = false) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = local ? new URL(`vendor/${dep.name}.min.js`,base).href : dep.url;
      // CDN assets are pinned and protected by SRI. Local fallback is byte-identical.
      if (!local) { script.integrity = dep.integrity; script.crossOrigin = 'anonymous'; }
      script.onload = resolve;
      script.onerror = () => {script.remove(); local ? reject(new Error(dep.name)) : loadScript(dep,true).then(resolve,reject);};
      document.head.append(script);
    });
  }
  function startMotion() {
    if (reduced.matches || !window.gsap || !window.ScrollTrigger) return;
    restore();
    gsap.registerPlugin(ScrollTrigger);
    context = gsap.context(() => {
      if(document.querySelector('.hero')){
        gsap.fromTo('.hero-image',{scale:1,filter:'brightness(.80)'},{scale:1.055,filter:'brightness(1)',duration:2.3,ease:'power2.out'});
        gsap.from('.hero-line',{y:25,autoAlpha:0,stagger:.14,duration:.8,delay:.15,clearProps:'transform,opacity,visibility',ease:'power3.out'});
        gsap.from('.hero-entrance',{y:15,autoAlpha:0,stagger:.12,duration:.7,delay:.5,clearProps:'transform,opacity,visibility'});
      }
      gsap.utils.toArray('[data-reveal]').forEach((el,i)=>gsap.from(el,{y:28,autoAlpha:0,duration:.65,delay:innerWidth>700?(i%3)*.06:0,ease:'power2.out',clearProps:'transform,opacity,visibility',scrollTrigger:{trigger:el,start:'top 94%',once:true}}));
      gsap.utils.toArray('[data-shop-reveal]').forEach((el,i)=>gsap.from(el,{x:i%2?35:-35,autoAlpha:0,duration:.7,clearProps:'transform,opacity,visibility',scrollTrigger:{trigger:el,start:'top 93%',once:true}}));
      document.querySelectorAll('[data-price]').forEach(el=>{
        const end=Number(el.dataset.price);
        const value={n:end};
        ScrollTrigger.create({trigger:el,start:'top 96%',once:true,onEnter:()=>{
          value.n=0;
          gsap.to(value,{n:end,duration:.8,ease:'power2.out',onUpdate:()=>el.textContent=Math.round(value.n).toLocaleString('ja-JP'),onComplete:()=>el.textContent=end.toLocaleString('ja-JP')});
        }});
      });
    });
    if(window.Lenis){
      lenis = new Lenis({lerp:.11,smoothWheel:true,syncTouch:false});
      window.karijuLenis=lenis;
      lenis.on('scroll',ScrollTrigger.update);
      ticker=time=>lenis.raf(time*1000);
      gsap.ticker.add(ticker);
    }
    document.fonts.ready.then(()=>ScrollTrigger.refresh());
    document.querySelectorAll('img').forEach(img=>img.addEventListener('load',()=>ScrollTrigger.refresh(),{once:true}));
  }
  document.addEventListener('click',e=>{
    const a=e.target.closest('a[href^="#"]');
    if(!a)return;
    const target=document.getElementById(a.getAttribute('href').slice(1));
    if(target && lenis && !reduced.matches){e.preventDefault();lenis.scrollTo(target,{offset:-100,onComplete:()=>{history.pushState(null,'',a.hash);target.setAttribute('tabindex','-1');target.focus({preventScroll:true});}});}
  });
  let loaded=false;
  async function initialize(){
    try{if(!loaded){for(const dep of dependencies)await loadScript(dep);loaded=true;}startMotion();}
    catch(error){restore();console.warn('動きの読み込みを省略しました。内容はそのまま閲覧できます。');}
  }
  if(!reduced.matches)initialize();
  reduced.addEventListener('change',()=>reduced.matches?restore():initialize());
})();

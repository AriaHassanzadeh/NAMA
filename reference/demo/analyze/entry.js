/* NAMA's logo-first entrance. Media marks are navigation, not live connections. */
(() => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const STORE = 'nama-analyze-entry-v1';
  const clean = value => typeof value === 'string' ? value.slice(0, 2000) : '';
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem(STORE) || '{}') || {}; } catch {}
  let draft = {
    idea: clean(stored.idea), customer: clean(stored.customer), goalNote: clean(stored.goalNote),
    audience: ['consumer','business','both'].includes(stored.audience) ? stored.audience : '',
    market: clean(stored.market), budget: clean(stored.budget),
    goal: ['market','competitors','opportunity'].includes(stored.goal) ? stored.goal : '',
    theme: stored.theme === 'light' ? 'light' : 'dark', completed: stored.completed === true,
    source: clean(stored.source)
  };
  let paused = false;
  let callbacks = {};
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fa = value => String(value).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
  const paths = {
    arrow:'<path d="M18 12H6m6 6-6-6 6-6"/>', chevron:'<path d="m9 5 7 7-7 7"/>',
    sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/>',
    moon:'<path d="M20 14A8 8 0 0 1 10 4a8 8 0 1 0 10 10Z"/>', plus:'<path d="M12 5v14M5 12h14"/>',
    check:'<path d="m5 12 4 4L19 6"/>', shirt:'<path d="m8 3-5 3-2 5 5 2v8h12v-8l5-2-2-5-5-3a4 4 0 0 1-8 0Z"/>',
    bolt:'<path d="m13 2-9 12h7l-1 8 10-12h-7V2Z"/>',
    users:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3m1-16a3 3 0 0 1 0 6m2 3a5 5 0 0 1 3 4v3"/>',
    shop:'<path d="m3 9 2-6h14l2 6M4 12v9h16v-9M9 21v-6h6v6"/><path d="M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/>',
    globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a19 19 0 0 1 0 18 19 19 0 0 1 0-18Z"/>',
    chart:'<path d="M4 3v17h17M7 15l5-5 4 3 5-8"/>',
    target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><path d="m12 12 9-9m-5 0h5v5"/>',
    spark:'<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
    shield:'<path d="m12 3 8 3v6c0 4-4 7-8 9-4-2-8-5-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/>'
  };
  const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.spark}</svg>`;
  const persist = () => { try { localStorage.setItem(STORE, JSON.stringify(draft)); } catch {} };
  const themeControl = () => `<button type="button" class="theme-toggle" data-entry-action="theme" aria-label="تغییر به حالت ${draft.theme==='dark'?'روشن':'تاریک'}" aria-pressed="${draft.theme==='dark'}">${icon(draft.theme==='dark'?'sun':'moon')}</button>`;
  const steps = ['idea','customer','goal'];
  const stepRoute = step => '#/start/' + steps[step];
  const isValidIdea = () => draft.idea.trim().length >= 5;
  const isValidCustomer = () => Boolean(draft.audience || draft.customer.trim().length >= 3);
  const guard = step => !isValidIdea() && step > 0 ? 0 : !isValidCustomer() && step > 1 ? 1 : step;
  const stepIndex = () => Math.max(0, steps.indexOf(location.hash.split('/')[2]));
  const refresh = selector => { callbacks.render?.(); if(selector) document.querySelector(selector)?.focus({preventScroll:true}); };


  const marks = {
    instagram: '<rect x="4" y="4" width="16" height="16" rx="5" stroke="currentColor" stroke-width="1.65"/><circle cx="12" cy="12" r="3.6" stroke="currentColor" stroke-width="1.65"/><circle cx="17.1" cy="6.9" r="1" fill="currentColor"/>',
    telegram: '<path fill="currentColor" d="m20.7 4.3-3.2 15.1c-.2 1-1 1.3-1.8.7l-4.8-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.4-4.9L17 6.1c.4-.4-.1-.6-.6-.3L5.2 12.9.4 11.4c-1-.3-1.1-1 .2-1.5L19.4 2.7c.9-.3 1.7.2 1.3 1.6Z" transform="translate(1 1) scale(.96)"/>',
    youtube: '<rect x="2.5" y="5.3" width="19" height="13.4" rx="4.1" fill="currentColor"/><path d="m10 9 5.3 3-5.3 3V9Z" fill="var(--planet-fill)"/>',
    tiktok: '<path fill="currentColor" d="M14.1 3h3.2c.2 1.7 1.2 3.1 2.7 3.8.6.3 1.3.4 2 .5v3.2a9.2 9.2 0 0 1-4.7-1.4v7.2a6 6 0 1 1-6.8-5.9v3.3a2.7 2.7 0 1 0 3.6 2.6V3Z" transform="translate(-1 0)"/>',
    linkedin: '<rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" stroke-width="1.4"/><circle cx="7.4" cy="7.6" r="1.3" fill="currentColor"/><path d="M7.4 11v6.5M11.6 17.5V11m0 2.6c0-3.6 5-3.6 5 0v3.9" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>',
    x: '<path fill="currentColor" d="M17.5 3H21l-7.6 8.7L22.3 21h-6.9L10 15.1 4.8 21H1.3l7-8L.7 3h7.1l4.9 5.4L17.5 3Zm-1.3 16h2L6.6 4.9H4.5L16.2 19Z"/>',
    podcast: '<rect x="9" y="3.5" width="6" height="12" rx="3" stroke="currentColor" stroke-width="1.6"/><path d="M6 11a6 6 0 0 0 12 0M12 17v4m-3 0h6M3.3 7a11 11 0 0 0 0 8M20.7 7a11 11 0 0 1 0 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
    news: '<path d="M5 4h15v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9h2m0-5v14m3-10h8m-8 4h3v4H8v-4Zm6 0h3m-3 4h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    rss: '<circle cx="5.4" cy="18.6" r="1.9" fill="currentColor"/><path d="M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/>',
    search: '<path fill="currentColor" d="M21.6 12.2c0-.7-.1-1.4-.2-2.1H12v4h5.4a4.6 4.6 0 0 1-2 3.1v2.6h3.3c2-1.8 2.9-4.4 2.9-7.6Z"/><path fill="currentColor" d="M12 22c2.7 0 5-.9 6.7-2.4l-3.3-2.6a6.1 6.1 0 0 1-9.2-3.2H2.8v2.7A10 10 0 0 0 12 22Zm-5.8-8.2a6.2 6.2 0 0 1 0-3.6V7.5H2.8a10 10 0 0 0 0 9l3.4-2.7ZM12 6a5.5 5.5 0 0 1 3.9 1.5l2.9-2.8A9.7 9.7 0 0 0 12 2a10 10 0 0 0-9.2 5.5l3.4 2.7A6 6 0 0 1 12 6Z"/>'
  };
  const media = [
    {key:'instagram', name:'Instagram', section:'social', label:'آغاز بررسی بازار', accent:'#e87da9'},
    {key:'telegram', name:'Telegram', section:'social', label:'آغاز بررسی بازار', accent:'#79b9e8'},
    {key:'youtube', name:'YouTube', section:'campaigns', label:'کشف تبلیغات', accent:'#ff727b'},
    {key:'tiktok', name:'TikTok', section:'social', label:'آغاز بررسی بازار', accent:'#7edbd9'},
    {key:'linkedin', name:'LinkedIn', section:'social', label:'آغاز بررسی بازار', accent:'#8baee8'},
    {key:'x', name:'X', section:'social', label:'آغاز بررسی بازار', accent:'#ddd8e9'},
    {key:'podcast', name:'Podcasts', section:'campaigns', label:'کشف تبلیغات', accent:'#baa2ec'},
    {key:'news', name:'News', section:'market', label:'روندها و فرصت‌ها', accent:'#e4bd9b'},
    {key:'rss', name:'RSS', section:'market', label:'روندها و فرصت‌ها', accent:'#dda779'},
    {key:'search', name:'Search', section:'overview', label:'نمای کلی بازار', accent:'#91b8ad'}
  ];
  const rings = [
    {diameter:43, duration:58, planets:[[0,17],[1,197]]},
    {diameter:70, duration:90, planets:[[2,83],[3,203],[4,323]]},
    {diameter:100, duration:128, planets:[[5,47],[6,119],[7,191],[8,263],[9,335]]}
  ];
  const svg = (paths, cls='') => `<svg class="solar-media-mark ${cls}" viewBox="0 0 24 24" fill="none" aria-hidden="true">${paths}</svg>`;
  const motionIcon = () => paused ? '<path d="m9 5 10 7-10 7V5Z"/>' : '<path d="M8 5v14M16 5v14"/>';
  const motionLabel = () => reducedMotion.matches ? 'حرکت مطابق تنظیم کاهش انیمیشن غیرفعال است' : paused ? 'ادامهٔ حرکت مدارها' : 'توقف حرکت مدارها';

  function stars() {
    let seed = 291127;
    const random = () => {seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646;};
    return Array.from({length:172}, (_, i) => {
      const x = (random()*100).toFixed(3), y = (random()*100).toFixed(3);
      const size = (random()*.95+.7).toFixed(2), opacity = (random()*.27+.14).toFixed(2);
      return `<i class="solar-star ${i%17===0?'solar-star--shimmer':''} ${i%43===0?'solar-star--cross':''}" style="left:${x}%;top:${y}%;--star-size:${size}px;--star-opacity:${opacity};--star-delay:-${(random()*9).toFixed(2)}s"></i>`;
    }).join('');
  }

  function portal() {
    return `<main class="solar-portal ${paused?'is-paused':''}" aria-label="منظومهٔ رسانه‌ای نما">
      <h1 class="sr-only">نما؛ شروع یک مسیر روشن برای تحلیل بازار</h1>
      <div class="solar-stars" aria-hidden="true">${stars()}</div>
      <div class="solar-atmosphere" aria-hidden="true"></div>
      <div class="solar-tools">${themeControl()}<button class="solar-motion-toggle" data-entry-action="motion" aria-label="${motionLabel()}" aria-pressed="${paused||reducedMotion.matches}" ${reducedMotion.matches?'disabled':''} title="${motionLabel()}">${svg(motionIcon(),'solar-control-mark')}</button></div>
      <div class="solar-edition" aria-hidden="true"><span></span><span>NAMA UNIVERSE</span></div>
      <section class="solar-system" aria-label="رسانه‌ها در مدار نما">
        <div class="solar-aura" aria-hidden="true"></div>
        ${rings.map((ring, ri)=>`<div class="solar-orbit solar-orbit--${ri+1}" style="--orbit-diameter:${ring.diameter}%;--orbit-duration:${ring.duration}s"><div class="solar-orbit-track" aria-hidden="true"></div>${ring.planets.map(([index,phase])=>{const item=media[index];return `<div class="solar-rotor" style="--phase:${phase}deg"><div class="solar-distance"><div class="solar-counter"><button class="solar-planet solar-planet--${item.key}" style="--planet-accent:${item.accent}" data-entry-action="start" data-entry-source="${item.key}" aria-label="${item.name} — ${item.label}">${svg(marks[item.key])}<span class="solar-planet-tooltip"><strong>${item.name}</strong><small>${item.label}</small></span></button></div></div></div>`;}).join('')}</div>`).join('')}
        <div class="solar-center"><button class="solar-core" data-entry-action="start" aria-label="شروع با نما"><span class="solar-core-halo" aria-hidden="true"></span><img src="assets/mark.svg" alt=""><span class="nama-logotype">NAMA</span><span class="solar-core-enter" aria-hidden="true">${icon('arrow','sm')}</span></button></div>
      </section>
      <footer class="solar-footer"><span class="solar-signature" lang="en" dir="ltr">INTELLIGENCE. IN ORBIT.</span><button class="solar-enter-hint" data-entry-action="start"><span></span>برای شروع، روی نما کلیک کن ${icon('arrow','sm')}</button><span class="solar-index" aria-hidden="true">01 <i></i> NAMA</span></footer>
    </main>`;
  };


  function discovery(step=0) {
    const titles = ['اول، از ایده‌ات بگو.','مشتری تو چه کسی است؟','از این بررسی چه می‌خواهی؟'];
    const descriptions = ['قرار است چه چیزی بفروشی یا چه مسئله‌ای را حل کنی؟','برای چه کسی ارزش می‌سازی؟ از اولین مشتری‌های احتمالی‌ات بگو.','مهم‌ترین تصمیم پیش رویت را مشخص کن تا مسیر بررسی روشن‌تر شود.'];
    const fields = ['idea','customer','goalNote'];
    const placeholders = ['مثلاً می‌خواهم یک برند پوشاک مینیمال برای خانم‌های شاغل راه بیندازم…','مثلاً خانم‌های شاغل ۲۵ تا ۳۵ سال در تهران که لباس ساده و باکیفیت می‌خواهند…','اگر سؤال مشخصی داری، اینجا بنویس؛ مثلاً چه چیزی من را از رقبا متفاوت می‌کند؟'];
    const audiences = [['consumer','خریدار نهایی','users'],['business','کسب‌وکارها','shop'],['both','هر دو گروه','globe']];
    const goals = [['market','شناخت بازار','chart'],['competitors','مقایسه رقبا','target'],['opportunity','پیدا کردن فرصت','spark']];
    const choices = (items,key) => `<div class="entry-choices" role="group" aria-label="${key==='audience'?'نوع مشتری':'هدف بررسی'}">${items.map(([value,label,mark])=>`<button type="button" class="entry-choice ${draft[key]===value?'selected':''}" data-entry-action="choice" data-entry-key="${key}" data-entry-value="${value}" aria-pressed="${draft[key]===value}">${icon(mark)}<strong>${label}</strong><span class="entry-choice-check">${icon('check')}</span></button>`).join('')}</div>`;
    return `<main class="entry-discovery">
      <header class="entry-header">
        <button type="button" class="entry-brand" data-entry-action="portal" aria-label="بازگشت به منظومهٔ نما"><img src="assets/mark.svg" alt=""><span>NAMA</span></button>
        <nav class="entry-progress" aria-label="مراحل شروع پروژه">${steps.map((key,i)=>`<button type="button" class="${i===step?'current':i<step?'complete':''}" data-entry-action="step" data-entry-step="${i}" ${i===step?'aria-current="step"':''} ${i>step?'disabled':''}><b>${fa('0'+(i+1))}</b> ${['ایده','مشتری','هدف'][i]}</button>${i<2?`<span class="${i<step?'done':''}" aria-hidden="true"></span>`:''}`).join('')}</nav>
        <div class="entry-header-actions">${themeControl()}<button type="button" class="entry-back" data-entry-action="back">بازگشت ${icon('chevron')}</button></div>
      </header>
      <section class="entry-question" aria-labelledby="entryTitle">
        <img class="entry-mini-mark" src="assets/mark.svg" alt="">
        <p class="entry-eyebrow">کمی بیشتر، کمی روشن‌تر</p>
        <h1 id="entryTitle" tabindex="-1">${titles[step]}</h1><p class="entry-description">${descriptions[step]}</p>
        ${step===0?`<div class="entry-examples">${['پوشاک مینیمال زنانه','فروشگاه لباس ورزشی','برند پوشاک روزمره'].map((text,i)=>`<button type="button" data-entry-action="example" data-entry-value="${text}">${icon(i===1?'bolt':'shirt')}${text}</button>`).join('')}</div>`:''}
        ${step===1?choices(audiences,'audience')+`<div class="entry-fields"><div class="form-field"><label for="entryMarket">بازار اولیه <small>اختیاری</small></label><input id="entryMarket" data-entry-field="market" maxlength="100" value="${esc(draft.market)}" placeholder="مثلاً تهران یا سراسر ایران"></div><div class="form-field"><label for="entryBudget">بودجهٔ آزمایش اولیه <small>اختیاری</small></label><select id="entryBudget" data-entry-field="budget">${['هنوز مشخص نیست','کمتر از ۲۰ میلیون تومان','۲۰ تا ۵۰ میلیون تومان','۵۰ تا ۱۰۰ میلیون تومان','بیشتر از ۱۰۰ میلیون تومان'].map(value=>`<option ${draft.budget===value?'selected':''}>${value}</option>`).join('')}</select></div></div>`:''}
        ${step===2?choices(goals,'goal')+`<p class="entry-demo-note">پاسخ‌ها در پروفایل پروژه می‌مانند. اطلاعات بازار در این دمو، نمونه‌اند.</p>`:''}
      </section>
      <footer class="entry-footer">
        <form class="entry-composer" data-form="entry" novalidate>
          <label class="sr-only" for="entryAnswer">${step===0?'توضیح ایده':step===1?'توضیح مشتری':'توضیح هدف'}</label>
          <textarea id="entryAnswer" data-entry-field="${fields[step]}" maxlength="2000" rows="2" placeholder="${placeholders[step]}" aria-describedby="entryError">${esc(draft[fields[step]])}</textarea>
          <div class="entry-composer-actions"><div class="entry-composer-tools"><button type="button" class="entry-example-shortcut" data-entry-action="suggest" aria-label="یک نمونه برای این مرحله">${icon('plus')}</button><span>${icon('shield')}شروع با اطلاعات خودت</span></div><button class="entry-send" type="submit" aria-label="${step===2?'ورود به فضای کاری':'مرحله بعد'}">${icon(step===2?'spark':'arrow')}</button></div>
          <p id="entryError" class="entry-error" role="alert" hidden></p>
        </form>
        <div class="entry-footer-note"><span>${step===2?'با تکمیل این مرحله وارد فضای تحلیل می‌شوی.':'با Enter ادامه بده · Shift + Enter برای خط جدید'}</span><button type="button" data-entry-action="sample">مستقیم به نمونه برو</button></div>
      </footer>
    </main>`;
  }

  function captureFields() {
    document.querySelectorAll('[data-entry-field]').forEach(field => { draft[field.dataset.entryField]=field.value; });
    persist();
  }
  function error(message,focus) {
    const element=document.querySelector('#entryError');
    element.textContent=message; element.hidden=false;
    document.querySelector(focus)?.focus();
  }
  function next() {
    captureFields(); const step=stepIndex();
    if(step===0 && !isValidIdea()) { error('ایده‌ات را در یک جملهٔ کوتاه بنویس؛ حداقل ۵ نویسه.','#entryAnswer'); return; }
    if(step===1 && !isValidCustomer()) { error('نوع مشتری را انتخاب کن یا کمی درباره‌اش بنویس.','#entryAnswer'); return; }
    if(step===2 && !draft.goal) { error('یکی از هدف‌های بررسی را انتخاب کن.','[data-entry-key="goal"]'); return; }
    if(step<2) callbacks.navigate?.(stepRoute(step+1));
    else { draft.completed=true;persist();callbacks.complete?.(brief()); }
  }
  function brief() {
    const {theme,...data}=draft;
    return {...data, audienceLabel:({consumer:'خریدار نهایی',business:'کسب‌وکارها',both:'هر دو گروه'})[draft.audience]||'',goalLabel:({market:'شناخت بازار',competitors:'مقایسه رقبا',opportunity:'پیدا کردن فرصت'})[draft.goal]||''};
  }

  document.addEventListener('input', event => {
    const field=event.target.closest('[data-entry-field]');
    if(!field)return;
    draft[field.dataset.entryField]=field.value;persist();
    const message=document.querySelector('#entryError');if(message)message.hidden=true;
  });
  document.addEventListener('change', event => {
    const field=event.target.closest('[data-entry-field]');
    if(field){draft[field.dataset.entryField]=field.value;persist();}
  });
  document.addEventListener('submit', event => {
    if(!event.target.matches('[data-form="entry"]'))return;
    event.preventDefault();next();
  });
  document.addEventListener('keydown', event => {
    if(event.target.id==='entryAnswer' && event.key==='Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault(); event.target.closest('form').requestSubmit();
    }
  });
  document.addEventListener('click', event => {
    const control=event.target.closest('[data-entry-action]');if(!control)return;
    event.preventDefault();const action=control.dataset.entryAction;
    if(action==='theme'){captureFields();draft.theme=draft.theme==='dark'?'light':'dark';persist();refresh('[data-entry-action="theme"]');return;}
    if(action==='motion'){
      if(reducedMotion.matches)return;
      paused=!paused;document.querySelector('.solar-portal')?.classList.toggle('is-paused',paused);
      control.setAttribute('aria-pressed',String(paused));control.setAttribute('aria-label',motionLabel());control.title=motionLabel();control.innerHTML=svg(motionIcon(),'solar-control-mark');return;
    }
    if(action==='start'){draft.source=control.dataset.entrySource||'';persist();callbacks.navigate?.(stepRoute(0));return;}
    if(action==='portal'){captureFields();callbacks.navigate?.('#/');return;}
    if(action==='back'){captureFields();const step=stepIndex();callbacks.navigate?.(step>0?stepRoute(step-1):'#/');return;}
    if(action==='step'){captureFields();callbacks.navigate?.(stepRoute(guard(Math.min(stepIndex(),+control.dataset.entryStep))));return;}
    if(action==='sample'){captureFields();callbacks.sample?.();return;}
    if(action==='choice'){
      captureFields();const key=control.dataset.entryKey;
      if(!['audience','goal'].includes(key))return;
      draft[key]=control.dataset.entryValue;persist();refresh(`[data-entry-key="${key}"][data-entry-value="${draft[key]}"]`);return;
    }
    if(action==='example'||action==='suggest'){
      const step=stepIndex(),answer=document.querySelector('#entryAnswer');
      const value=action==='example'?'می‌خواهم یک '+control.dataset.entryValue+' راه‌اندازی کنم.':[
        'می‌خواهم یک برند پوشاک مینیمال برای خانم‌های شاغل راه‌اندازی کنم.',
        'خانم‌های شاغل ۲۵ تا ۳۵ سال که برای خرید لباس روزمره، کیفیت و سادگی برایشان مهم است.',
        'می‌خواهم بدانم چه پیشنهادی نسبت به رقبا متمایز است و از کجا شروع کنم.'
      ][step];
      answer.value=value;draft[answer.dataset.entryField]=value;persist();const message=document.querySelector('#entryError');if(message)message.hidden=true;answer.focus();return;
    }
  });
  reducedMotion.addEventListener('change',()=>{if(document.querySelector('.solar-portal'))refresh();});
  window.NAMA_ENTRY={portal,discovery,guard,brief,theme:()=>draft.theme,init:value=>{callbacks=value;},reset:()=>{draft={idea:'',customer:'',goalNote:'',audience:'',market:'',budget:'',goal:'',theme:draft.theme,completed:false,source:''};persist();}};
})();

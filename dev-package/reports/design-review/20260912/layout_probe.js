(() => {
  const visible = el => {const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};
  const rect = r => ({x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height),right:Math.round(r.right)});
  const selector = el => el.tagName.toLowerCase()+(typeof el.className==='string'&&el.className.trim()?'.'+el.className.trim().split(/\s+/).join('.'):'');
  const properties=['fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','display','gap','padding','margin','border','borderRadius','backgroundColor','color','width','minWidth','maxWidth','overflowX','whiteSpace','outlineStyle','outlineWidth','transitionDuration'];
  const describe = el => {const cs=getComputedStyle(el);return {selector:selector(el),text:(el.innerText||el.getAttribute('aria-label')||'').trim().slice(0,70),rect:rect(el.getBoundingClientRect()),style:Object.fromEntries(properties.map(p=>[p,cs[p]])),scrollWidth:el.scrollWidth,clientWidth:el.clientWidth};};
  const all=[...document.querySelectorAll('body *')].filter(visible);
  const target='button,select,input,textarea,h1,h2,.page-head,.axis-bar,.axis-pick,.dash-open-catalog,.dash-lead,.fchips,.modal,.modal-foot,.modal-act,.settabs,.preview-section,.pj-toolbar';
  return {
    url:location.href,title:document.title,screen:document.querySelector('[data-screen]')?.getAttribute('data-screen'),viewport:{width:innerWidth,height:innerHeight},
    document:{width:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,bodyScrollWidth:document.body.scrollWidth},
    fonts:{status:document.fonts.status,pretendard:document.fonts.check('14px "Pretendard Variable"'),body:getComputedStyle(document.body).fontFamily},
    stylesheets:[...document.styleSheets].map(s=>s.href),
    elements:[...document.querySelectorAll(target)].filter(visible).map(describe),
    outsideViewport:all.filter(el=>{const r=el.getBoundingClientRect();return r.right>innerWidth+2||r.left< -2;}).slice(0,60).map(describe),
    overflowingBoxes:all.filter(el=>el.clientWidth>0&&el.scrollWidth>el.clientWidth+2).slice(0,60).map(describe),
    links:[...document.querySelectorAll('a[href]')].filter(visible).map(el=>({text:el.textContent.trim().slice(0,50),href:el.getAttribute('href')})),
  };
})()

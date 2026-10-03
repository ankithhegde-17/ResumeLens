/* Browser-local signed state: no resume text or provider tokens in cookies. */
document.addEventListener('DOMContentLoaded', async () => {
  const marker = document.querySelector('#workspace-state');
  if (!marker) return;
  const incoming = JSON.parse(marker.textContent);
  const key = 'resumelens.workspace.' + incoming.owner;
  let state = incoming.state;
  let available = true;
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  function notice(message) {
    const box = document.createElement('p');
    box.className = 'alert error'; box.setAttribute('role', 'alert'); box.textContent = message;
    document.querySelector('main').prepend(box);
  }
  function persist(value) {
    state = value;
    try { localStorage.setItem(key, JSON.stringify({state:value, expires:Date.now() + 86400000})); }
    catch { available = false; notice('Browser storage is unavailable or full. Enable storage before uploading; export important results.'); }
  }
  function latest() {
    try {
      const saved=JSON.parse(localStorage.getItem(key) || 'null');
      if (saved && saved.expires>Date.now()) state=saved.state;
    } catch { /* Keep the currently loaded state; storage failure is already shown. */ }
    return state;
  }
  function replace(html) {
    document.open(); document.write(html); document.close();
  }
  function storeHTML(html) {
    const parsed = new DOMParser().parseFromString(html, 'text/html');
    const next = parsed.querySelector('#workspace-state');
    if (next) persist(JSON.parse(next.textContent).state);
  }
  window.ResumeLensWorkspace = {
    decorate(data) { data.set('workspace_state', latest()); },
    save(value) { if (value) persist(value); }
  };
  try {
    // Remove expired/unreachable ResumeLens payloads without touching other apps.
    for (const storedKey of Object.keys(localStorage)) {
      if (!storedKey.startsWith('resumelens.workspace.')) continue;
      let old;
      try { old=JSON.parse(localStorage.getItem(storedKey)); } catch { old=null; }
      if (storedKey!==key || !old || old.expires<=Date.now()) localStorage.removeItem(storedKey);
    }
    const previous = JSON.parse(localStorage.getItem(key) || 'null');
    if (!incoming.loaded && previous && previous.expires > Date.now()) {
      state = previous.state;
      const response = await fetch(location.href, {method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json', 'X-Workspace-Read':'1'},
        body:JSON.stringify({workspace_state:state, csrf_token:csrf})});
      const html = await response.text();
      if (response.ok) { storeHTML(html); replace(html); return; }
      // Do not silently overwrite an invalid or wrong-browser workspace.
      available = false;
      notice('This browser workspace could not be restored. Clear its data in Browser preferences, then start again.');
    } else persist(state);
  } catch {
    available = false;
    notice('Your browser workspace could not be loaded. Enable browser storage or clear ResumeLens data.');
  }
  document.addEventListener('submit', async event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.id === 'career-ai-form' || form.method.toLowerCase() !== 'post') return;
    event.preventDefault(); event.stopImmediatePropagation();
    // A control named "action" masks form.action (review has two action buttons).
    const target=new URL(form.getAttribute('action') || location.href,location.href);
    if (!available && !target.pathname.endsWith('/workspace/clear')) { notice('Enable browser storage before continuing.'); return; }
    const data = new FormData(form);
    if (event.submitter && event.submitter.name) data.append(event.submitter.name,event.submitter.value);
    data.set('workspace_state',latest());
    if (document.body.dataset.hosted === 'true') {
      let bytes=0;
      for (const value of data.values()) bytes += value instanceof File ? value.size : new Blob([value]).size;
      if (bytes > 4 * 1024 * 1024 - 65536) { notice('This upload plus browser history is too large. Use a smaller file or delete older analyses.'); return; }
    }
    const buttons=[...form.querySelectorAll('button')];
    const disabled=buttons.map(button=>button.disabled);
    buttons.forEach(button=>{button.disabled=true;});
    try {
      const response=await fetch(target.href,{method:'POST',body:data,credentials:'same-origin',headers:{'X-Workspace-Client':'1'}});
      if ((response.headers.get('Content-Type') || '').includes('application/json')) {
        const body=await response.json(); persist(body.workspace_state);
        if (body.redirect && available) { location.assign(body.redirect); return; }
        throw new Error(body.error || 'The request could not be completed.');
      }
      const html=await response.text(); storeHTML(html); replace(html);
    } catch (error) {
      notice(error.message || 'Cannot reach ResumeLens. Your browser data has not been removed.');
      buttons.forEach((button,index)=>{button.disabled=disabled[index];});
    }
  },true);
  // Downloads need the same signed browser state but must remain JSON files.
  document.querySelectorAll('a[href$="/download"]').forEach(link=>link.addEventListener('click',async event=>{
    event.preventDefault();
    try {
      const response=await fetch(link.href,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Workspace-Read':'1'},body:JSON.stringify({workspace_state:state,csrf_token:csrf})});
      if (!response.ok) throw new Error('Could not export this analysis.');
      const url=URL.createObjectURL(await response.blob());
      const anchor=document.createElement('a');anchor.href=url;anchor.download='resume-analysis.json';anchor.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(error) { notice(error.message); }
  }));
});

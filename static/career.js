/* Optional career chat: same-origin requests only; untrusted answers are plain text. */
document.addEventListener('DOMContentLoaded', () => {
  const panel = document.querySelector('#career-ai-panel');
  if (!panel) return;
  const toggle = document.querySelector('.career-ai-toggle');
  const form = document.querySelector('#career-ai-form');
  const input = document.querySelector('#career-ai-input');
  const log = panel.querySelector('.career-ai-messages');
  const status = panel.querySelector('.ai-status');
  const retry = panel.querySelector('.ai-retry');
  let busy = false;
  let lastMessage = '';
  const mobile = window.matchMedia('(max-width:600px)');
  let inertBefore = [];
  function modality(value) {
    inertBefore.forEach(([element, previous]) => { element.inert = previous; });
    inertBefore = [];
    panel.setAttribute('aria-modal', String(value && mobile.matches));
    if (value && mobile.matches) {
      document.querySelectorAll('.workspace,.sidebar,.mobile-menu-toggle,.career-ai-toggle,.skip-link').forEach(element => {
        inertBefore.push([element, element.inert]);
        element.inert = true;
      });
    }
  }
  function open(value) {
    panel.hidden = !value;
    toggle.setAttribute('aria-expanded', String(value));
    modality(value);
    if (value) input.focus(); else toggle.focus();
  }
  mobile.addEventListener('change', () => modality(!panel.hidden));
  toggle.addEventListener('click', () => open(panel.hidden));
  panel.querySelector('.career-ai-close').addEventListener('click', () => open(false));
  panel.addEventListener('keydown', e => {
    if (e.key === 'Escape') { e.stopPropagation(); open(false); }
    if (e.key === 'Tab' && mobile.matches) {
      const focusable = [...panel.querySelectorAll('button,input,textarea,[tabindex="0"]')].filter(element => !element.disabled && element.offsetParent !== null && element.type !== 'hidden');
      const first = focusable[0], last = focusable[focusable.length - 1];
      if ((e.shiftKey && document.activeElement === first) || (!e.shiftKey && document.activeElement === last)) {
        e.preventDefault(); (e.shiftKey ? last : first).focus();
      }
    }
  });
  panel.querySelectorAll('.ai-prompt').forEach(button => button.addEventListener('click', () => {
    input.value = button.textContent;
    input.focus();
  }));
  function append(text, user = false) {
    const message = document.createElement('p');
    message.className = user ? 'ai-message user-message' : 'ai-message';
    message.textContent = text;
    log.append(message);
    // Bound the rendered conversation as well as the server-side context.
    while (log.children.length > 20) log.firstElementChild.remove();
    log.scrollTop = log.scrollHeight;
  }
  function setBusy(value) {
    busy = value;
    form.querySelectorAll('button').forEach(button => { button.disabled = value; });
    status.textContent = value ? 'Thinking…' : '';
    log.setAttribute('aria-busy', String(value));
  }
  async function send(message, action = '', isRetry = false) {
    if (busy) return;
    const data = new FormData(form);
    window.ResumeLensWorkspace?.decorate(data);
    data.set('message', message);
    if (action) data.set('action', action);
    if (!action && !isRetry) {
      append(message, true);
      // Clear immediately, including failed sends; Retry retains lastMessage.
      input.value = '';
    }
    lastMessage = message;
    retry.hidden = true;
    setBusy(true);
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 35000);
    try {
      const response = await fetch(form.action, {method: 'POST', body: data, credentials: 'same-origin', signal: controller.signal, headers:{'X-Workspace-Client':'1'}});
      const result = await response.json();
      window.ResumeLensWorkspace?.save(result.workspace_state);
      if (!response.ok) throw new Error(result.error || 'Career AI is unavailable. Try again later.');
      if (action === 'new') { log.replaceChildren(); input.value = ''; }
      append(result.answer);
    } catch (error) {
      append(error.name === 'AbortError' ? 'Career AI took too long. You can retry; curated guides still work.' : (error instanceof SyntaxError ? 'Try later. Career AI is unavailable.' : error.message));
      retry.hidden = action === 'new';
    } finally {
      clearTimeout(timeout);
      setBusy(false);
    }
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    const message = input.value.trim();
    if (message && form.reportValidity()) send(message);
  });
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }
  });
  retry.addEventListener('click', () => send(lastMessage, '', true));
  panel.querySelector('.ai-new').addEventListener('click', () => send('', 'new'));
});

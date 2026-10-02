/* Progressive enhancements; Flask remains responsible for validation and security. */
document.documentElement.classList.add('js');
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const sidebar = document.querySelector('#app-sidebar');
  const scrim = document.querySelector('.sidebar-scrim');
  const workspace = document.querySelector('.workspace');
  const close = document.querySelector('.sidebar-close');
  const mobile = window.matchMedia('(max-width: 900px)');

  const setMenu = (open, restoreFocus = false) => {
    if (!toggle || !sidebar || !scrim) return;
    open = open && mobile.matches;
    sidebar.classList.toggle('is-open', open);
    sidebar.inert = mobile.matches && !open;
    workspace.inert = open;
    scrim.hidden = !open;
    document.body.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.querySelector('.sr-only').textContent = open ? 'Close navigation menu' : 'Open navigation menu';
    if (open) close.focus();
    else if (restoreFocus) toggle.focus();
  };
  if (toggle && sidebar && scrim) {
    setMenu(false);
    toggle.addEventListener('click', () => setMenu(!sidebar.classList.contains('is-open'), true));
    close.addEventListener('click', () => setMenu(false, true));
    scrim.addEventListener('click', () => setMenu(false, true));
    sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
    sidebar.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => setMenu(false)));
    mobile.addEventListener('change', () => setMenu(false));
    document.addEventListener('keydown', event => {
      if (!sidebar.classList.contains('is-open')) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        setMenu(false, true);
      }
      if (event.key === 'Tab') {
        const controls = [...sidebar.querySelectorAll('a[href], button, input:not([type="hidden"])')]
          .filter(element => !element.disabled && element.getClientRects().length);
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    });
  }

  const input = document.querySelector('#resume');
  const info = document.querySelector('#file-info');
  const zone = document.querySelector('#drop-zone');
  const prompt = document.querySelector('#upload-prompt');
  if (input && info && zone && prompt) {
    const updateFile = () => {
      const file = input.files[0];
      input.setCustomValidity('');
      zone.classList.remove('invalid');
      input.removeAttribute('aria-invalid');
      zone.classList.toggle('has-file', Boolean(file));
      if (!file) { info.textContent = ''; prompt.textContent = 'Drop your resume here'; return; }
      let error = '';
      if (!/\.(pdf|jpe?g|png)$/i.test(file.name)) error = 'Choose a PDF, JPG, or PNG file.';
      else if (file.size > 10 * 1024 * 1024) error = 'Choose a file up to 10 MB.';
      else if (!file.size) error = 'This file is empty. Choose another resume.';
      input.setCustomValidity(error);
      zone.classList.toggle('invalid', Boolean(error));
      if (error) input.setAttribute('aria-invalid', 'true');
      info.textContent = file.name + ' · ' + (file.size / 1024 / 1024).toFixed(2) + ' MB' + (error ? ' — ' + error : ' selected');
      prompt.textContent = error ? 'Please choose another file' : 'Ready to review';
    };
    input.addEventListener('change', updateFile);
    input.addEventListener('invalid', event => {
      event.preventDefault();
      zone.classList.add('invalid');
      if (!input.files.length) info.textContent = 'Choose a resume file before continuing.';
      zone.focus();
    });
    zone.addEventListener('click', event => { if (event.target !== input) input.click(); });
    zone.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); input.click(); }
    });
    ['dragenter','dragover'].forEach(name => zone.addEventListener(name, event => {
      event.preventDefault(); zone.classList.add('dragging');
    }));
    ['dragleave','drop'].forEach(name => zone.addEventListener(name, event => {
      event.preventDefault(); zone.classList.remove('dragging');
    }));
    zone.addEventListener('drop', event => {
      if (event.dataTransfer.files.length) {
        input.files = event.dataTransfer.files; updateFile();
      }
    });
  }

  const resetForms = () => document.querySelectorAll('form[data-loading]').forEach(form => {
    delete form.dataset.submitting;
    form.removeAttribute('aria-busy');
    form.querySelectorAll('button').forEach(button => {
      button.classList.remove('busy'); button.removeAttribute('aria-disabled');
    });
    const message = form.querySelector('.loading-message');
    if (message) message.hidden = true;
  });
  document.querySelectorAll('form[data-loading]').forEach(form => {
    form.addEventListener('submit', event => {
      if (form.dataset.submitting) { event.preventDefault(); return; }
      form.dataset.submitting = 'true';
      form.setAttribute('aria-busy', 'true');
      const message = form.querySelector('.loading-message');
      if (message) {
        message.hidden = false;
        message.textContent = event.submitter?.value === 'refresh' ? 'Refreshing skills from your edited text…' : form.dataset.loading;
      }
      // Keep the actual submitter enabled so its action field reaches Flask.
      form.querySelectorAll('button').forEach(button => {
        button.classList.add('busy'); button.setAttribute('aria-disabled','true');
      });
    });
  });
  window.addEventListener('pageshow', resetForms);

  // Career filtering is a regular GET form, usable with or without JavaScript.
});

const navToggle = document.querySelector('.nav-toggle');
const primaryNav = document.querySelector('.primary-nav');

document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

if (navToggle && primaryNav) {
  navToggle.addEventListener('click', () => {
    const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!isOpen));
    primaryNav.classList.toggle('is-open', !isOpen);
  });
  primaryNav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    navToggle.setAttribute('aria-expanded', 'false');
    primaryNav.classList.remove('is-open');
  }));
}

const ariaLauncher = document.querySelector('.aria-chat-launcher');
const ariaDrawer = document.querySelector('.aria-chat-drawer');
const ariaClose = document.querySelector('.aria-chat-close');
if (ariaLauncher && ariaDrawer) {
  const ariaClosedKey = 'smpilot-aria-closed-at';
  const ariaClearDelay = 10 * 60 * 1000;
  let ariaClearTimer;
  const clearAriaConversation = async () => {
    localStorage.removeItem(ariaClosedKey);
    try {
      const body = new URLSearchParams({ csrf: ariaDrawer.dataset.csrf, ajax: '1' });
      const response = await fetch(ariaDrawer.dataset.clearUrl, { method: 'POST', body });
      if (response.ok) {
        const frame = ariaDrawer.querySelector('iframe');
        if (frame) frame.src = `${frame.dataset.src}&cleared=${Date.now()}`;
      }
    } catch (_) {}
  };
  const scheduleAriaClear = (closedAt = Date.now()) => {
    clearTimeout(ariaClearTimer);
    localStorage.setItem(ariaClosedKey, String(closedAt));
    const remaining = Math.max(0, ariaClearDelay - (Date.now() - closedAt));
    ariaClearTimer = setTimeout(clearAriaConversation, remaining);
  };
  const setAriaOpen = (open) => {
    ariaDrawer.hidden = !open;
    ariaLauncher.setAttribute('aria-expanded', String(open));
    if (open) {
      clearTimeout(ariaClearTimer);
      localStorage.removeItem(ariaClosedKey);
      const frame = ariaDrawer.querySelector('iframe');
      if (frame && !frame.src) frame.src = frame.dataset.src;
    } else {
      scheduleAriaClear();
    }
  };
  ariaLauncher.addEventListener('click', () => setAriaOpen(ariaDrawer.hidden));
  if (ariaClose) ariaClose.addEventListener('click', () => setAriaOpen(false));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !ariaDrawer.hidden) setAriaOpen(false);
  });
  const previousClose = Number(localStorage.getItem(ariaClosedKey));
  if (previousClose) scheduleAriaClear(previousClose);
}

const notificationCount = document.querySelector('.notification-count');
if (notificationCount) {
  fetch('/notifications/unread-count', { headers: { Accept: 'application/json' } })
    .then((response) => response.ok ? response.json() : null)
    .then((data) => {
      if (data && data.count > 0) {
        notificationCount.textContent = data.count > 99 ? '99+' : String(data.count);
        notificationCount.hidden = false;
      }
    })
    .catch(() => {});
}

if ('serviceWorker' in navigator && window.isSecureContext) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js', {
    scope: '/',
    updateViaCache: 'none',
  }).then((registration) => registration.update()).catch(() => {}));
}

let deferredInstallPrompt;
const installButton = document.querySelector('.pwa-install');
const installHelp = document.querySelector('.pwa-install-help');
const isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
const isMobileViewport = window.matchMedia('(max-width: 768px)').matches;
const showInstallHelp = () => {
  if (!installHelp) return;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const iosCopy = installHelp.querySelector('.pwa-ios-copy');
  const browserCopy = installHelp.querySelector('.pwa-browser-copy');
  if (iosCopy) iosCopy.hidden = !isIOS;
  if (browserCopy) browserCopy.hidden = isIOS;
  installHelp.hidden = false;
};
if (installButton && isMobileViewport && !isStandalone) installButton.hidden = false;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  if (installButton) installButton.hidden = false;
});
if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredInstallPrompt) {
      showInstallHelp();
      return;
    }
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    installButton.hidden = true;
  });
}
if (installHelp) {
  installHelp.querySelectorAll('.pwa-help-close,.pwa-help-done').forEach((button) => button.addEventListener('click', () => { installHelp.hidden = true; }));
  installHelp.addEventListener('click', (event) => { if (event.target === installHelp) installHelp.hidden = true; });
}
window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  if (installButton) installButton.hidden = true;
});

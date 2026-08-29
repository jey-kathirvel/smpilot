const navToggle = document.querySelector('.nav-toggle');
const primaryNav = document.querySelector('.primary-nav');

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
  const setAriaOpen = (open) => {
    ariaDrawer.hidden = !open;
    ariaLauncher.setAttribute('aria-expanded', String(open));
    if (open) {
      const frame = ariaDrawer.querySelector('iframe');
      if (frame && !frame.src) frame.src = frame.dataset.src;
    }
  };
  ariaLauncher.addEventListener('click', () => setAriaOpen(ariaDrawer.hidden));
  if (ariaClose) ariaClose.addEventListener('click', () => setAriaOpen(false));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !ariaDrawer.hidden) setAriaOpen(false);
  });
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
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  if (installButton) installButton.hidden = false;
});
if (installButton) {
  installButton.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    installButton.hidden = true;
  });
}
window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  if (installButton) installButton.hidden = true;
});

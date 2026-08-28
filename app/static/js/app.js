const navToggle = document.querySelector('.nav-toggle');
const primaryNav = document.querySelector('.primary-nav');

if (navToggle && primaryNav) {
  navToggle.addEventListener('click', () => {
    const isOpen = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!isOpen));
    primaryNav.classList.toggle('is-open', !isOpen);
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

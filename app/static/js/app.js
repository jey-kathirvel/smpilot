const navToggle = document.querySelector('.nav-toggle');
const primaryNav = document.querySelector('.primary-nav');

document.querySelectorAll('form[data-confirm]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
});

const fieldHelp = {
  acceptance_criteria: 'Define the observable conditions that must be true for this work to be accepted as complete.',
  assignee_id: 'Choose the team member currently responsible for moving this work forward.',
  blockers: 'Describe anything preventing progress, including the decision or support needed to unblock it.',
  capacity_hours_per_day: 'Enter the realistic number of hours available for project work on a normal working day.',
  category: 'Group the retrospective observation so recurring improvement themes are easier to identify.',
  confidence: 'Estimate confidence in completing the planned work; lower confidence helps surface risk early.',
  confirm_password: 'Repeat the new password exactly to prevent an accidental password change.',
  content: 'Capture one specific observation so the team can discuss and act on it.',
  current_password: 'Enter your existing password to authorize this security-sensitive change.',
  decision: 'Record the decision the team has agreed to follow.',
  description: 'Add the context, expected outcome, and constraints someone needs to understand this item.',
  display_name: 'Use the name teammates will recognize in assignments, stand-ups, and reports.',
  due_date: 'Choose a realistic date for reviewing or completing this improvement action.',
  email: 'Use the email address associated with this SMPilot account.',
  end_date: 'Set the final calendar day of the sprint; this drives progress and health calculations.',
  epic_id: 'Link this item to the larger epic whose outcome it contributes to.',
  full_name: 'Enter the name teammates should see throughout the workspace.',
  goal: 'State the single outcome the sprint should achieve, not a list of every task.',
  mobile: 'Add a reachable contact number, including the country code when appropriate.',
  name: 'Use a short, clear name that teammates can identify quickly.',
  organization_name: 'Enter the organization or team this account represents.',
  owner: 'Name the person responsible for following through and reporting progress.',
  password: 'Use a strong, unique password that you do not reuse on another service.',
  priority: 'Set priority by delivery impact and urgency, not by who requested the work.',
  project_key: 'Use a short unique code; it becomes the prefix for backlog item IDs.',
  question: 'Ask one focused question and include the project context Aria needs to answer well.',
  relation_type: 'Describe how the selected work items affect or depend on each other.',
  reset_code: 'Enter the time-limited verification code sent during password recovery.',
  result: 'Summarize the outcome produced after the decision was applied.',
  role: 'Select the member’s primary collaboration role; this is not a performance rating.',
  sprint_goal: 'Describe the valuable outcome this proposed sprint should deliver.',
  start_date: 'Set the first calendar day of the sprint; reporting begins from this date.',
  status: 'Choose the state that accurately reflects where the work is now.',
  story_points: 'Estimate relative effort, complexity, and uncertainty—not elapsed hours.',
  target_item_id: 'Select the backlog item affected by this dependency relationship.',
  timezone: 'Choose the timezone used to determine daily updates, dates, and reporting boundaries.',
  title: 'Write a concise, outcome-focused title that is easy to scan in the backlog.',
  today: 'State the most important work planned for today and the intended outcome.',
  type: 'Choose the work-item type that best represents the scope and purpose of this item.',
  unfinished_action: 'Choose whether incomplete sprint work returns to the backlog or keeps its current status.',
  yesterday: 'Summarize completed progress since the previous stand-up; keep it brief and factual.'
};

let fieldHelpIndex = 0;
const firstStandupMember = document.querySelector('.team-standup-list .standup-member');
const standupMembers = document.querySelectorAll('.team-standup-list .standup-member');
standupMembers.forEach((member) => member.addEventListener('toggle', () => {
  if (!member.open) return;
  standupMembers.forEach((other) => { if (other !== member) other.open = false; });
}));
document.querySelectorAll('label input[name], label textarea[name], label select[name]').forEach((control) => {
  if (!fieldHelp[control.name] || ['hidden', 'checkbox', 'radio'].includes(control.type)) return;
  const standupMember = control.closest('.standup-member');
  if (standupMember && standupMember !== firstStandupMember) return;
  const label = control.closest('label');
  if (!label || label.classList.contains('has-field-help')) return;
  const id = `field-help-${++fieldHelpIndex}`;
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'field-help'; button.textContent = '?';
  button.setAttribute('aria-label', `Help for ${control.name.replaceAll('_', ' ')}`);
  button.setAttribute('aria-describedby', id); button.setAttribute('aria-expanded', 'false');
  const help = document.createElement('span');
  help.id = id; help.className = 'field-help-text'; help.setAttribute('role', 'tooltip'); help.textContent = fieldHelp[control.name];
  button.addEventListener('click', (event) => {
    event.preventDefault(); event.stopPropagation();
    const opening = button.getAttribute('aria-expanded') !== 'true';
    document.querySelectorAll('.field-help[aria-expanded="true"]').forEach((item) => item.setAttribute('aria-expanded', 'false'));
    button.setAttribute('aria-expanded', String(opening));
  });
  label.classList.add('has-field-help'); label.append(button, help);
});
document.addEventListener('click', () => document.querySelectorAll('.field-help[aria-expanded="true"]').forEach((item) => item.setAttribute('aria-expanded', 'false')));

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

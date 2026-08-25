const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('#nav');

menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!open));
  menuButton.textContent = open ? 'Menú' : 'Cerrar';
  nav.classList.toggle('open', !open);
});

nav?.addEventListener('click', (event) => {
  if (event.target.matches('a')) {
    nav.classList.remove('open');
    menuButton?.setAttribute('aria-expanded', 'false');
    if (menuButton) menuButton.textContent = 'Menú';
  }
});

document.querySelectorAll('[data-plan]').forEach((link) => {
  link.addEventListener('click', () => {
    const select = document.querySelector('[name="need"]');
    const planInput = document.querySelector('[name="plan"]');
    const plan = link.dataset.plan;
    const option = [...select.options].find((item) => item.textContent.includes(
      plan === 'Nexo Básico' ? 'presentar' : plan === 'Nexo Profesional' ? 'catálogo' : 'más completo'
    ));
    if (option) select.value = option.value;
    if (planInput) planInput.value = plan;
  });
});

document.querySelector('#quote-form')?.addEventListener('submit', (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const message = [
    'Hola, vengo de la página de Punto Nexu.',
    `Mi nombre es ${data.get('name')}.`,
    `Mi negocio: ${data.get('business')}.`,
    `Necesito: ${data.get('need')}.`,
    data.get('plan') ? `Plan que estoy revisando: ${data.get('plan')}.` : ''
  ].filter(Boolean).join('\n');
  window.open(`https://wa.me/573334328971?text=${encodeURIComponent(message)}`, '_blank', 'noopener');
});

document.querySelector('#year').textContent = new Date().getFullYear();

const FORM_ENDPOINT = 'https://formspree.io/f/mnngpyre';

function isConfigured() {
  return FORM_ENDPOINT && !FORM_ENDPOINT.includes('FORM_ENDPOINT_URL');
}

function escapeHTML(str) {
  return str.replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('suggest-form');
  if (!form) return;

  const statusEl = document.getElementById('sf-status');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!isConfigured()) {
      statusEl.textContent = 'Form endpoint not configured yet.';
      statusEl.classList.add('error');
      return;
    }

    if (!form.reportValidity()) {
      statusEl.textContent = 'Please fill the required fields.';
      statusEl.classList.add('error');
      return;
    }

    const formData = {
      name: form.name.value.trim(),
      email: form.email.value.trim(),
      topic: form.topic.value.trim(),
      details: form.details.value.trim()
    };

    statusEl.textContent = 'Sending…';
    statusEl.classList.remove('error', 'success');

    try {
      const response = await fetch(FORM_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      form.reset();
      statusEl.textContent = 'Thanks! Your suggestion has been sent to the L&D team.';
      statusEl.classList.add('success');
    } catch (err) {
      statusEl.textContent = 'Sorry, something went wrong. Please try again later.';
      statusEl.classList.add('error');
      console.error(err);
    }
  });
});

# Suggest a Topic

We welcome ideas for future Learning & Development sessions. Share a topic below and the L&D team will review it.

<form id="suggest-form" class="suggest-form" novalidate>
  <div class="field">
    <label for="sf-name">Your name (optional)</label>
    <input id="sf-name" name="name" type="text" maxlength="80" autocomplete="name">
  </div>
  <div class="field">
    <label for="sf-email">Email (optional, so we can follow up)</label>
    <input id="sf-email" name="email" type="email" maxlength="120" autocomplete="email">
  </div>
  <div class="field required">
    <label for="sf-topic">Topic title *</label>
    <input id="sf-topic" name="topic" type="text" maxlength="140" required>
  </div>
  <div class="field required">
    <label for="sf-details">What would you love to see covered? *</label>
    <textarea id="sf-details" name="details" rows="6" maxlength="1500" required></textarea>
  </div>
  <p class="help">We use a secure, third-party form endpoint so you don't need a GitHub account. No data is stored on this site.</p>
  <button type="submit">Send suggestion</button>
  <p id="sf-status" class="status" role="status" aria-live="polite"></p>
</form>

> **Setup required:** Replace `FORM_ENDPOINT_URL` in `docs/assets/suggest.js` with your provider's POST URL (e.g., a [Formspree](https://formspree.io/) form). Providers like Formspree or StaticForms handle spam filtering and sanitize submissions server-side, protecting against SQL injection and related attacks.

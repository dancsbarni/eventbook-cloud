async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`/api${path}`, {...options, headers, credentials: "same-origin"});
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) throw new Error(data?.error || `Hiba történt (${response.status}).`);
  return data;
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function formatDate(value) {
  return new Date(value).toLocaleString("hu-HU", {dateStyle:"medium",timeStyle:"short"});
}
function formatMoney(value) { return new Intl.NumberFormat("hu-HU").format(value) + " Ft"; }
function showAlert(target, message, type="danger") {
  const el = document.querySelector(target);
  if (el) el.innerHTML = `<div class="alert alert-${type}" role="alert">${escapeHtml(message)}</div>`;
}

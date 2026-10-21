// api.js is loaded dynamically here so pages share one small API helper.
let selectedCategory = "";
async function refreshNav() {
  try {
    const result = await api("/me");
    if (result.user) {
      const auth = document.getElementById("auth-nav"); if (auth) auth.hidden = true;
      const logout = document.getElementById("logout-nav"); if (logout) logout.hidden = false;
      const tickets = document.getElementById("my-tickets-nav"); if (tickets) tickets.hidden = false;
      const admin = document.getElementById("admin-nav"); if (admin) admin.hidden = result.user.role !== "admin";
    }
  } catch(e) { console.error(e); }
}
async function logout() {
  try { await api("/auth/logout", {method:"POST"}); location.href="/"; } catch(e) { alert(e.message); }
}
function setCategory(category) {
  selectedCategory = category;
  document.querySelectorAll(".btn-category").forEach(b => b.classList.toggle("active", b.textContent.trim() === (category || "Mindegyik")));
  loadEvents();
}
async function loadEvents() {
  const grid = document.getElementById("events-grid"); if (!grid) return;
  grid.innerHTML = '<div class="col-12 text-secondary">Betöltés…</div>';
  const params = new URLSearchParams();
  const q = document.getElementById("search")?.value?.trim(); if (q) params.set("q", q);
  if (selectedCategory) params.set("category", selectedCategory);
  try {
    const data = await api(`/events?${params}`);
    if (!data.events.length) { grid.innerHTML = '<div class="col-12"><div class="alert alert-light">Most nincs a keresésnek megfelelő rendezvény.</div></div>'; return; }
    grid.innerHTML = data.events.map(e => {
      const prices = e.ticket_types.map(t => t.price_huf);
      const minPrice = prices.length ? Math.min(...prices) : 0;
      const img = e.image_url || "https://images.unsplash.com/photo-1501386761578-eac5c94b800a?auto=format&fit=crop&w=1200&q=80";
      return `<div class="col-md-6 col-lg-4"><article class="event-card"><img class="event-image" src="${escapeHtml(img)}" alt="${escapeHtml(e.title)}" loading="lazy"><div class="event-body"><div class="event-category mb-2">${escapeHtml(e.category)}</div><h3 class="event-title">${escapeHtml(e.title)}</h3><div class="event-meta mt-3">📍 ${escapeHtml(e.location)}</div><div class="event-meta mt-1">🗓 ${escapeHtml(formatDate(e.start_time))}</div><div class="d-flex justify-content-between align-items-center mt-4"><div><div class="text-secondary small">Jegyek ettől</div><div class="price">${formatMoney(minPrice)}</div></div><button class="btn btn-primary" onclick="viewEvent(${e.id})">Részletek</button></div></div></article></div>`;
    }).join("");
  } catch(e) { grid.innerHTML = `<div class="col-12"><div class="alert alert-danger">${escapeHtml(e.message)}</div></div>`; }
}
async function viewEvent(id) {
  try {
    const {event:e} = await api(`/events/${id}`);
    const options = e.ticket_types.map(t => `<option value="${t.id}">${escapeHtml(t.name)} — ${formatMoney(t.price_huf)} (elérhető: ${t.available})</option>`).join("");
    const qty = prompt(`${e.title}\n${e.description}\n\nVálaszd ki a jegytípust a felugró ablakban.\n${e.ticket_types.map(t => `${t.id}: ${t.name} — ${formatMoney(t.price_huf)}; szabad: ${t.available}`).join("\n")}\n\nJegytípus azonosítója:`);
    if (qty === null) return;
    const ticketId = Number(qty);
    const ticket = e.ticket_types.find(t => t.id === ticketId);
    if (!ticket) { alert("Érvénytelen jegytípus-azonosító."); return; }
    const countRaw = prompt(`Hány darab ${ticket.name} jegyet szeretnél? (1–10)`, "1");
    if (countRaw === null) return;
    const count = Number(countRaw);
    if (!Number.isInteger(count) || count < 1 || count > 10) { alert("1 és 10 közötti egész számot adj meg."); return; }
    const me = await api("/me");
    if (!me.user) { location.href = "login.html"; return; }
    const result = await api("/bookings", {method:"POST", body:JSON.stringify({items:[{ticket_type_id:ticketId, quantity:count}]})});
    alert(`Sikeres foglalás!\nFoglalási kód: ${result.booking.booking_code}\nA QR-kódot a Jegyeim oldalon találod.`);
    location.href = "my-tickets.html";
  } catch(e) { alert(e.message); }
}
async function loadMyTickets() {
  const target = document.getElementById("tickets"); if (!target) return;
  try {
    const me = await api("/me");
    if (!me.user) { location.href = "login.html"; return; }
    const {bookings} = await api("/bookings");
    if (!bookings.length) { target.innerHTML = '<div class="alert alert-light">Még nincs foglalásod. <a href="/">Fedezd fel a rendezvényeket!</a></div>'; return; }
    target.innerHTML = bookings.map(b => `<div class="ticket-card mb-3"><div class="d-flex flex-column flex-md-row justify-content-between gap-3"><div><span class="badge text-bg-success">Visszaigazolva</span><h2 class="h5 fw-bold mt-3">${escapeHtml(b.items.map(i=>i.event_title).join(", "))}</h2><p class="text-secondary mb-1">${escapeHtml(formatDate(b.created_at))}</p><div class="ticket-code">${escapeHtml(b.booking_code)}</div><p class="mt-2 mb-0">${b.items.map(i=>`${escapeHtml(i.ticket_type)} × ${i.quantity}`).join("<br>")}</p><div class="fw-bold mt-3">${formatMoney(b.total_huf)}</div></div><div class="text-center"><img width="150" height="150" alt="Jegy QR-kód" src="/api/bookings/${encodeURIComponent(b.booking_code)}/qr"><div class="small text-secondary mt-2">Belépéskor mutasd fel</div></div></div></div>`).join("");
  } catch(e) { target.innerHTML = `<div class="alert alert-danger">${escapeHtml(e.message)}</div>`; }
}
async function loadAdmin() {
  const eventsTarget = document.getElementById("admin-events"); if (!eventsTarget) return;
  try {
    const me = await api("/me");
    if (!me.user || me.user.role !== "admin") { document.getElementById("admin-alert").innerHTML = '<div class="alert alert-warning">Ehhez az oldalhoz admin jogosultság szükséges. Regisztrálj, majd a README szerint állítsd be az admin szerepkört.</div>'; return; }
    const [stats, eventData, bookingData] = await Promise.all([api("/admin/stats"), api("/events"), api("/admin/bookings")]);
    document.getElementById("stats").innerHTML = [["Rendezvények",stats.events],["Foglalások",stats.bookings],["Eladott jegyek",stats.tickets_sold],["Foglalási érték",formatMoney(stats.booking_value_huf)]].map(([l,v])=>`<div class="col-6 col-lg-3"><div class="stat-card"><div class="text-secondary small">${l}</div><div class="stat-value">${v}</div></div></div>`).join("");
    eventsTarget.innerHTML = `<div class="table-responsive"><table class="table"><thead><tr><th>Rendezvény</th><th>Helyszín</th><th>Dátum</th><th>Állapot</th><th></th></tr></thead><tbody>${eventData.events.map(e=>`<tr><td class="fw-semibold">${escapeHtml(e.title)}</td><td>${escapeHtml(e.location)}</td><td>${escapeHtml(formatDate(e.start_time))}</td><td>${escapeHtml(e.status)}</td><td><button class="btn btn-sm btn-outline-danger" onclick="archiveEvent(${e.id})">Archiválás</button></td></tr>`).join("")}</tbody></table></div>`;
    document.getElementById("admin-bookings").innerHTML = bookingData.bookings.length ? `<div class="table-responsive"><table class="table"><thead><tr><th>Kód</th><th>Vásárló</th><th>Jegyek</th><th>Összeg</th></tr></thead><tbody>${bookingData.bookings.map(b=>`<tr><td class="ticket-code">${escapeHtml(b.booking_code)}</td><td>${escapeHtml(b.customer_name)}<br><small class="text-secondary">${escapeHtml(b.customer_email)}</small></td><td>${b.items.reduce((n,i)=>n+i.quantity,0)}</td><td>${formatMoney(b.total_huf)}</td></tr>`).join("")}</tbody></table></div>` : '<p class="text-secondary">Még nincs foglalás.</p>';
  } catch(e) { document.getElementById("admin-alert").innerHTML = `<div class="alert alert-danger">${escapeHtml(e.message)}</div>`; }
  const form = document.getElementById("event-form");
  if (form) form.onsubmit = async ev => {
    ev.preventDefault();
    const f = new FormData(form);
    const payload = {title:f.get("title"),location:f.get("location"),category:f.get("category"),start_time:new Date(f.get("start_time")).toISOString(),description:f.get("description"),ticket_types:[{name:"Normál",price_huf:Number(f.get("price_huf")),capacity:Number(f.get("capacity"))}]};
    try { await api("/events",{method:"POST",body:JSON.stringify(payload)}); showAlert("#admin-alert","Rendezvény létrehozva.","success"); form.reset(); await loadAdmin(); }
    catch(e) { showAlert("#admin-alert",e.message); }
  };
}
async function archiveEvent(id) {
  if (!confirm("Biztosan archiválod ezt a rendezvényt?")) return;
  try { await api(`/events/${id}`,{method:"DELETE"}); await loadAdmin(); }
  catch(e) { showAlert("#admin-alert",e.message); }
}
document.addEventListener("DOMContentLoaded", () => { refreshNav(); loadEvents(); });

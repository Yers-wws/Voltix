'use strict';
const LOCAL_API = 'http://127.0.0.1:8000/api';
const REMOTE_API = 'https://dummyjson.com';
let API = LOCAL_API;
const CATEGORIES = { smartphones: 'Smartphones', laptops: 'Laptops', tablets: 'Tablets', 'mobile-accessories': 'Accessories' };
const FREE_SHIPPING_FROM = 500, SHIPPING = 15, PROMO = { code: 'TECH10', off: 0.10 };
const $ = (s, r = document) => r.querySelector(s);

/* ---- localStorage helpers (safe if storage is blocked) ---- */
const store = {
  get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } }
};
const state = {
  products: [],
  wish: store.get('vx_wish', []),          // array of product ids
  cart: store.get('vx_cart', []),          // array of { id, qty }
  promo: store.get('vx_promo', false)
};
let rerender = () => {};                    // each page sets its own render function

const money = n => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
const salePrice = p => Math.round(p.price * (1 - p.discountPercentage / 100) * 100) / 100;
const byId = id => state.products.find(p => p.id === id);

/* ---- DOM helper: el('div', {class:'x', onclick:fn}, child, 'text') ---- */
function el(tag, props = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === null || v === false) continue;
    if (k === 'class') n.className = v;
    else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
    else n.setAttribute(k, v);
  }
  n.append(...kids);
  return n;
}

/* ---- UI helpers ---- */
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast.id);
  toast.id = setTimeout(() => t.classList.remove('show'), 2200);
}
function showStatus(box, kind, text, retry) {            // kind: loading | error | empty
  const d = el('div', { class: 'status ' + kind }, kind === 'loading' ? el('span', { class: 'spinner' }) : '', text);
  if (retry) d.append(el('button', { class: 'btn primary', onclick: retry }, 'Try again'));
  box.replaceChildren(d);
  return d;
}
const cartCount = () => state.cart.reduce((n, l) => n + l.qty, 0);
function updateBadges() {
  const v = { wish: state.wish.length, cart: cartCount(), products: state.products.length || '…' };
  document.querySelectorAll('[data-count]').forEach(n => { n.textContent = v[n.dataset.count]; });
}
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  $('#themeBtn').textContent = t === 'dark' ? '☀️' : '🌙';
}

/* ---- external data: fetch() for several categories at once ---- */
async function loadProducts() {
  if (state.products.length) return state.products;
  try {
    const results = await Promise.all(Object.keys(CATEGORIES).map(async cat => {
      const res = await fetch(`${API}/products/category/${cat}?limit=100`);
      if (!res.ok) throw new Error('Server answered ' + res.status);
      return (await res.json()).products;
    }));
    state.products = results.flat();
  } catch (err) {
    if (API !== REMOTE_API) {
      console.warn('Local FastAPI backend not reachable, falling back to dummyjson:', err);
      API = REMOTE_API;
      return loadProducts();
    }
    throw err;
  }
  updateBadges();
  return state.products;
}

/* ---- wishlist and cart ---- */
function toggleWish(p) {
  const on = state.wish.includes(p.id);
  state.wish = on ? state.wish.filter(id => id !== p.id) : [...state.wish, p.id];
  store.set('vx_wish', state.wish);
  updateBadges();
  toast(on ? 'Removed from wishlist' : 'Saved to wishlist');
  rerender();
}
function saveCart() { store.set('vx_cart', state.cart); store.set('vx_promo', state.promo); updateBadges(); }
function addToCart(p, qty = 1) {
  if (p.stock < 1) return toast('Sorry, this product is out of stock');
  const line = state.cart.find(l => l.id === p.id);
  const next = Math.min((line?.qty || 0) + qty, p.stock);
  if (line) line.qty = next; else state.cart.push({ id: p.id, qty: next });
  saveCart();
  rerender();
  toast(`${p.title} added to cart`);
}
function cartTotals() {
  const subtotal = state.cart.reduce((s, l) => s + salePrice(byId(l.id) || { price: 0, discountPercentage: 0 }) * l.qty, 0);
  const discount = state.promo ? subtotal * PROMO.off : 0;
  const after = subtotal - discount;
  const shipping = !state.cart.length || after >= FREE_SHIPPING_FROM ? 0 : SHIPPING;
  return { subtotal, discount, shipping, total: after + shipping };
}

/* ---- product card and details dialog ---- */
function wishButton(p) {
  const on = state.wish.includes(p.id);
  return el('button', {
    class: 'btn fav' + (on ? ' on' : ''), 'aria-pressed': String(on), 'aria-label': 'Wishlist: ' + p.title,
    onclick: e => { toggleWish(p); const now = state.wish.includes(p.id); const b = e.currentTarget;
      b.classList.toggle('on', now); b.setAttribute('aria-pressed', String(now)); b.textContent = now ? '♥' : '♡'; }
  }, on ? '♥' : '♡');
}
function stockLabel(p) {
  if (p.stock < 1) return el('p', { class: 'stock out' }, 'Out of stock');
  if (p.stock <= 10) return el('p', { class: 'stock low' }, `Only ${p.stock} left`);
  return el('p', { class: 'stock in' }, 'In stock');
}
function priceBlock(p) {
  const kids = [el('strong', {}, money(salePrice(p)))];
  if (p.discountPercentage >= 1) kids.push(el('s', {}, money(p.price)));
  return el('p', { class: 'price' }, ...kids);
}
function productCard(p) {
  return el('article', { class: 'card' },
    p.discountPercentage >= 1 ? el('span', { class: 'badge' }, `-${Math.round(p.discountPercentage)}%`) : '',
    el('img', { src: p.thumbnail, alt: p.title, loading: 'lazy' }),
    el('div', { class: 'card-body' },
      el('p', { class: 'brand' }, p.brand || CATEGORIES[p.category] || p.category),
      el('h3', {}, p.title),
      el('p', { class: 'rating' }, `★ ${p.rating.toFixed(1)}`),
      priceBlock(p), stockLabel(p),
      el('div', { class: 'card-actions' },
        el('button', { class: 'btn', onclick: () => openModal(p) }, 'Details'),
        el('button', { class: 'btn primary', disabled: p.stock < 1 ? '' : null, onclick: () => addToCart(p) }, 'Add to cart'),
        wishButton(p))));
}
function openModal(p) {
  const d = $('#modal');
  const main = el('img', { class: 'main-img', src: p.images?.[0] || p.thumbnail, alt: p.title });
  const thumbs = el('div', { class: 'thumbs' });
  (p.images || []).slice(0, 5).forEach((src, i) => {
    const b = el('button', { type: 'button', 'aria-label': `Photo ${i + 1}`, 'aria-current': String(i === 0),
      onclick: () => { main.src = src; thumbs.querySelectorAll('button').forEach(x => x.setAttribute('aria-current', 'false')); b.setAttribute('aria-current', 'true'); } },
      el('img', { src, alt: '' }));
    thumbs.append(b);
  });
  const specs = [['Brand', p.brand], ['Category', CATEGORIES[p.category]], ['Warranty', p.warrantyInformation],
    ['Shipping', p.shippingInformation], ['Return policy', p.returnPolicy], ['SKU', p.sku]].filter(r => r[1]);
  let qty = 1;
  const out = el('output', {}, '1');
  const setQty = n => { qty = Math.max(1, Math.min(p.stock || 1, n)); out.textContent = qty; };
  d.replaceChildren(
    el('button', { class: 'icon-btn close', 'aria-label': 'Close', onclick: () => d.close() }, '✕'),
    main, thumbs,
    el('div', { class: 'modal-body' },
      el('h2', {}, p.title),
      el('p', { class: 'rating' }, `★ ${p.rating.toFixed(1)} · ${(p.reviews || []).length} reviews`),
      priceBlock(p), stockLabel(p),
      el('p', {}, p.description),
      el('table', { class: 'specs' }, ...specs.map(([k, v]) => el('tr', {}, el('th', {}, k), el('td', {}, v)))),
      ...((p.reviews || []).length ? [el('h4', {}, 'Customer reviews'),
        ...p.reviews.slice(0, 3).map(r => el('div', { class: 'review' }, el('p', {}, `${'★'.repeat(r.rating)} ${r.reviewerName}`), el('p', { class: 'muted' }, r.comment)))] : []),
      el('div', { class: 'card-actions' },
        el('span', { class: 'qty' },
          el('button', { type: 'button', 'aria-label': 'Decrease quantity', onclick: () => setQty(qty - 1) }, '−'), out,
          el('button', { type: 'button', 'aria-label': 'Increase quantity', onclick: () => setQty(qty + 1) }, '+')),
        el('button', { class: 'btn primary', disabled: p.stock < 1 ? '' : null, onclick: () => addToCart(p, qty) }, 'Add to cart'),
        wishButton(p))));
  if (!d.open) d.showModal();
}
function fillGrid(box, list, emptyText) {
  if (!list.length) return showStatus(box, 'empty', emptyText);
  box.replaceChildren(...list.map(productCard));
}

/* ---- page: home ---- */
function initHome() {
  const daily = $('#daily'), top = $('#top');
  const render = () => {
    const all = state.products;
    const deal = [...all].sort((a, b) => b.discountPercentage - a.discountPercentage)[new Date().getDate() % 5];
    daily.replaceChildren(productCard(deal));
    fillGrid(top, [...all].filter(p => p.stock > 0).sort((a, b) => b.discountPercentage - a.discountPercentage).slice(5, 8), 'No products found.');
  };
  const load = async () => {
    showStatus(daily, 'loading', 'Loading today’s deal…');
    showStatus(top, 'loading', 'Loading discounts…');
    try { await loadProducts(); rerender = render; render(); }
    catch { showStatus(daily, 'error', 'Products did not load. Check your internet connection.', load); top.replaceChildren(); }
  };
  load();
}

/* ---- page: catalog (search, filter, sort) ---- */
function initProducts() {
  const grid = $('#grid'), q = $('#search'), cat = $('#category'), brand = $('#brand'), so = $('#sort');
  const max = $('#maxPrice'), maxOut = $('#maxOut'), stock = $('#inStock'), ow = $('#onlyWish'), count = $('#count');
  const saved = store.get('vx_filters', {});
  const params = new URLSearchParams(location.search);
  q.value = params.get('q') || '';
  so.value = saved.sort || 'rating';
  stock.checked = !!saved.inStock;
  ow.checked = !!saved.onlyWish;
  const sorts = {
    rating: (a, b) => b.rating - a.rating,
    priceAsc: (a, b) => salePrice(a) - salePrice(b),
    priceDesc: (a, b) => salePrice(b) - salePrice(a),
    discount: (a, b) => b.discountPercentage - a.discountPercentage,
    name: (a, b) => a.title.localeCompare(b.title)
  };
  const render = () => {
    const term = q.value.trim().toLowerCase();
    const limit = Number(max.value);
    maxOut.textContent = limit >= Number(max.max) ? 'any' : money(limit);
    const list = state.products.filter(p =>
      (!term || [p.title, p.brand, p.category, ...(p.tags || [])].join(' ').toLowerCase().includes(term)) &&
      (!cat.value || p.category === cat.value) && (!brand.value || p.brand === brand.value) &&
      (limit >= Number(max.max) || salePrice(p) <= limit) &&
      (!stock.checked || p.stock > 0) && (!ow.checked || state.wish.includes(p.id))
    ).sort(sorts[so.value]);
    count.textContent = `Showing ${list.length} of ${state.products.length} products`;
    fillGrid(grid, list, ow.checked && !state.wish.length ? 'Your wishlist is empty. Tap ♡ on a product.' : 'No products match. Clear the search or relax a filter.');
    store.set('vx_filters', { sort: so.value, inStock: stock.checked, onlyWish: ow.checked });
  };
  [q, max].forEach(c => c.addEventListener('input', render));
  [cat, brand, so, stock, ow].forEach(c => c.addEventListener('change', render));
  const load = async () => {
    showStatus(grid, 'loading', 'Loading products…');
    try {
      const all = await loadProducts();
      Object.entries(CATEGORIES).forEach(([v, t]) => cat.append(el('option', { value: v }, t)));
      [...new Set(all.map(p => p.brand).filter(Boolean))].sort().forEach(b => brand.append(el('option', { value: b }, b)));
      const top = Math.ceil(Math.max(...all.map(salePrice)) / 100) * 100;
      max.max = top; max.value = top;
      if (CATEGORIES[params.get('cat')]) cat.value = params.get('cat');
      rerender = render; render();
    } catch { count.textContent = ''; showStatus(grid, 'error', 'Products did not load. Check your internet connection.', load); }
  };
  load();
}

/* ---- page: cart (lines, totals, promo, checkout via POST) ---- */
function initCart() {
  const lines = $('#lines'), totals = $('#totals'), wishBox = $('#wish'), form = $('#checkout'), btn = $('#placeBtn');
  const renderLines = () => {
    if (!state.cart.length) {
      return showStatus(lines, 'empty', 'Your cart is empty.').append(el('a', { class: 'btn primary', href: 'products.html' }, 'Browse the catalog'));
    }
    lines.replaceChildren(...state.cart.map(l => {
      const p = byId(l.id); if (!p) return '';
      const change = n => { l.qty = Math.max(1, Math.min(p.stock, l.qty + n)); saveCart(); rerender(); };
      return el('div', { class: 'line' },
        el('img', { src: p.thumbnail, alt: p.title }),
        el('div', {}, el('h3', {}, p.title), el('p', { class: 'muted' }, `${money(salePrice(p))} each`),
          el('span', { class: 'qty' },
            el('button', { type: 'button', 'aria-label': 'Decrease quantity of ' + p.title, onclick: () => change(-1) }, '−'),
            el('output', {}, String(l.qty)),
            el('button', { type: 'button', 'aria-label': 'Increase quantity of ' + p.title, onclick: () => change(1) }, '+'))),
        el('div', { class: 'line-end' }, el('strong', {}, money(salePrice(p) * l.qty)),
          el('button', { class: 'icon-btn', 'aria-label': 'Remove ' + p.title,
            onclick: () => { state.cart = state.cart.filter(x => x.id !== l.id); saveCart(); rerender(); } }, '✕')));
    }));
  };
  const renderTotals = () => {
    const t = cartTotals();
    const row = (k, v, cls = '') => el('div', { class: cls }, el('dt', {}, k), el('dd', {}, v));
    totals.replaceChildren(row('Subtotal', money(t.subtotal)),
      ...(state.promo ? [row(`Promo ${PROMO.code}`, '−' + money(t.discount))] : []),
      row('Shipping', t.shipping ? money(t.shipping) : 'Free'),
      row('Total', money(t.total), 'total'));
    btn.disabled = !state.cart.length;
  };
  const renderWish = () => {
    if (!state.wish.length) showStatus(wishBox, 'empty', 'No saved products yet.');
    else fillGrid(wishBox, state.products.filter(p => state.wish.includes(p.id)), 'Saved products could not be found.');
  };
  rerender = () => { renderLines(); renderTotals(); renderWish(); };

  $('#promoForm').addEventListener('submit', e => {
    e.preventDefault();
    const input = $('#promo');
    if (input.value.trim().toUpperCase() === PROMO.code) { state.promo = true; saveCart(); renderTotals(); toast('Promo code applied: 10% off'); }
    else toast('That promo code is not valid');
    input.value = '';
  });

  const rules = {
    name: v => v.trim().length >= 2 || 'Enter your full name',
    email: v => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) || 'Enter a valid email address',
    address: v => v.trim().length >= 6 || 'Enter a delivery address'
  };
  Object.keys(rules).forEach(id => $('#' + id).addEventListener('input', () => { $('#' + id + 'Err').textContent = ''; }));
  form.addEventListener('submit', async e => {
    e.preventDefault();                                           // stay on the page, we send JSON ourselves
    let ok = true;
    for (const [id, rule] of Object.entries(rules)) {
      const res = rule($('#' + id).value);
      $('#' + id + 'Err').textContent = res === true ? '' : res;
      if (res !== true) ok = false;
    }
    if (!ok || !state.cart.length) return;
    btn.disabled = true; btn.textContent = 'Placing order…';        // loading state
    try {
      let order;
      if (API === LOCAL_API) {
        const res = await fetch(`${API}/orders`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_name: $('#name').value.trim(),
            email: $('#email').value.trim(),
            shipping_address: $('#address').value.trim(),
            items: state.cart.map(l => ({ product_id: l.id, quantity: l.qty })),
            promo_code: state.promo ? PROMO.code : null
          })
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Server answered ' + res.status);
        }
        order = await res.json();
      } else {
        const res = await fetch(`${API}/carts/add`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userId: 1, products: state.cart.map(l => ({ id: l.id, quantity: l.qty })) })
        });
        if (!res.ok) throw new Error('Server answered ' + res.status);
        order = await res.json();
      }
      const paid = money(cartTotals().total);
      state.cart = []; state.promo = false; saveCart();
      $('.cart-layout').replaceChildren(el('div', { class: 'order-ok' },
        el('h2', {}, 'Thank you, your order is placed!'),
        el('p', {}, `Order #${order.id} · ${paid}. A confirmation will be sent to ${$('#email').value.trim()}.`),
        el('a', { class: 'btn primary', href: 'products.html' }, 'Continue shopping')));
    } catch (err) {
      toast(err.message || 'Order failed. Check your connection and try again.');
      btn.disabled = false; btn.textContent = 'Place order';
    }
  });

  const load = async () => {
    if (!state.cart.length && !state.wish.length) return rerender();
    showStatus(lines, 'loading', 'Loading your cart…');
    try { await loadProducts(); rerender(); }
    catch { showStatus(lines, 'error', 'Cart did not load. Check your internet connection.', load); }
  };
  load();
}

/* ---- start ---- */
applyTheme(store.get('vx_theme', matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('#themeBtn').addEventListener('click', () => {
  const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(t); store.set('vx_theme', t);
});
$('#modal').addEventListener('click', e => { if (e.target === e.currentTarget) e.currentTarget.close(); });
$('#year').textContent = new Date().getFullYear();
updateBadges();
({ home: initHome, products: initProducts, cart: initCart })[document.body.dataset.page]?.();

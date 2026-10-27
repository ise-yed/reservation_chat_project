/* ═══════════════════════════════════════════════════════
   CONFIG & STATE
═══════════════════════════════════════════════════════ */
const API = '/api/v1';
let authToken = localStorage.getItem('admin_token') || null;
let currentUser = JSON.parse(localStorage.getItem('admin_user') || 'null');
let currentPage = 'dashboard';
let globalSearchQuery = '';

// Cached reference lists for dropdowns
let cachedOrgs = [];
let cachedCategories = [];

const WEEKDAYS_FA = {
  0: 'دوشنبه (Monday)',
  1: 'سه‌شنبه (Tuesday)',
  2: 'چهارشنبه (Wednesday)',
  3: 'پنج‌شنبه (Thursday)',
  4: 'جمعه (Friday)',
  5: 'شنبه (Saturday)',
  6: 'یکشنبه (Sunday)',
};

const APPT_STATUS_MAP = {
  pending:               { label: 'در انتظار تأیید', cls: 'badge-amber'  },
  confirmed:             { label: 'تأیید شده',       cls: 'badge-green'  },
  cancelled_by_customer: { label: 'لغو توسط بیمار',  cls: 'badge-rose'   },
  cancelled_by_provider: { label: 'لغو توسط پزشک',   cls: 'badge-rose'   },
  completed:             { label: 'انجام شده',       cls: 'badge-cyan'   },
  no_show:               { label: 'غیبت بیمار',      cls: 'badge-gray'   },
};

const PAYMENT_STATUS_MAP = {
  pending:   { label: 'در انتظار پرداخت', cls: 'badge-amber' },
  paid:      { label: 'پرداخت شده',       cls: 'badge-green' },
  failed:    { label: 'ناموفق',           cls: 'badge-rose'  },
  cancelled: { label: 'لغو شده',          cls: 'badge-gray'  },
  refunded:  { label: 'بازپرداخت شده',    cls: 'badge-cyan'  },
};

const ROLE_MAP = {
  customer:    { label: 'بیمار (Customer)',       cls: 'badge-blue'   },
  provider:    { label: 'پزشک (Provider)',        cls: 'badge-green'  },
  staff:       { label: 'کارمند (Staff)',         cls: 'badge-amber'  },
  org_admin:   { label: 'ادمین سازمان (OrgAdmin)', cls: 'badge-purple' },
  super_admin: { label: 'سوپر ادمین (SuperAdmin)', cls: 'badge-rose'   },
};

/* ═══════════════════════════════════════════════════════
   API HELPER (WITH AUTO TOKEN REFRESH & ERROR PARSER)
═══════════════════════════════════════════════════════ */
async function tryRefreshToken() {
  const refresh = localStorage.getItem('admin_refresh_token');
  if (!refresh) return false;
  try {
    const res = await fetch(API + '/auth/refresh/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data.access) {
      authToken = data.access;
      localStorage.setItem('admin_token', authToken);
      if (data.refresh) localStorage.setItem('admin_refresh_token', data.refresh);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

async function api(method, path, body = null, skipAuth = false, isRetry = false) {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken && !skipAuth) headers['Authorization'] = `Bearer ${authToken}`;
  const opts = { method, headers };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(API + path, opts);

  if (res.status === 401 && !skipAuth) {
    if (!isRetry && (await tryRefreshToken())) {
      return api(method, path, body, skipAuth, true);
    }
    doLogout();
    throw { message: 'نشست کاربری شما منقضی شده است. لطفاً دوباره وارد شوید.' };
  }

  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = text; }
  if (!res.ok) throw data;
  return data;
}

const apiGet    = (path)       => api('GET', path);
const apiPost   = (path, body) => api('POST', path, body);
const apiPatch  = (path, body) => api('PATCH', path, body);
const apiDelete = (path)       => api('DELETE', path);

// Helper to append page_size=100 so DRF returns up to 100 items per page
function withPageSize(path, size = 100) {
  return path + (path.includes('?') ? '&' : '?') + `page_size=${size}`;
}

function formatApiError(err) {
  if (!err) return 'خطای ناشناخته رخ داد';
  if (typeof err === 'string') return err;
  if (err.errors && typeof err.errors === 'object') {
    const parts = [];
    for (const [k, v] of Object.entries(err.errors)) {
      const valStr = Array.isArray(v) ? v.join('، ') : JSON.stringify(v);
      parts.push(`${k === 'non_field_errors' ? '' : k + ': '}${valStr}`);
    }
    if (parts.length) return parts.join(' | ');
  }
  if (err.message) return err.message;
  if (err.detail) return err.detail;
  if (Array.isArray(err.non_field_errors)) return err.non_field_errors.join('، ');
  return JSON.stringify(err);
}

/* ═══════════════════════════════════════════════════════
   AUTH
═══════════════════════════════════════════════════════ */
async function doLogin() {
  const email = document.getElementById('login-email').value.trim();
  const pw    = document.getElementById('login-password').value;
  const btn   = document.getElementById('btn-login-submit');
  const err   = document.getElementById('login-error');
  err.classList.remove('show');

  if (!email || !pw) {
    showErr(err, 'لطفاً ایمیل و رمز عبور را وارد کنید.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'در حال ورود…';
  try {
    const data = await api('POST', '/auth/login/', { email, password: pw }, true);
    authToken = data.tokens?.access || data.access;
    const refreshToken = data.tokens?.refresh || data.refresh;
    localStorage.setItem('admin_token', authToken);
    if (refreshToken) localStorage.setItem('admin_refresh_token', refreshToken);

    const me = await apiGet('/auth/me/');
    const adminRoles = ['staff', 'org_admin', 'super_admin'];
    if (!me.is_staff && !adminRoles.includes(me.role)) {
      showErr(err, 'شما دسترسی ورود به پنل ادمین را ندارید.');
      authToken = null;
      localStorage.removeItem('admin_token');
      localStorage.removeItem('admin_refresh_token');
      return;
    }

    currentUser = me;
    localStorage.setItem('admin_user', JSON.stringify(me));
    initApp();
  } catch (e) {
    showErr(err, formatApiError(e));
  } finally {
    btn.disabled = false;
    btn.textContent = 'ورود به سیستم';
  }
}

function showErr(el, msg) {
  el.textContent = msg;
  el.classList.add('show');
}

document.getElementById('login-password')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

async function doLogout() {
  const refresh = localStorage.getItem('admin_refresh_token');
  if (refresh && authToken) {
    try { await api('POST', '/auth/logout/', { refresh }, false, true); } catch {}
  }
  authToken = null;
  currentUser = null;
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_refresh_token');
  localStorage.removeItem('admin_user');
  document.getElementById('app').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}

function isSuperAdmin() {
  return currentUser?.role === 'super_admin' || currentUser?.is_superuser;
}

async function loadCommonLists() {
  try {
    const orgPath = isSuperAdmin() ? '/organizations/?include_inactive=true' : '/organizations/my/';
    const orgRes = await apiGet(withPageSize(orgPath));
    cachedOrgs = orgRes.results || orgRes || [];
  } catch { cachedOrgs = []; }

  try {
    const catRes = await apiGet(withPageSize('/categories/admin/'));
    cachedCategories = catRes.results || catRes || [];
  } catch { cachedCategories = []; }
}

async function initApp() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = 'flex';

  const fullName = currentUser?.full_name || currentUser?.first_name || currentUser?.email?.split('@')[0] || 'ادمین';
  document.getElementById('user-name').textContent = fullName;
  document.getElementById('user-role').textContent = ROLE_MAP[currentUser?.role]?.label || currentUser?.role || '';
  document.getElementById('user-avatar').textContent = (currentUser?.first_name?.[0] || currentUser?.email?.[0] || 'A').toUpperCase();

  // Hide Users menu for non-super_admin since /api/v1/admin/users/ requires IsSuperAdminUser
  const navUsers = document.getElementById('nav-users');
  if (navUsers) {
    navUsers.style.display = isSuperAdmin() ? 'flex' : 'none';
  }

  await loadCommonLists();
  navigate('dashboard');
}

if (authToken && currentUser) {
  initApp();
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR & GLOBAL SEARCH
═══════════════════════════════════════════════════════ */
function toggleSidebar(force) {
  const sb = document.getElementById('sidebar');
  const ov = document.getElementById('sidebar-overlay');
  const open = typeof force === 'boolean' ? force : !sb.classList.contains('open');
  sb.classList.toggle('open', open);
  ov.classList.toggle('open', open);
}

function onGlobalSearch(val) {
  globalSearchQuery = (val || '').trim().toLowerCase();
  const clearBtn = document.getElementById('global-search-clear');
  if (clearBtn) clearBtn.style.display = globalSearchQuery ? 'inline-block' : 'none';

  const rows = document.querySelectorAll('#page tbody tr');
  rows.forEach(tr => {
    if (tr.querySelector('.empty')) return;
    const text = (tr.innerText || '').toLowerCase();
    tr.style.display = !globalSearchQuery || text.includes(globalSearchQuery) ? '' : 'none';
  });
}

function clearGlobalSearch() {
  const inp = document.getElementById('global-search');
  if (inp) inp.value = '';
  onGlobalSearch('');
}

/* ═══════════════════════════════════════════════════════
   ROUTER
═══════════════════════════════════════════════════════ */
const PAGE_TITLES = {
  dashboard:     'داشبورد آماری',
  users:         'مدیریت کاربران',
  organizations: 'سازمان‌ها (کلینیک‌ها)',
  branches:      'مدیریت شعب',
  providers:     'پزشکان (Providers)',
  offerings:     'خدمات (Offerings)',
  categories:    'تخصص‌های پزشکی',
  availability:  'ساعات کاری و مرخصی پزشکان',
  holidays:      'تعطیلات سازمان',
  appointments:  'مدیریت نوبت‌ها',
  payments:      'مدیریت پرداخت‌ها',
  chats:         'مکالمات چت (Read-Only)',
  notifications: 'لاگ ارسال نوتیفیکیشن‌ها',
};

function navigate(page, params = {}) {
  currentPage = page;
  toggleSidebar(false);
  clearGlobalSearch();

  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-page') === page);
  });
  document.getElementById('topbar-title').textContent = PAGE_TITLES[page] || page;

  const pageEl = document.getElementById('page');
  pageEl.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';

  const routes = {
    dashboard:     renderDashboard,
    users:         renderUsers,
    organizations: renderOrganizations,
    branches:      renderBranches,
    providers:     renderProviders,
    offerings:     renderOfferings,
    categories:    renderCategories,
    availability:  renderAvailability,
    holidays:      renderHolidays,
    appointments:  renderAppointments,
    payments:      renderPayments,
    chats:         renderChats,
    notifications: renderNotifications,
  };

  const fn = routes[page];
  if (fn) fn(params);
}

/* ═══════════════════════════════════════════════════════
   TOAST & MODAL & HELPERS
═══════════════════════════════════════════════════════ */
function toast(msg, type = 'success') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span><span>${escapeHTML(String(msg))}</span>`;
  document.getElementById('toast-container').appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

function openModal(title, bodyHTML, footerHTML = '', large = false) {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHTML;
  document.getElementById('modal-footer').innerHTML = footerHTML;
  const modal = document.getElementById('modal');
  modal.classList.toggle('modal-lg', Boolean(large));
  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}

function closeModalOnBackdrop(e) {
  if (e.target.id === 'modal-overlay') closeModal();
}

function escapeHTML(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function fmtDate(d) {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleString('fa-IR', { dateStyle: 'short', timeStyle: 'short' });
  } catch { return d; }
}

function fmtDateOnly(d) {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleDateString('fa-IR');
  } catch { return d; }
}

function fmtMoney(n) {
  return Number(n || 0).toLocaleString('fa-IR') + ' تومان';
}

function toDatetimeLocalValue(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return '';
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function statusBadge(status, map) {
  const m = map[status] || { label: status || '—', cls: 'badge-gray' };
  return `<span class="badge ${m.cls}">${escapeHTML(m.label)}</span>`;
}

function paginateLocal(items, page, perPage = 20) {
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.min(Math.max(1, page), pages);
  const slice = items.slice((safePage - 1) * perPage, safePage * perPage);
  return { items: slice, total, pages, page: safePage };
}

function renderPagination(p, callbackName) {
  if (p.pages <= 1) return '';
  let btns = '';
  for (let i = 1; i <= p.pages; i++) {
    btns += `<button class="page-btn${i === p.page ? ' active' : ''}" onclick="${callbackName}(${i})">${i}</button>`;
  }
  return `<div class="pagination"><span class="page-info">مجموع: ${p.total} مورد</span>${btns}</div>`;
}

function errorHTML(e) {
  return `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">خطا در بارگذاری اطلاعات</div><div class="empty-sub">${escapeHTML(formatApiError(e))}</div></div>`;
}

/* ═══════════════════════════════════════════════════════
   1. DASHBOARD
═══════════════════════════════════════════════════════ */
let dashboardOrgFilter = '';

async function renderDashboard() {
  const el = document.getElementById('page');
  try {
    const query = dashboardOrgFilter ? `?org_id=${dashboardOrgFilter}` : '';
    const stats = await apiGet(`/admin/dashboard/stats/${query}`);
    const appts  = stats.appointments || {};
    const rev    = stats.revenue      || {};
    const prov   = stats.providers    || {};
    const users  = stats.users        || {};
    const pymts  = stats.payments     || {};
    const recent = stats.recent_appointments || [];

    const bySt   = appts.by_status || {};
    const pyBySt = pymts.by_status || {};

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1>📊 داشبورد</h1>
          <div class="page-header-sub">نگاه کلی به عملکرد کلینیک و وضعیت نوبت‌ها</div>
        </div>
        <div class="header-actions">
          <select class="form-control" style="width:auto;min-width:200px" onchange="dashboardOrgFilter=this.value;renderDashboard()">
            <option value="">همه سازمان‌های مجاز</option>
            ${cachedOrgs.map(o => `<option value="${o.id}" ${dashboardOrgFilter === o.id ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
          </select>
          <button class="btn btn-ghost" onclick="renderDashboard()">🔄 بروزرسانی</button>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card" style="--card-color:var(--accent)">
          <div class="stat-icon">🗓️</div>
          <div class="stat-label">نوبت‌های امروز</div>
          <div class="stat-value">${appts.today ?? 0}</div>
          <div class="stat-sub">${appts.this_month ?? 0} نوبت در این ماه</div>
        </div>
        <div class="stat-card" style="--card-color:var(--green)">
          <div class="stat-icon">💰</div>
          <div class="stat-label">درآمد این ماه</div>
          <div class="stat-value">${(rev.this_month || 0).toLocaleString('fa-IR')}</div>
          <div class="stat-sub">کل درآمد: ${(rev.total || 0).toLocaleString('fa-IR')} تومان</div>
        </div>
        <div class="stat-card" style="--card-color:var(--cyan)">
          <div class="stat-icon">👨‍⚕️</div>
          <div class="stat-label">پزشکان فعال</div>
          <div class="stat-value">${prov.active ?? 0}</div>
          <div class="stat-sub">آماده پذیرش نوبت</div>
        </div>
        <div class="stat-card" style="--card-color:var(--blue)">
          <div class="stat-icon">👤</div>
          <div class="stat-label">بیماران جدید این ماه</div>
          <div class="stat-value">${users.new_patients_this_month ?? 0}</div>
          <div class="stat-sub">کل کاربران: ${users.total ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--green)">
          <div class="stat-icon">✅</div>
          <div class="stat-label">نوبت تأیید شده</div>
          <div class="stat-value">${bySt.confirmed ?? 0}</div>
          <div class="stat-sub">تکمیل شده: ${bySt.completed ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--amber)">
          <div class="stat-icon">⏳</div>
          <div class="stat-label">نوبت در انتظار تأیید</div>
          <div class="stat-value">${bySt.pending ?? 0}</div>
          <div class="stat-sub">غیبت (No-Show): ${bySt.no_show ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--green)">
          <div class="stat-icon">💳</div>
          <div class="stat-label">پرداخت‌های موفق</div>
          <div class="stat-value">${pyBySt.paid ?? 0}</div>
          <div class="stat-sub">در انتظار: ${pyBySt.pending ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--rose)">
          <div class="stat-icon">❌</div>
          <div class="stat-label">پرداخت ناموفق / بازپرداخت</div>
          <div class="stat-value">${pyBySt.failed ?? 0}</div>
          <div class="stat-sub">بازپرداخت شده: ${pyBySt.refunded ?? 0}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <span>🗓️ ۵ نوبت ثبت‌شده اخیر</span>
          <button class="btn btn-ghost btn-sm" onclick="navigate('appointments')">مشاهده همه نوبت‌ها ←</button>
        </div>
        <div class="table-wrapper">
          <table>
            <thead><tr>
              <th>بیمار</th><th>پزشک</th><th>سازمان</th><th>زمان نوبت</th><th>وضعیت</th>
            </tr></thead>
            <tbody>
              ${recent.length === 0
                ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">📭</div><div>نوبتی وجود ندارد</div></div></td></tr>`
                : recent.map(a => `<tr>
                    <td>${escapeHTML((a['customer__first_name'] || '') + ' ' + (a['customer__last_name'] || ''))}<br><span class="td-muted">${escapeHTML(a['customer__email'] || '')}</span></td>
                    <td>${escapeHTML((a['provider__user__first_name'] || '') + ' ' + (a['provider__user__last_name'] || ''))}<br><span class="td-muted">${escapeHTML(a['provider__user__email'] || '')}</span></td>
                    <td>${escapeHTML(a['organization__name'] || '—')}</td>
                    <td class="td-muted">${fmtDate(a.start_at)}</td>
                    <td>${statusBadge(a.status, APPT_STATUS_MAP)}</td>
                  </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

/* ═══════════════════════════════════════════════════════
   2. USERS
═══════════════════════════════════════════════════════ */
let usersData = [];
let usersPage = 1;
let usersSearch = '';
let usersRoleFilter = '';
let usersActiveFilter = '';

async function renderUsers() {
  const el = document.getElementById('page');
  try {
    let url = withPageSize('/admin/users/?ordering=-created_at');
    if (usersRoleFilter) url += `&role=${encodeURIComponent(usersRoleFilter)}`;
    if (usersActiveFilter !== '') url += `&is_active=${usersActiveFilter}`;
    const data = await apiGet(url);
    usersData = data.results || data || [];
    renderUsersTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setUsersPage(p) {
  usersPage = p;
  renderUsersTable();
}

function renderUsersTable() {
  const el = document.getElementById('page');
  const filtered = usersData.filter(u => {
    if (!usersSearch) return true;
    const q = usersSearch.toLowerCase();
    return (
      (u.email || '').toLowerCase().includes(q) ||
      (u.first_name || '').toLowerCase().includes(q) ||
      (u.last_name || '').toLowerCase().includes(q) ||
      (u.phone_number || '').includes(q)
    );
  });

  const pg = paginateLocal(filtered, usersPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>👥 مدیریت کاربران</h1><div class="page-header-sub">${filtered.length} کاربر</div></div>
      ${isSuperAdmin() ? `<button class="btn btn-primary" onclick="openCreateUserModal()">➕ کاربر جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو بر اساس ایمیل، نام یا موبایل…" value="${escapeHTML(usersSearch)}" oninput="usersSearch=this.value;usersPage=1;renderUsersTable()" />
        </div>
        <select onchange="usersRoleFilter=this.value;usersPage=1;renderUsers()">
          <option value="">همه نقش‌ها</option>
          <option value="customer" ${usersRoleFilter === 'customer' ? 'selected' : ''}>بیمار (Customer)</option>
          <option value="provider" ${usersRoleFilter === 'provider' ? 'selected' : ''}>پزشک (Provider)</option>
          <option value="staff" ${usersRoleFilter === 'staff' ? 'selected' : ''}>کارمند (Staff)</option>
          <option value="org_admin" ${usersRoleFilter === 'org_admin' ? 'selected' : ''}>ادمین سازمان (Org Admin)</option>
          <option value="super_admin" ${usersRoleFilter === 'super_admin' ? 'selected' : ''}>سوپر ادمین (Super Admin)</option>
        </select>
        <select onchange="usersActiveFilter=this.value;usersPage=1;renderUsers()">
          <option value="">وضعیت (همه)</option>
          <option value="true" ${usersActiveFilter === 'true' ? 'selected' : ''}>فقط فعال</option>
          <option value="false" ${usersActiveFilter === 'false' ? 'selected' : ''}>فقط غیرفعال</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>ایمیل</th><th>نام و نام خانوادگی</th><th>شماره تماس</th><th>نقش</th><th>وضعیت</th><th>تأیید شده</th><th>تاریخ عضویت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="8"><div class="empty"><div class="empty-icon">👻</div><div>کاربری یافت نشد</div></div></td></tr>`
              : pg.items.map(u => `<tr>
                  <td class="dir-ltr">${escapeHTML(u.email)}</td>
                  <td><strong>${escapeHTML((u.first_name || '') + ' ' + (u.last_name || '')) || '—'}</strong></td>
                  <td class="dir-ltr">${escapeHTML(u.phone_number || '—')}</td>
                  <td>${statusBadge(u.role, ROLE_MAP)}</td>
                  <td>${u.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td>${u.is_verified ? '<span class="badge badge-green">بله</span>' : '<span class="badge badge-amber">خیر</span>'}</td>
                  <td class="td-muted">${fmtDate(u.created_at)}</td>
                  <td>
                    <div class="row-actions">
                      ${isSuperAdmin() ? `<button class="btn btn-ghost btn-sm" onclick="openEditUserModal('${u.id}')">✏️ ویرایش</button>` : ''}
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setUsersPage')}
    </div>
  `;
}

function openCreateUserModal() {
  openModal('ایجاد کاربر جدید', `
    <div class="form-row">
      <div class="form-group"><label class="form-label">ایمیل *</label><input id="fu-email" type="email" class="form-control dir-ltr" placeholder="user@example.com"></div>
      <div class="form-group"><label class="form-label">رمز عبور *</label><input id="fu-pw" type="password" class="form-control dir-ltr" placeholder="حداقل ۸ کاراکتر"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام</label><input id="fu-fn" class="form-control" placeholder="نام"></div>
      <div class="form-group"><label class="form-label">نام خانوادگی</label><input id="fu-ln" class="form-control" placeholder="نام خانوادگی"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="fu-phone" class="form-control dir-ltr" placeholder="0912..."></div>
      <div class="form-group"><label class="form-label">نقش کاربری *</label>
        <select id="fu-role" class="form-control">
          <option value="customer">بیمار (Customer)</option>
          <option value="provider">پزشک (Provider)</option>
          <option value="staff">کارمند (Staff)</option>
          <option value="org_admin">ادمین سازمان (Org Admin)</option>
          <option value="super_admin">سوپر ادمین (Super Admin)</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">وضعیت حساب</label>
        <select id="fu-active" class="form-control">
          <option value="true" selected>فعال</option>
          <option value="false">غیرفعال</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">تأیید شده (Verified)</label>
        <select id="fu-verified" class="form-control">
          <option value="true" selected>بله</option>
          <option value="false">خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateUser()">ذخیره کاربر</button>
  `);
}

async function submitCreateUser() {
  const email = document.getElementById('fu-email').value.trim();
  const password = document.getElementById('fu-pw').value;
  if (!email || !password) {
    toast('ایمیل و رمز عبور الزامی است', 'error');
    return;
  }
  const body = {
    email,
    password,
    first_name: document.getElementById('fu-fn').value.trim(),
    last_name: document.getElementById('fu-ln').value.trim(),
    phone_number: document.getElementById('fu-phone').value.trim(),
    role: document.getElementById('fu-role').value,
    is_active: document.getElementById('fu-active').value === 'true',
    is_verified: document.getElementById('fu-verified').value === 'true',
  };
  try {
    await apiPost('/admin/users/', body);
    closeModal();
    toast('کاربر جدید با موفقیت ایجاد شد');
    await renderUsers();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditUserModal(userId) {
  const u = usersData.find(x => x.id === userId);
  if (!u) return;
  openModal(`ویرایش کاربر: ${u.email}`, `
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام</label><input id="eu-fn" class="form-control" value="${escapeHTML(u.first_name || '')}"></div>
      <div class="form-group"><label class="form-label">نام خانوادگی</label><input id="eu-ln" class="form-control" value="${escapeHTML(u.last_name || '')}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eu-phone" class="form-control dir-ltr" value="${escapeHTML(u.phone_number || '')}"></div>
      <div class="form-group"><label class="form-label">نقش</label>
        <select id="eu-role" class="form-control">
          <option value="customer" ${u.role === 'customer' ? 'selected' : ''}>بیمار (Customer)</option>
          <option value="provider" ${u.role === 'provider' ? 'selected' : ''}>پزشک (Provider)</option>
          <option value="staff" ${u.role === 'staff' ? 'selected' : ''}>کارمند (Staff)</option>
          <option value="org_admin" ${u.role === 'org_admin' ? 'selected' : ''}>ادمین سازمان (Org Admin)</option>
          <option value="super_admin" ${u.role === 'super_admin' ? 'selected' : ''}>سوپر ادمین (Super Admin)</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">وضعیت فعال بودن</label>
        <select id="eu-active" class="form-control">
          <option value="true" ${u.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!u.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">تأیید شده (Verified)</label>
        <select id="eu-verified" class="form-control">
          <option value="true" ${u.is_verified ? 'selected' : ''}>بله</option>
          <option value="false" ${!u.is_verified ? 'selected' : ''}>خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditUser('${u.id}')">بروزرسانی</button>
  `);
}

async function submitEditUser(id) {
  const body = {
    first_name: document.getElementById('eu-fn').value.trim(),
    last_name: document.getElementById('eu-ln').value.trim(),
    phone_number: document.getElementById('eu-phone').value.trim(),
    role: document.getElementById('eu-role').value,
    is_active: document.getElementById('eu-active').value === 'true',
    is_verified: document.getElementById('eu-verified').value === 'true',
  };
  try {
    await apiPatch(`/admin/users/${id}/`, body);
    closeModal();
    toast('اطلاعات کاربر بروزرسانی شد');
    await renderUsers();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   3. ORGANIZATIONS
═══════════════════════════════════════════════════════ */
let orgsData = [];
let orgsPage = 1;
let orgsSearch = '';

async function renderOrganizations() {
  const el = document.getElementById('page');
  try {
    const [activeRes, myRes] = await Promise.all([
      isSuperAdmin() ? apiGet(withPageSize('/organizations/?include_inactive=true')) : Promise.resolve({ results: [] }),
      apiGet(withPageSize('/organizations/my/')),
    ]);
    const list1 = activeRes.results || activeRes || [];
    const list2 = myRes.results || myRes || [];
    const map = new Map();
    [...list1, ...list2].forEach(o => map.set(o.id, o));
    orgsData = Array.from(map.values());
    cachedOrgs = orgsData;
    renderOrgsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setOrgsPage(p) {
  orgsPage = p;
  renderOrgsTable();
}

function renderOrgsTable() {
  const el = document.getElementById('page');
  const filtered = orgsData.filter(o => {
    if (!orgsSearch) return true;
    const q = orgsSearch.toLowerCase();
    return (
      (o.name || '').toLowerCase().includes(q) ||
      (o.slug || '').toLowerCase().includes(q) ||
      (o.phone_number || '').includes(q) ||
      (o.email || '').toLowerCase().includes(q)
    );
  });
  const pg = paginateLocal(filtered, orgsPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>🏢 سازمان‌ها (کلینیک‌ها)</h1><div class="page-header-sub">${filtered.length} سازمان</div></div>
      ${isSuperAdmin() ? `<button class="btn btn-primary" onclick="openCreateOrgModal()">➕ سازمان جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو در نام، اسلاگ، تلفن…" value="${escapeHTML(orgsSearch)}" oninput="orgsSearch=this.value;orgsPage=1;renderOrgsTable()" />
        </div>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام سازمان</th><th>مالک</th><th>Slug</th><th>تلفن / ایمیل</th><th>شعب فعال</th><th>وضعیت</th><th>تاریخ ایجاد</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="8"><div class="empty"><div class="empty-icon">🏢</div><div>سازمانی یافت نشد</div></div></td></tr>`
              : pg.items.map(o => `<tr>
                  <td><strong>${escapeHTML(o.name)}</strong><br><span class="td-muted">${escapeHTML((o.description || '').substring(0, 45))}</span></td>
                  <td>${escapeHTML(o.owner?.full_name || o.owner?.email || '—')}</td>
                  <td class="td-muted dir-ltr">${escapeHTML(o.slug || '')}</td>
                  <td>${escapeHTML(o.phone_number || '—')}<br><span class="td-muted dir-ltr">${escapeHTML(o.email || '')}</span></td>
                  <td><span class="badge badge-blue">${o.active_branches_count ?? 0} شعبه</span></td>
                  <td>${o.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td class="td-muted">${fmtDate(o.created_at)}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openEditOrgModal('${o.id}')">✏️ ویرایش</button>
                      <button class="btn btn-ghost btn-sm" onclick="navigate('branches', { orgId: '${o.id}' })">📍 شعب</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setOrgsPage')}
    </div>
  `;
}

function openCreateOrgModal() {
  openModal('ایجاد سازمان جدید', `
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام سازمان *</label><input id="fo-name" class="form-control" placeholder="مثلاً: کلینیک تخصصی سلامت"></div>
      <div class="form-group"><label class="form-label">Slug (اختیاری)</label><input id="fo-slug" class="form-control dir-ltr" placeholder="tehran-health-clinic"></div>
    </div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="fo-desc" class="form-control" rows="2"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="fo-phone" class="form-control dir-ltr" placeholder="021..."></div>
      <div class="form-group"><label class="form-label">ایمیل</label><input id="fo-email" type="email" class="form-control dir-ltr" placeholder="info@clinic.com"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">وبسایت</label><input id="fo-website" class="form-control dir-ltr" placeholder="https://..."></div>
      <div class="form-group"><label class="form-label">منطقه زمانی (Timezone)</label><input id="fo-tz" class="form-control dir-ltr" value="Asia/Tehran"></div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateOrg()">ذخیره</button>
  `);
}

async function submitCreateOrg() {
  const name = document.getElementById('fo-name').value.trim();
  if (!name) { toast('نام سازمان الزامی است', 'error'); return; }
  const body = {
    name,
    slug: document.getElementById('fo-slug').value.trim(),
    description: document.getElementById('fo-desc').value.trim(),
    phone_number: document.getElementById('fo-phone').value.trim(),
    email: document.getElementById('fo-email').value.trim(),
    website: document.getElementById('fo-website').value.trim(),
    timezone: document.getElementById('fo-tz').value.trim() || 'Asia/Tehran',
    is_active: true,
  };
  try {
    await apiPost('/organizations/', body);
    closeModal();
    toast('سازمان با موفقیت ایجاد شد');
    await renderOrganizations();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditOrgModal(orgId) {
  const o = orgsData.find(x => x.id === orgId);
  if (!o) return;
  openModal(`ویرایش سازمان: ${o.name}`, `
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام سازمان *</label><input id="eo-name" class="form-control" value="${escapeHTML(o.name || '')}"></div>
      <div class="form-group"><label class="form-label">Slug</label><input id="eo-slug" class="form-control dir-ltr" value="${escapeHTML(o.slug || '')}"></div>
    </div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="eo-desc" class="form-control" rows="2">${escapeHTML(o.description || '')}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eo-phone" class="form-control dir-ltr" value="${escapeHTML(o.phone_number || '')}"></div>
      <div class="form-group"><label class="form-label">ایمیل</label><input id="eo-email" class="form-control dir-ltr" value="${escapeHTML(o.email || '')}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">وبسایت</label><input id="eo-website" class="form-control dir-ltr" value="${escapeHTML(o.website || '')}"></div>
      <div class="form-group"><label class="form-label">وضعیت</label>
        <select id="eo-active" class="form-control">
          <option value="true" ${o.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!o.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditOrg('${o.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditOrg(id) {
  const body = {
    name: document.getElementById('eo-name').value.trim(),
    slug: document.getElementById('eo-slug').value.trim(),
    description: document.getElementById('eo-desc').value.trim(),
    phone_number: document.getElementById('eo-phone').value.trim(),
    email: document.getElementById('eo-email').value.trim(),
    website: document.getElementById('eo-website').value.trim(),
    is_active: document.getElementById('eo-active').value === 'true',
  };
  try {
    await apiPatch(`/organizations/${id}/`, body);
    closeModal();
    toast('سازمان بروزرسانی شد');
    await renderOrganizations();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   4. BRANCHES
═══════════════════════════════════════════════════════ */
let branchesData = [];
let branchesPage = 1;
let selectedBranchOrgId = '';

async function renderBranches(params = {}) {
  const el = document.getElementById('page');
  try {
    if (!cachedOrgs.length) await loadCommonLists();
    if (!cachedOrgs.length) {
      el.innerHTML = `<div class="empty"><div class="empty-icon">🏢</div><div class="empty-title">ابتدا یک سازمان ایجاد کنید</div></div>`;
      return;
    }
    if (params.orgId) selectedBranchOrgId = params.orgId;
    if (!selectedBranchOrgId || !cachedOrgs.some(o => o.id === selectedBranchOrgId)) {
      selectedBranchOrgId = cachedOrgs[0].id;
    }
    const data = await apiGet(withPageSize(`/organizations/${selectedBranchOrgId}/branches/`));
    branchesData = data.results || data || [];
    renderBranchesTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setBranchesPage(p) {
  branchesPage = p;
  renderBranchesTable();
}

function renderBranchesTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(branchesData, branchesPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>📍 مدیریت شعب</h1><div class="page-header-sub">${branchesData.length} شعبه در سازمان انتخاب‌شده</div></div>
      <button class="btn btn-primary" onclick="openCreateBranchModal()">➕ شعبه جدید</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <label style="font-size:0.82rem;color:var(--textSub)">انتخاب سازمان:</label>
        <select onchange="selectedBranchOrgId=this.value;branchesPage=1;renderBranches()">
          ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === selectedBranchOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام شعبه</th><th>آدرس</th><th>شماره تماس</th><th>مختصات (Lat, Lng)</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="6"><div class="empty"><div class="empty-icon">📍</div><div>شعبه‌ای برای این سازمان ثبت نشده است</div></div></td></tr>`
              : pg.items.map(b => `<tr>
                  <td><strong>${escapeHTML(b.name)}</strong></td>
                  <td>${escapeHTML(b.address || '—')}</td>
                  <td class="dir-ltr">${escapeHTML(b.phone_number || '—')}</td>
                  <td class="td-muted dir-ltr">${b.latitude && b.longitude ? `${b.latitude}, ${b.longitude}` : '—'}</td>
                  <td>${b.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td><button class="btn btn-ghost btn-sm" onclick="openEditBranchModal('${b.id}')">✏️ ویرایش</button></td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setBranchesPage')}
    </div>
  `;
}

function openCreateBranchModal() {
  openModal('ایجاد شعبه جدید', `
    <div class="form-group"><label class="form-label">نام شعبه *</label><input id="fb-name" class="form-control" placeholder="مثلاً: شعبه مرکزی (ونک)"></div>
    <div class="form-group"><label class="form-label">آدرس</label><textarea id="fb-addr" class="form-control" rows="2"></textarea></div>
    <div class="form-group"><label class="form-label">شماره تماس</label><input id="fb-phone" class="form-control dir-ltr" placeholder="021..."></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">عرض جغرافیایی (Latitude)</label><input id="fb-lat" type="number" step="0.000001" class="form-control dir-ltr" placeholder="35.757500"></div>
      <div class="form-group"><label class="form-label">طول جغرافیایی (Longitude)</label><input id="fb-lng" type="number" step="0.000001" class="form-control dir-ltr" placeholder="51.410000"></div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateBranch()">ذخیره شعبه</button>
  `);
}

async function submitCreateBranch() {
  const name = document.getElementById('fb-name').value.trim();
  if (!name) { toast('نام شعبه الزامی است', 'error'); return; }
  const lat = document.getElementById('fb-lat').value;
  const lng = document.getElementById('fb-lng').value;
  const body = {
    name,
    address: document.getElementById('fb-addr').value.trim(),
    phone_number: document.getElementById('fb-phone').value.trim(),
    latitude: lat ? parseFloat(lat) : null,
    longitude: lng ? parseFloat(lng) : null,
    is_active: true,
  };
  try {
    await apiPost(`/organizations/${selectedBranchOrgId}/branches/`, body);
    closeModal();
    toast('شعبه با موفقیت ایجاد شد');
    await renderBranches();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditBranchModal(branchId) {
  const b = branchesData.find(x => x.id === branchId);
  if (!b) return;
  openModal(`ویرایش شعبه: ${b.name}`, `
    <div class="form-group"><label class="form-label">نام شعبه *</label><input id="eb-name" class="form-control" value="${escapeHTML(b.name || '')}"></div>
    <div class="form-group"><label class="form-label">آدرس</label><textarea id="eb-addr" class="form-control" rows="2">${escapeHTML(b.address || '')}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eb-phone" class="form-control dir-ltr" value="${escapeHTML(b.phone_number || '')}"></div>
      <div class="form-group"><label class="form-label">وضعیت</label>
        <select id="eb-active" class="form-control">
          <option value="true" ${b.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!b.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">عرض جغرافیایی (Latitude)</label><input id="eb-lat" type="number" step="0.000001" class="form-control dir-ltr" value="${b.latitude ?? ''}"></div>
      <div class="form-group"><label class="form-label">طول جغرافیایی (Longitude)</label><input id="eb-lng" type="number" step="0.000001" class="form-control dir-ltr" value="${b.longitude ?? ''}"></div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditBranch('${b.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditBranch(id) {
  const lat = document.getElementById('eb-lat').value;
  const lng = document.getElementById('eb-lng').value;
  const body = {
    name: document.getElementById('eb-name').value.trim(),
    address: document.getElementById('eb-addr').value.trim(),
    phone_number: document.getElementById('eb-phone').value.trim(),
    latitude: lat !== '' ? parseFloat(lat) : null,
    longitude: lng !== '' ? parseFloat(lng) : null,
    is_active: document.getElementById('eb-active').value === 'true',
  };
  try {
    await apiPatch(`/organizations/branches/${id}/`, body);
    closeModal();
    toast('شعبه بروزرسانی شد');
    await renderBranches();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   5. PROVIDERS (پزشکان)
═══════════════════════════════════════════════════════ */
let providersData = [];
let providersPage = 1;
let selectedProviderOrgId = '';
let providersSearch = '';

async function renderProviders() {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    // Fetching per organization via /providers/organizations/{org_id}/ returns both active & inactive providers for admins!
    if (selectedProviderOrgId) {
      const data = await apiGet(withPageSize(`/providers/organizations/${selectedProviderOrgId}/`));
      providersData = data.results || data || [];
    } else if (cachedOrgs.length > 0) {
      const results = await Promise.all(
        cachedOrgs.map(o => apiGet(withPageSize(`/providers/organizations/${o.id}/`)).catch(() => ({ results: [] })))
      );
      const map = new Map();
      results.forEach(r => (r.results || r || []).forEach(p => map.set(p.id, p)));
      providersData = Array.from(map.values());
    } else {
      const data = await apiGet(withPageSize('/providers/'));
      providersData = data.results || data || [];
    }
    renderProvidersTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setProvidersPage(p) {
  providersPage = p;
  renderProvidersTable();
}

function renderProvidersTable() {
  const el = document.getElementById('page');
  const filtered = providersData.filter(p => {
    if (!providersSearch) return true;
    const q = providersSearch.toLowerCase();
    const fullName = `${p.user?.first_name || ''} ${p.user?.last_name || ''}`.toLowerCase();
    return (
      fullName.includes(q) ||
      (p.user?.email || '').toLowerCase().includes(q) ||
      (p.title || '').toLowerCase().includes(q) ||
      (p.organization?.name || '').toLowerCase().includes(q)
    );
  });

  const pg = paginateLocal(filtered, providersPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>👨‍⚕️ پزشکان (Providers)</h1><div class="page-header-sub">${filtered.length} پروفایل پزشک</div></div>
      <button class="btn btn-primary" onclick="openCreateProviderModal()">➕ افزودن پزشک به سازمان</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو در نام پزشک، ایمیل، عنوان…" value="${escapeHTML(providersSearch)}" oninput="providersSearch=this.value;providersPage=1;renderProvidersTable()" />
        </div>
        <select onchange="selectedProviderOrgId=this.value;providersPage=1;renderProviders()">
          <option value="">همه سازمان‌ها</option>
          ${cachedOrgs.map(o => `<option value="${o.id}" ${selectedProviderOrgId === o.id ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>پزشک</th><th>عنوان</th><th>سازمان / شعبه</th><th>تخصص‌ها</th><th>مدت پیش‌فرض اسلات</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="7"><div class="empty"><div class="empty-icon">👨‍⚕️</div><div>پزشکی یافت نشد</div></div></td></tr>`
              : pg.items.map(p => `<tr>
                  <td><strong>${escapeHTML((p.user?.first_name || '') + ' ' + (p.user?.last_name || '')) || '—'}</strong><br><span class="td-muted dir-ltr">${escapeHTML(p.user?.email || '')}</span></td>
                  <td>${escapeHTML(p.title || '—')}</td>
                  <td>${escapeHTML(p.organization?.name || '—')}<br><span class="td-muted">📍 ${escapeHTML(p.branch?.name || 'بدون شعبه')}</span></td>
                  <td>${(p.specialties || []).map(s => `<span class="badge badge-purple" style="margin:2px">${escapeHTML(s.name)}</span>`).join('') || '—'}</td>
                  <td>${p.default_slot_duration_minutes} دقیقه</td>
                  <td>${p.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openEditProviderModal('${p.id}')">✏️ ویرایش</button>
                      <button class="btn btn-ghost btn-sm" onclick="navigate('availability', { providerId: '${p.id}' })">⏰ ساعات کاری</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setProvidersPage')}
    </div>
  `;
}

async function openCreateProviderModal() {
let providerUsers = [];
  try {
    const res = await apiGet(withPageSize('/admin/users/?role=provider&is_active=true'));
    providerUsers = res.results || res || [];
  } catch {}

  const activeCategories = cachedCategories.filter(c => c.is_active);
  const firstOrgId = selectedProviderOrgId || cachedOrgs[0]?.id || '';
  let orgBranches = [];
  if (firstOrgId) {
    try {
      const bRes = await apiGet(withPageSize(`/organizations/${firstOrgId}/branches/`));
      orgBranches = (bRes.results || bRes || []).filter(b => b.is_active);
    } catch {}
  }

  openModal('ایجاد پروفایل پزشک جدید', `
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">کاربر پزشک (دارای نقش provider) *</label>
        ${providerUsers.length > 0
          ? `<select id="fp-user" class="form-control">
              ${providerUsers.map(u => `<option value="${u.id}">${escapeHTML(u.full_name || u.email)} (${escapeHTML(u.email)})</option>`).join('')}
             </select>`
          : `<input id="fp-user" class="form-control dir-ltr" placeholder="UUID کاربر با نقش provider">
             <div class="form-hint">شناسه UUID کاربر دارای نقش پزشک را وارد کنید.</div>`
        }
      </div>
      <div class="form-group">
        <label class="form-label">سازمان (کلینیک) *</label>
        <select id="fp-org" class="form-control" onchange="onProviderModalOrgChange(this.value, 'fp-branch')">
          ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === firstOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">شعبه (اختیاری)</label>
        <select id="fp-branch" class="form-control">
          <option value="">— بدون شعبه —</option>
          ${orgBranches.map(b => `<option value="${b.id}">${escapeHTML(b.name)}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">عنوان پزشکی (Title)</label>
        <input id="fp-title" class="form-control" placeholder="مثلاً: دکتر / متخصص قلب و عروق">
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">تخصص‌ها (Specialties)</label>
      <div class="checkbox-grid" id="fp-specialties">
        ${activeCategories.length === 0
          ? '<span class="td-muted">تخصصی ثبت نشده است</span>'
          : activeCategories.map(c => `
              <label class="checkbox-chip">
                <input type="checkbox" value="${c.id}">
                <span>${escapeHTML(c.name)}</span>
              </label>
            `).join('')}
      </div>
    </div>
    <div class="form-group"><label class="form-label">بیوگرافی و سوابق</label><textarea id="fp-bio" class="form-control" rows="2"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">مدت پیش‌فرض هر نوبت (دقیقه)</label><input id="fp-dur" class="form-control" type="number" min="1" max="480" value="30"></div>
      <div class="form-group"><label class="form-label">وضعیت اولیه</label>
        <select id="fp-active" class="form-control">
          <option value="true" selected>فعال</option>
          <option value="false">غیرفعال</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateProvider()">ذخیره پروفایل پزشک</button>
  `);
}

async function onProviderModalOrgChange(orgId, branchSelectId) {
  const sel = document.getElementById(branchSelectId);
  if (!sel) return;
  sel.innerHTML = '<option value="">در حال بارگذاری…</option>';
  try {
    const res = await apiGet(withPageSize(`/organizations/${orgId}/branches/`));
    const branches = (res.results || res || []).filter(b => b.is_active);
    sel.innerHTML = `<option value="">— بدون شعبه —</option>` +
      branches.map(b => `<option value="${b.id}">${escapeHTML(b.name)}</option>`).join('');
  } catch {
    sel.innerHTML = '<option value="">— بدون شعبه —</option>';
  }
}

async function submitCreateProvider() {
  const user_id = document.getElementById('fp-user').value.trim();
  const organization_id = document.getElementById('fp-org').value;
  const branchVal = document.getElementById('fp-branch').value;
  if (!user_id || !organization_id) {
    toast('انتخاب کاربر پزشک و سازمان الزامی است', 'error');
    return;
  }
  const specialty_ids = Array.from(document.querySelectorAll('#fp-specialties input:checked')).map(el => el.value);

  const body = {
    user_id,
    organization_id,
    branch_id: branchVal || null,
    title: document.getElementById('fp-title').value.trim(),
    specialty_ids,
    bio: document.getElementById('fp-bio').value.trim(),
    default_slot_duration_minutes: parseInt(document.getElementById('fp-dur').value) || 30,
    is_active: document.getElementById('fp-active').value === 'true',
  };
  try {
    await apiPost('/providers/', body);
    closeModal();
    toast('پروفایل پزشک با موفقیت ایجاد شد');
    await renderProviders();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function openEditProviderModal(providerId) {
  const p = providersData.find(x => x.id === providerId);
  if (!p) return;

  let orgBranches = [];
  if (p.organization?.id) {
    try {
      const bRes = await apiGet(withPageSize(`/organizations/${p.organization.id}/branches/`));
      orgBranches = (bRes.results || bRes || []).filter(b => b.is_active);
    } catch {}
  }

  const currentSpecIds = new Set((p.specialties || []).map(s => s.id));
  const activeCategories = cachedCategories.filter(c => c.is_active || currentSpecIds.has(c.id));

  openModal(`ویرایش پزشک: ${p.user?.full_name || p.user?.email || ''}`, `
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">عنوان پزشکی (Title)</label>
        <input id="ep-title" class="form-control" value="${escapeHTML(p.title || '')}">
      </div>
      <div class="form-group">
        <label class="form-label">شعبه در سازمان «${escapeHTML(p.organization?.name || '')}»</label>
        <select id="ep-branch" class="form-control">
          <option value="">— بدون شعبه —</option>
          ${orgBranches.map(b => `<option value="${b.id}" ${p.branch?.id === b.id ? 'selected' : ''}>${escapeHTML(b.name)}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">تخصص‌ها (Specialties)</label>
      <div class="checkbox-grid" id="ep-specialties">
        ${activeCategories.map(c => `
          <label class="checkbox-chip">
            <input type="checkbox" value="${c.id}" ${currentSpecIds.has(c.id) ? 'checked' : ''}>
            <span>${escapeHTML(c.name)}</span>
          </label>
        `).join('')}
      </div>
    </div>
    <div class="form-group"><label class="form-label">بیوگرافی</label><textarea id="ep-bio" class="form-control" rows="2">${escapeHTML(p.bio || '')}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">مدت پیش‌فرض ویزیت (دقیقه)</label><input id="ep-dur" class="form-control" type="number" min="1" max="480" value="${p.default_slot_duration_minutes || 30}"></div>
      <div class="form-group"><label class="form-label">وضعیت فعالیت</label>
        <select id="ep-active" class="form-control">
          <option value="true" ${p.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!p.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditProvider('${p.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditProvider(id) {
  const branchVal = document.getElementById('ep-branch').value;
  const specialty_ids = Array.from(document.querySelectorAll('#ep-specialties input:checked')).map(el => el.value);
  const body = {
    branch_id: branchVal || null,
    title: document.getElementById('ep-title').value.trim(),
    specialty_ids,
    bio: document.getElementById('ep-bio').value.trim(),
    default_slot_duration_minutes: parseInt(document.getElementById('ep-dur').value) || 30,
    is_active: document.getElementById('ep-active').value === 'true',
  };
  try {
    await apiPatch(`/providers/${id}/`, body);
    closeModal();
    toast('پروفایل پزشک بروزرسانی شد');
    await renderProviders();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   6. OFFERINGS (خدمات)
═══════════════════════════════════════════════════════ */
let offeringsData = [];
let offeringsPage = 1;
let selectedOfferingOrgId = '';
let selectedOfferingMode = '';

async function renderOfferings() {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    // Fetching via /offerings/organizations/{org_id}/ includes inactive offerings for org_admin & super_admin!
    if (selectedOfferingOrgId) {
      const data = await apiGet(withPageSize(`/offerings/organizations/${selectedOfferingOrgId}/`));
      offeringsData = data.results || data || [];
    } else if (cachedOrgs.length > 0) {
      const results = await Promise.all(
        cachedOrgs.map(o => apiGet(withPageSize(`/offerings/organizations/${o.id}/`)).catch(() => ({ results: [] })))
      );
      const map = new Map();
      results.forEach(r => (r.results || r || []).forEach(of => map.set(of.id, of)));
      offeringsData = Array.from(map.values());
    } else {
      const data = await apiGet(withPageSize('/offerings/'));
      offeringsData = data.results || data || [];
    }
    renderOfferingsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setOfferingsPage(p) {
  offeringsPage = p;
  renderOfferingsTable();
}

function renderOfferingsTable() {
  const el = document.getElementById('page');
  const filtered = offeringsData.filter(o => !selectedOfferingMode || o.visit_mode === selectedOfferingMode);
  const pg = paginateLocal(filtered, offeringsPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>📋 خدمات (Offerings)</h1><div class="page-header-sub">${filtered.length} خدمت تعریف‌شده</div></div>
      <button class="btn btn-primary" onclick="openCreateOfferingModal()">➕ خدمت جدید</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <select onchange="selectedOfferingOrgId=this.value;offeringsPage=1;renderOfferings()">
          <option value="">همه سازمان‌ها</option>
          ${cachedOrgs.map(o => `<option value="${o.id}" ${selectedOfferingOrgId === o.id ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
        <select onchange="selectedOfferingMode=this.value;offeringsPage=1;renderOfferingsTable()">
          <option value="">همه انواع ویزیت</option>
          <option value="in_person" ${selectedOfferingMode === 'in_person' ? 'selected' : ''}>حضوری (in_person)</option>
          <option value="online_chat" ${selectedOfferingMode === 'online_chat' ? 'selected' : ''}>چت آنلاین (online_chat)</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>عنوان خدمت</th><th>پزشک / سازمان</th><th>تخصص مرتبط</th><th>نوع ویزیت</th><th>مدت / تنفس</th><th>قیمت</th><th>نیاز به تأیید</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="9"><div class="empty"><div class="empty-icon">📋</div><div>خدمتی یافت نشد</div></div></td></tr>`
              : pg.items.map(o => `<tr>
                  <td><strong>${escapeHTML(o.title)}</strong><br><span class="td-muted">${escapeHTML((o.description || '').substring(0, 45))}</span></td>
                  <td>${escapeHTML((o.provider?.user?.first_name || '') + ' ' + (o.provider?.user?.last_name || ''))}<br><span class="td-muted">${escapeHTML(o.organization?.name || '')}</span></td>
                  <td>${o.specialty ? `<span class="badge badge-gray">${escapeHTML(o.specialty.name)}</span>` : '—'}</td>
                  <td>${o.visit_mode === 'in_person' ? '<span class="badge badge-blue">🏥 حضوری</span>' : '<span class="badge badge-purple">💬 چت آنلاین</span>'}</td>
                  <td>${o.duration_minutes} دقیقه<br><span class="td-muted">قبل: ${o.buffer_before_minutes || 0} | بعد: ${o.buffer_after_minutes || 0}</span></td>
                  <td><strong>${fmtMoney(o.price)}</strong></td>
                  <td>${o.requires_approval ? '<span class="badge badge-amber">بله</span>' : '<span class="badge badge-gray">خیر</span>'}</td>
                  <td>${o.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td><button class="btn btn-ghost btn-sm" onclick="openEditOfferingModal('${o.id}')">✏️ ویرایش</button></td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setOfferingsPage')}
    </div>
  `;
}

async function openCreateOfferingModal() {
  const firstOrgId = selectedOfferingOrgId || cachedOrgs[0]?.id || '';
  let orgProviders = [];
  if (firstOrgId) {
    try {
      const pRes = await apiGet(withPageSize(`/providers/organizations/${firstOrgId}/`));
      orgProviders = (pRes.results || pRes || []).filter(p => p.is_active);
    } catch {}
  }
  const activeCategories = cachedCategories.filter(c => c.is_active);

  openModal('تعریف خدمت جدید (Offering)', `
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">سازمان *</label>
        <select id="fof-org" class="form-control" onchange="onOfferingModalOrgChange(this.value)">
          ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === firstOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">پزشک ارائه‌دهنده *</label>
        <select id="fof-prov" class="form-control">
          ${orgProviders.length === 0
            ? '<option value="">— پزشکی در این سازمان یافت نشد —</option>'
            : orgProviders.map(p => `<option value="${p.id}">${escapeHTML((p.user?.first_name || '') + ' ' + (p.user?.last_name || '') || p.user?.email)}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">عنوان خدمت *</label><input id="fof-title" class="form-control" placeholder="مثلاً: ویزیت حضوری و چکاپ"></div>
      <div class="form-group"><label class="form-label">تخصص مرتبط (اختیاری)</label>
        <select id="fof-spec" class="form-control">
          <option value="">— انتخاب تخصص —</option>
          ${activeCategories.map(c => `<option value="${c.id}">${escapeHTML(c.name)}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="fof-desc" class="form-control" rows="2"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نوع ویزیت *</label>
        <select id="fof-mode" class="form-control">
          <option value="in_person">حضوری در کلینیک (in_person)</option>
          <option value="online_chat">مشاوره و چت آنلاین (online_chat)</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">قیمت (تومان) *</label><input id="fof-price" class="form-control" type="number" min="0" step="1000" value="250000"></div>
    </div>
    <div class="form-row-3">
      <div class="form-group"><label class="form-label">مدت ویزیت (دقیقه)</label><input id="fof-dur" class="form-control" type="number" min="1" max="480" value="30"></div>
      <div class="form-group"><label class="form-label">تنفس قبل (Buffer Before)</label><input id="fof-buf-before" class="form-control" type="number" min="0" max="240" value="0"></div>
      <div class="form-group"><label class="form-label">تنفس بعد (Buffer After)</label><input id="fof-buf-after" class="form-control" type="number" min="0" max="240" value="0"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نیاز به تأیید دستی پزشک/ادمین؟</label>
        <select id="fof-appr" class="form-control"><option value="false">خیر (تأیید خودکار)</option><option value="true">بله (PENDING تا زمان تأیید)</option></select>
      </div>
      <div class="form-group"><label class="form-label">وضعیت</label>
        <select id="fof-active" class="form-control"><option value="true" selected>فعال</option><option value="false">غیرفعال</option></select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateOffering()">ذخیره خدمت</button>
  `);
}

async function onOfferingModalOrgChange(orgId) {
  const sel = document.getElementById('fof-prov');
  if (!sel) return;
  sel.innerHTML = '<option value="">در حال بارگذاری…</option>';
  try {
    const res = await apiGet(withPageSize(`/providers/organizations/${orgId}/`));
    const provs = (res.results || res || []).filter(p => p.is_active);
    sel.innerHTML = provs.length === 0
      ? '<option value="">— پزشکی در این سازمان یافت نشد —</option>'
      : provs.map(p => `<option value="${p.id}">${escapeHTML((p.user?.first_name || '') + ' ' + (p.user?.last_name || '') || p.user?.email)}</option>`).join('');
  } catch {
    sel.innerHTML = '<option value="">خطا در بارگذاری پزشکان</option>';
  }
}

async function submitCreateOffering() {
  const organization_id = document.getElementById('fof-org').value;
  const provider_id = document.getElementById('fof-prov').value;
  const title = document.getElementById('fof-title').value.trim();
  const specVal = document.getElementById('fof-spec').value;

  if (!organization_id || !provider_id || !title) {
    toast('سازمان، پزشک و عنوان خدمت الزامی هستند', 'error');
    return;
  }

  const body = {
    organization_id,
    provider_id,
    specialty_id: specVal || null,
    title,
    description: document.getElementById('fof-desc').value.trim(),
    visit_mode: document.getElementById('fof-mode').value,
    duration_minutes: parseInt(document.getElementById('fof-dur').value) || 30,
    buffer_before_minutes: parseInt(document.getElementById('fof-buf-before').value) || 0,
    buffer_after_minutes: parseInt(document.getElementById('fof-buf-after').value) || 0,
    price: document.getElementById('fof-price').value || '0',
    requires_approval: document.getElementById('fof-appr').value === 'true',
    is_active: document.getElementById('fof-active').value === 'true',
  };

  try {
    await apiPost('/offerings/', body);
    closeModal();
    toast('خدمت جدید با موفقیت ایجاد شد');
    await renderOfferings();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditOfferingModal(offeringId) {
  const o = offeringsData.find(x => x.id === offeringId);
  if (!o) return;
  const activeCategories = cachedCategories.filter(c => c.is_active || c.id === o.specialty?.id);

  openModal(`ویرایش خدمت: ${o.title}`, `
    <div class="form-row">
      <div class="form-group"><label class="form-label">عنوان خدمت *</label><input id="eof-title" class="form-control" value="${escapeHTML(o.title || '')}"></div>
      <div class="form-group"><label class="form-label">تخصص مرتبط</label>
        <select id="eof-spec" class="form-control">
          <option value="">— بدون تخصص —</option>
          ${activeCategories.map(c => `<option value="${c.id}" ${o.specialty?.id === c.id ? 'selected' : ''}>${escapeHTML(c.name)}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="eof-desc" class="form-control" rows="2">${escapeHTML(o.description || '')}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نوع ویزیت</label>
        <select id="eof-mode" class="form-control">
          <option value="in_person" ${o.visit_mode === 'in_person' ? 'selected' : ''}>حضوری در کلینیک (in_person)</option>
          <option value="online_chat" ${o.visit_mode === 'online_chat' ? 'selected' : ''}>مشاوره و چت آنلاین (online_chat)</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">قیمت (تومان)</label><input id="eof-price" class="form-control" type="number" min="0" value="${o.price || 0}"></div>
    </div>
    <div class="form-row-3">
      <div class="form-group"><label class="form-label">مدت (دقیقه)</label><input id="eof-dur" class="form-control" type="number" min="1" max="480" value="${o.duration_minutes || 30}"></div>
      <div class="form-group"><label class="form-label">تنفس قبل (دقیقه)</label><input id="eof-buf-before" class="form-control" type="number" min="0" max="240" value="${o.buffer_before_minutes || 0}"></div>
      <div class="form-group"><label class="form-label">تنفس بعد (دقیقه)</label><input id="eof-buf-after" class="form-control" type="number" min="0" max="240" value="${o.buffer_after_minutes || 0}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نیاز به تأیید دستی؟</label>
        <select id="eof-appr" class="form-control">
          <option value="false" ${!o.requires_approval ? 'selected' : ''}>خیر</option>
          <option value="true" ${o.requires_approval ? 'selected' : ''}>بله</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">وضعیت</label>
        <select id="eof-active" class="form-control">
          <option value="true" ${o.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!o.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditOffering('${o.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditOffering(id) {
  const specVal = document.getElementById('eof-spec').value;
  const body = {
    title: document.getElementById('eof-title').value.trim(),
    specialty_id: specVal || null,
    description: document.getElementById('eof-desc').value.trim(),
    visit_mode: document.getElementById('eof-mode').value,
    duration_minutes: parseInt(document.getElementById('eof-dur').value) || 30,
    buffer_before_minutes: parseInt(document.getElementById('eof-buf-before').value) || 0,
    buffer_after_minutes: parseInt(document.getElementById('eof-buf-after').value) || 0,
    price: document.getElementById('eof-price').value || '0',
    requires_approval: document.getElementById('eof-appr').value === 'true',
    is_active: document.getElementById('eof-active').value === 'true',
  };
  try {
    await apiPatch(`/offerings/${id}/`, body);
    closeModal();
    toast('خدمت بروزرسانی شد');
    await renderOfferings();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   7. CATEGORIES (تخصص‌ها)
═══════════════════════════════════════════════════════ */
let catsData = [];
let catsPage = 1;

async function renderCategories() {
  const el = document.getElementById('page');
  try {
    const data = await apiGet(withPageSize('/categories/admin/'));
    catsData = data.results || data || [];
    cachedCategories = catsData;
    renderCatsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setCatsPage(p) {
  catsPage = p;
  renderCatsTable();
}

function renderCatsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(catsData, catsPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>🏷️ تخصص‌های پزشکی</h1><div class="page-header-sub">${catsData.length} تخصص</div></div>
      ${isSuperAdmin() ? `<button class="btn btn-primary" onclick="openCreateCatModal()">➕ تخصص جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام تخصص</th><th>Slug</th><th>توضیحات</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">🏷️</div><div>تخصصی ثبت نشده است</div></div></td></tr>`
              : pg.items.map(c => `<tr>
                  <td><strong>${escapeHTML(c.name)}</strong></td>
                  <td class="td-muted dir-ltr">${escapeHTML(c.slug || '')}</td>
                  <td class="td-muted">${escapeHTML(c.description || '—')}</td>
                  <td>${c.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td>
                    <div class="row-actions">
                      ${isSuperAdmin() ? `<button class="btn btn-ghost btn-sm" onclick="openEditCatModal('${c.id}')">✏️ ویرایش</button>` : ''}
                      ${isSuperAdmin() && c.is_active ? `<button class="btn btn-danger btn-sm" onclick="deleteCat('${c.id}')">🚫 غیرفعال‌سازی</button>` : ''}
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setCatsPage')}
    </div>
  `;
}

function openCreateCatModal() {
  openModal('افزودن تخصص جدید', `
    <div class="form-group"><label class="form-label">نام تخصص *</label><input id="fc-name" class="form-control" placeholder="مثلاً: قلب و عروق"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="fc-desc" class="form-control" rows="2"></textarea></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateCat()">ذخیره</button>
  `);
}

async function submitCreateCat() {
  const name = document.getElementById('fc-name').value.trim();
  if (!name) { toast('نام تخصص الزامی است', 'error'); return; }
  const body = { name, description: document.getElementById('fc-desc').value.trim(), is_active: true };
  try {
    await apiPost('/categories/admin/', body);
    closeModal();
    toast('تخصص جدید ایجاد شد');
    await renderCategories();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditCatModal(catId) {
  const c = catsData.find(x => x.id === catId);
  if (!c) return;
  openModal(`ویرایش تخصص: ${c.name}`, `
    <div class="form-group"><label class="form-label">نام تخصص *</label><input id="ec-name" class="form-control" value="${escapeHTML(c.name || '')}"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="ec-desc" class="form-control" rows="2">${escapeHTML(c.description || '')}</textarea></div>
    <div class="form-group"><label class="form-label">وضعیت</label>
      <select id="ec-active" class="form-control">
        <option value="true" ${c.is_active ? 'selected' : ''}>فعال</option>
        <option value="false" ${!c.is_active ? 'selected' : ''}>غیرفعال</option>
      </select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditCat('${c.id}')">ذخیره</button>
  `);
}

async function submitEditCat(id) {
  const body = {
    name: document.getElementById('ec-name').value.trim(),
    description: document.getElementById('ec-desc').value.trim(),
    is_active: document.getElementById('ec-active').value === 'true',
  };
  try {
    await apiPatch(`/categories/admin/${id}/`, body);
    closeModal();
    toast('تخصص بروزرسانی شد');
    await renderCategories();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function deleteCat(id) {
  const c = catsData.find(x => x.id === id);
  if (!confirm(`آیا تخصص "${c?.name || ''}" غیرفعال شود؟`)) return;
  try {
    await apiDelete(`/categories/admin/${id}/`);
    toast('تخصص غیرفعال شد');
    await renderCategories();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   8. AVAILABILITY (ساعات کاری هفتگی، مرخصی پزشکان و تست اسلات)
═══════════════════════════════════════════════════════ */
let availabilityTab = 'working_hours'; // 'working_hours' | 'time_offs' | 'slots_preview'
let availProvidersList = [];
let selectedAvailProviderId = '';
let workingHoursData = [];
let timeOffsData = [];
let availProviderOfferings = [];
let previewSlotsData = null;

async function renderAvailability(params = {}) {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    // Load all providers across accessible organizations
    if (cachedOrgs.length > 0) {
      const results = await Promise.all(
        cachedOrgs.map(o => apiGet(withPageSize(`/providers/organizations/${o.id}/`)).catch(() => ({ results: [] })))
      );
      const map = new Map();
      results.forEach(r => (r.results || r || []).forEach(p => map.set(p.id, p)));
      availProvidersList = Array.from(map.values());
    } else {
      const res = await apiGet(withPageSize('/providers/'));
      availProvidersList = res.results || res || [];
    }

    if (params.providerId) selectedAvailProviderId = params.providerId;
    if (!selectedAvailProviderId && availProvidersList.length > 0) {
      selectedAvailProviderId = availProvidersList[0].id;
    }

    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

async function loadSelectedProviderAvailability() {
  if (!selectedAvailProviderId) {
    workingHoursData = [];
    timeOffsData = [];
    availProviderOfferings = [];
    return;
  }
  const [whRes, toRes, offRes] = await Promise.all([
    apiGet(withPageSize(`/availability/providers/${selectedAvailProviderId}/working-hours/`)).catch(() => ({ results: [] })),
    apiGet(withPageSize(`/availability/providers/${selectedAvailProviderId}/time-offs/`)).catch(() => ({ results: [] })),
    apiGet(withPageSize(`/offerings/providers/${selectedAvailProviderId}/`)).catch(() => ({ results: [] })),
  ]);
  workingHoursData = whRes.results || whRes || [];
  timeOffsData = toRes.results || toRes || [];
  availProviderOfferings = (offRes.results || offRes || []).filter(o => o.is_active);
}

async function onChangeAvailProvider(provId) {
  selectedAvailProviderId = provId;
  previewSlotsData = null;
  await loadSelectedProviderAvailability();
  renderAvailabilityView();
}

function switchAvailTab(tab) {
  availabilityTab = tab;
  renderAvailabilityView();
}

function renderAvailabilityView() {
  const el = document.getElementById('page');
  if (availProvidersList.length === 0) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">👨‍⚕️</div><div class="empty-title">ابتدا یک پروفایل پزشک ایجاد کنید</div></div>`;
    return;
  }

  let tabContentHTML = '';
  if (availabilityTab === 'working_hours') {
    tabContentHTML = `
      <div class="card-title">
        <span>🕒 برنامه ساعات کاری هفتگی</span>
        <button class="btn btn-primary btn-sm" onclick="openCreateWorkingHourModal()">➕ افزودن شیفت کاری</button>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>روز هفته</th><th>ساعت شروع</th><th>ساعت پایان</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${workingHoursData.length === 0
              ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">⏰</div><div>ساعت کاری برای این پزشک ثبت نشده است</div></div></td></tr>`
              : workingHoursData.map(w => `<tr>
                  <td><strong>${escapeHTML(WEEKDAYS_FA[w.weekday] || w.weekday_display || w.weekday)}</strong></td>
                  <td class="dir-ltr">${escapeHTML(w.start_time)}</td>
                  <td class="dir-ltr">${escapeHTML(w.end_time)}</td>
                  <td>${w.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-rose">غیرفعال</span>'}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openEditWorkingHourModal('${w.id}')">✏️ ویرایش</button>
                      <button class="btn btn-ghost btn-sm" onclick="toggleWorkingHourActive('${w.id}')">${w.is_active ? '🚫 غیرفعال' : '✅ فعال'}</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } else if (availabilityTab === 'time_offs') {
    tabContentHTML = `
      <div class="card-title">
        <span>🏖️ مرخصی‌ها و ساعات عدم حضور (Time Offs)</span>
        <button class="btn btn-primary btn-sm" onclick="openCreateTimeOffModal()">➕ ثبت مرخصی جدید</button>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>شروع مرخصی</th><th>پایان مرخصی</th><th>علت / توضیح</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${timeOffsData.length === 0
              ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">🏖️</div><div>مرخصی ثبت‌شده‌ای وجود ندارد</div></div></td></tr>`
              : timeOffsData.map(t => `<tr>
                  <td class="td-muted">${fmtDate(t.start_at)}</td>
                  <td class="td-muted">${fmtDate(t.end_at)}</td>
                  <td>${escapeHTML(t.reason || '—')}</td>
                  <td>${t.is_active ? '<span class="badge badge-amber">فعال (اعمال‌شده)</span>' : '<span class="badge badge-gray">لغوشده / غیرفعال</span>'}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openEditTimeOffModal('${t.id}')">✏️ ویرایش</button>
                      <button class="btn btn-ghost btn-sm" onclick="toggleTimeOffActive('${t.id}')">${t.is_active ? '🚫 لغو مرخصی' : '✅ فعال‌سازی'}</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
    `;
  } else {
    const todayIso = new Date().toISOString().split('T')[0];
    tabContentHTML = `
      <div class="card-title"><span>🔍 پیش‌نمایش و تست اسلات‌های خالی پزشک</span></div>
      <div class="toolbar">
        <select id="slot-preview-offering">
          ${availProviderOfferings.length === 0
            ? '<option value="">— این پزشک خدمت فعالی ندارد —</option>'
            : availProviderOfferings.map(o => `<option value="${o.id}">${escapeHTML(o.title)} (${o.duration_minutes} دقیقه)</option>`).join('')}
        </select>
        <input type="date" id="slot-preview-date" value="${todayIso}" />
        <button class="btn btn-primary" onclick="fetchAvailableSlotsPreview()">جستجوی اسلات‌های آزاد</button>
      </div>
      <div id="slots-preview-container">
        ${previewSlotsData === null
          ? `<div class="empty"><div class="empty-icon">📅</div><div>خدمت و تاریخ مورد نظر را انتخاب و دکمه جستجو را بزنید</div></div>`
          : previewSlotsData.length === 0
            ? `<div class="empty"><div class="empty-icon">🚫</div><div class="empty-title">هیچ اسلات آزادی در این تاریخ یافت نشد</div><div class="empty-sub">احتمالاً برای این روزِ هفته ساعت کاری تعریف نشده، یا روز تعطیل است، یا تمام نوبت‌ها پر/گذشته هستند.</div></div>`
            : `<div class="slots-grid">
                ${previewSlotsData.map(s => {
                  const st = new Date(s.start_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
                  const et = new Date(s.end_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
                  return `<div class="slot-chip">
                    <div class="slot-time">${st} تا ${et}</div>
                    <div class="slot-meta">${s.duration_minutes} دقیقه | ${fmtMoney(s.price)}</div>
                  </div>`;
                }).join('')}
              </div>`
        }
      </div>
    `;
  }

  el.innerHTML = `
    <div class="page-header">
      <div>
        <h1>⏰ ساعات کاری و مرخصی پزشکان</h1>
        <div class="page-header-sub">تنظیم برنامه حضور هفتگی، مرخصی‌ها و بررسی اسلات‌های نوبت‌دهی</div>
      </div>
    </div>
    <div class="card">
      <div class="toolbar">
        <label style="font-size:0.85rem;font-weight:600;color:var(--textSub)">پزشک انتخاب‌شده:</label>
        <select style="min-width:280px" onchange="onChangeAvailProvider(this.value)">
          ${availProvidersList.map(p => `<option value="${p.id}" ${p.id === selectedAvailProviderId ? 'selected' : ''}>${escapeHTML((p.user?.first_name || '') + ' ' + (p.user?.last_name || '') || p.user?.email)} — ${escapeHTML(p.organization?.name || '')}</option>`).join('')}
        </select>
      </div>

      <div class="tabs">
        <div class="tab ${availabilityTab === 'working_hours' ? 'active' : ''}" onclick="switchAvailTab('working_hours')">🕒 ساعات کاری هفتگی (${workingHoursData.length})</div>
        <div class="tab ${availabilityTab === 'time_offs' ? 'active' : ''}" onclick="switchAvailTab('time_offs')">🏖️ مرخصی‌های پزشک (${timeOffsData.length})</div>
        <div class="tab ${availabilityTab === 'slots_preview' ? 'active' : ''}" onclick="switchAvailTab('slots_preview')">🔍 تست اسلات‌های خالی</div>
      </div>

      ${tabContentHTML}
    </div>
  `;
}

async function fetchAvailableSlotsPreview() {
  const offeringId = document.getElementById('slot-preview-offering')?.value;
  const dateVal = document.getElementById('slot-preview-date')?.value;
  if (!selectedAvailProviderId || !offeringId || !dateVal) {
    toast('لطفاً خدمت و تاریخ را انتخاب کنید', 'error');
    return;
  }
  try {
    const res = await apiGet(`/availability/slots/?provider_id=${selectedAvailProviderId}&offering_id=${offeringId}&date=${dateVal}`);
    previewSlotsData = res.results || [];
    renderAvailabilityView();
    // Restore selected offering & date
    const offEl = document.getElementById('slot-preview-offering');
    const dtEl = document.getElementById('slot-preview-date');
    if (offEl) offEl.value = offeringId;
    if (dtEl) dtEl.value = dateVal;
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openCreateWorkingHourModal() {
  openModal('افزودن ساعت کاری هفتگی', `
    <div class="form-group">
      <label class="form-label">روز هفته *</label>
      <select id="fwh-day" class="form-control">
        ${Object.entries(WEEKDAYS_FA).map(([k, v]) => `<option value="${k}">${escapeHTML(v)}</option>`).join('')}
      </select>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">ساعت شروع *</label><input id="fwh-start" type="time" class="form-control dir-ltr" value="09:00"></div>
      <div class="form-group"><label class="form-label">ساعت پایان *</label><input id="fwh-end" type="time" class="form-control dir-ltr" value="17:00"></div>
    </div>
    <div class="form-group">
      <label class="form-label">وضعیت</label>
      <select id="fwh-active" class="form-control"><option value="true" selected>فعال</option><option value="false">غیرفعال</option></select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateWorkingHour()">ذخیره</button>
  `);
}

async function submitCreateWorkingHour() {
  const body = {
    provider_id: selectedAvailProviderId,
    weekday: parseInt(document.getElementById('fwh-day').value),
    start_time: document.getElementById('fwh-start').value,
    end_time: document.getElementById('fwh-end').value,
    is_active: document.getElementById('fwh-active').value === 'true',
  };
  try {
    await apiPost('/availability/working-hours/', body);
    closeModal();
    toast('ساعت کاری ثبت شد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditWorkingHourModal(whId) {
  const w = workingHoursData.find(x => x.id === whId);
  if (!w) return;
  openModal('ویرایش ساعت کاری', `
    <div class="form-group">
      <label class="form-label">روز هفته</label>
      <select id="ewh-day" class="form-control">
        ${Object.entries(WEEKDAYS_FA).map(([k, v]) => `<option value="${k}" ${Number(k) === w.weekday ? 'selected' : ''}>${escapeHTML(v)}</option>`).join('')}
      </select>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">ساعت شروع</label><input id="ewh-start" type="time" class="form-control dir-ltr" value="${escapeHTML((w.start_time || '').substring(0, 5))}"></div>
      <div class="form-group"><label class="form-label">ساعت پایان</label><input id="ewh-end" type="time" class="form-control dir-ltr" value="${escapeHTML((w.end_time || '').substring(0, 5))}"></div>
    </div>
    <div class="form-group">
      <label class="form-label">وضعیت</label>
      <select id="ewh-active" class="form-control">
        <option value="true" ${w.is_active ? 'selected' : ''}>فعال</option>
        <option value="false" ${!w.is_active ? 'selected' : ''}>غیرفعال</option>
      </select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditWorkingHour('${w.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditWorkingHour(id) {
  const body = {
    weekday: parseInt(document.getElementById('ewh-day').value),
    start_time: document.getElementById('ewh-start').value,
    end_time: document.getElementById('ewh-end').value,
    is_active: document.getElementById('ewh-active').value === 'true',
  };
  try {
    await apiPatch(`/availability/working-hours/${id}/`, body);
    closeModal();
    toast('ساعت کاری بروزرسانی شد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function toggleWorkingHourActive(id) {
  const w = workingHoursData.find(x => x.id === id);
  if (!w) return;
  try {
    await apiPatch(`/availability/working-hours/${id}/`, { is_active: !w.is_active });
    toast('وضعیت ساعت کاری تغییر کرد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openCreateTimeOffModal() {
  openModal('ثبت مرخصی جدید برای پزشک', `
    <div class="form-row">
      <div class="form-group"><label class="form-label">شروع مرخصی *</label><input id="fto-start" type="datetime-local" class="form-control dir-ltr"></div>
      <div class="form-group"><label class="form-label">پایان مرخصی *</label><input id="fto-end" type="datetime-local" class="form-control dir-ltr"></div>
    </div>
    <div class="form-group"><label class="form-label">علت مرخصی</label><input id="fto-reason" class="form-control" placeholder="مثلاً: سفر / کنگره پزشکی"></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateTimeOff()">ثبت مرخصی</button>
  `);
}

async function submitCreateTimeOff() {
  const st = document.getElementById('fto-start').value;
  const et = document.getElementById('fto-end').value;
  if (!st || !et) { toast('زمان شروع و پایان الزامی است', 'error'); return; }
  const body = {
    provider_id: selectedAvailProviderId,
    start_at: new Date(st).toISOString(),
    end_at: new Date(et).toISOString(),
    reason: document.getElementById('fto-reason').value.trim(),
    is_active: true,
  };
  try {
    await apiPost('/availability/time-offs/', body);
    closeModal();
    toast('مرخصی ثبت شد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditTimeOffModal(toId) {
  const t = timeOffsData.find(x => x.id === toId);
  if (!t) return;
  openModal('ویرایش مرخصی پزشک', `
    <div class="form-row">
      <div class="form-group"><label class="form-label">شروع مرخصی</label><input id="eto-start" type="datetime-local" class="form-control dir-ltr" value="${toDatetimeLocalValue(t.start_at)}"></div>
      <div class="form-group"><label class="form-label">پایان مرخصی</label><input id="eto-end" type="datetime-local" class="form-control dir-ltr" value="${toDatetimeLocalValue(t.end_at)}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">علت</label><input id="eto-reason" class="form-control" value="${escapeHTML(t.reason || '')}"></div>
      <div class="form-group"><label class="form-label">وضعیت</label>
        <select id="eto-active" class="form-control">
          <option value="true" ${t.is_active ? 'selected' : ''}>فعال</option>
          <option value="false" ${!t.is_active ? 'selected' : ''}>غیرفعال</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditTimeOff('${t.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditTimeOff(id) {
  const st = document.getElementById('eto-start').value;
  const et = document.getElementById('eto-end').value;
  const body = {
    start_at: new Date(st).toISOString(),
    end_at: new Date(et).toISOString(),
    reason: document.getElementById('eto-reason').value.trim(),
    is_active: document.getElementById('eto-active').value === 'true',
  };
  try {
    await apiPatch(`/availability/time-offs/${id}/`, body);
    closeModal();
    toast('مرخصی بروزرسانی شد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function toggleTimeOffActive(id) {
  const t = timeOffsData.find(x => x.id === id);
  if (!t) return;
  try {
    await apiPatch(`/availability/time-offs/${id}/`, { is_active: !t.is_active });
    toast('وضعیت مرخصی تغییر کرد');
    await loadSelectedProviderAvailability();
    renderAvailabilityView();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   9. HOLIDAYS (تعطیلات سازمان)
═══════════════════════════════════════════════════════ */
let holidaysData = [];
let holidaysPage = 1;
let selectedHolidayOrgId = '';

async function renderHolidays() {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    // Fetching via /availability/organizations/{org_id}/holidays/ returns both active and inactive holidays for managers!
    if (selectedHolidayOrgId) {
      const data = await apiGet(withPageSize(`/availability/organizations/${selectedHolidayOrgId}/holidays/`));
      holidaysData = data.results || data || [];
    } else if (cachedOrgs.length > 0) {
      const results = await Promise.all(
        cachedOrgs.map(o => apiGet(withPageSize(`/availability/organizations/${o.id}/holidays/`)).catch(() => ({ results: [] })))
      );
      const map = new Map();
      results.forEach(r => (r.results || r || []).forEach(h => map.set(h.id, h)));
      holidaysData = Array.from(map.values());
    } else {
      const data = await apiGet(withPageSize('/availability/holidays/'));
      holidaysData = data.results || data || [];
    }
    renderHolidaysTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setHolidaysPage(p) {
  holidaysPage = p;
  renderHolidaysTable();
}

function renderHolidaysTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(holidaysData, holidaysPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>📅 تعطیلات رسمی سازمان</h1><div class="page-header-sub">${holidaysData.length} روز تعطیل ثبت‌شده</div></div>
      <button class="btn btn-primary" onclick="openCreateHolidayModal()">➕ ثبت روز تعطیل</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <select onchange="selectedHolidayOrgId=this.value;holidaysPage=1;renderHolidays()">
          <option value="">همه سازمان‌ها</option>
          ${cachedOrgs.map(o => `<option value="${o.id}" ${selectedHolidayOrgId === o.id ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>عنوان تعطیلی</th><th>تاریخ (میلادی / شمسی)</th><th>سازمان</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">📅</div><div>تعطیلی ثبت نشده است</div></div></td></tr>`
              : pg.items.map(h => `<tr>
                  <td><strong>${escapeHTML(h.title || '—')}</strong></td>
                  <td><span class="dir-ltr">${escapeHTML(h.date)}</span> — <span class="td-muted">${fmtDateOnly(h.date)}</span></td>
                  <td>${escapeHTML(h.organization?.name || '—')}</td>
                  <td>${h.is_active ? '<span class="badge badge-green">فعال</span>' : '<span class="badge badge-gray">غیرفعال</span>'}</td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openEditHolidayModal('${h.id}')">✏️ ویرایش</button>
                      <button class="btn btn-ghost btn-sm" onclick="toggleHolidayActive('${h.id}')">${h.is_active ? '🚫 غیرفعال' : '✅ فعال'}</button>
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setHolidaysPage')}
    </div>
  `;
}

function openCreateHolidayModal() {
  const firstOrgId = selectedHolidayOrgId || cachedOrgs[0]?.id || '';
  openModal('ثبت تعطیلی جدید برای سازمان', `
    <div class="form-group">
      <label class="form-label">سازمان *</label>
      <select id="fh-org" class="form-control">
        ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === firstOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
      </select>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">تاریخ تعطیلی *</label><input id="fh-date" class="form-control dir-ltr" type="date"></div>
      <div class="form-group"><label class="form-label">عنوان مناسبت *</label><input id="fh-title" class="form-control" placeholder="مثلاً: تعطیلی رسمی"></div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateHoliday()">ذخیره</button>
  `);
}

async function submitCreateHoliday() {
  const organization_id = document.getElementById('fh-org').value;
  const date = document.getElementById('fh-date').value;
  const title = document.getElementById('fh-title').value.trim();
  if (!organization_id || !date || !title) {
    toast('سازمان، تاریخ و عنوان الزامی هستند', 'error');
    return;
  }
  try {
    await apiPost('/availability/holidays/', { organization_id, date, title, is_active: true });
    closeModal();
    toast('تعطیلی با موفقیت ثبت شد');
    await renderHolidays();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openEditHolidayModal(holidayId) {
  const h = holidaysData.find(x => x.id === holidayId);
  if (!h) return;
  openModal(`ویرایش تعطیلی: ${h.title}`, `
    <div class="form-row">
      <div class="form-group"><label class="form-label">تاریخ</label><input id="eh-date" type="date" class="form-control dir-ltr" value="${escapeHTML(h.date || '')}"></div>
      <div class="form-group"><label class="form-label">عنوان</label><input id="eh-title" class="form-control" value="${escapeHTML(h.title || '')}"></div>
    </div>
    <div class="form-group">
      <label class="form-label">وضعیت</label>
      <select id="eh-active" class="form-control">
        <option value="true" ${h.is_active ? 'selected' : ''}>فعال</option>
        <option value="false" ${!h.is_active ? 'selected' : ''}>غیرفعال</option>
      </select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditHoliday('${h.id}')">ذخیره تغییرات</button>
  `);
}

async function submitEditHoliday(id) {
  const body = {
    date: document.getElementById('eh-date').value,
    title: document.getElementById('eh-title').value.trim(),
    is_active: document.getElementById('eh-active').value === 'true',
  };
  try {
    await apiPatch(`/availability/holidays/${id}/`, body);
    closeModal();
    toast('تعطیلی بروزرسانی شد');
    await renderHolidays();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function toggleHolidayActive(id) {
  const h = holidaysData.find(x => x.id === id);
  if (!h) return;
  try {
    await apiPatch(`/availability/holidays/${id}/`, { is_active: !h.is_active });
    toast('وضعیت تعطیلی تغییر کرد');
    await renderHolidays();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   10. APPOINTMENTS (نوبت‌ها)
═══════════════════════════════════════════════════════ */
let apptsData = [];
let apptsPage = 1;
let selectedApptOrgId = '';
let apptsStatusFilter = '';
let apptsModeFilter = '';
let apptsSearch = '';

async function renderAppointments() {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    if (!selectedApptOrgId && !isSuperAdmin() && cachedOrgs.length > 0) {
      selectedApptOrgId = cachedOrgs[0].id;
    }

    let url = selectedApptOrgId
      ? `/appointments/organizations/${selectedApptOrgId}/`
      : '/appointments/';
    const data = await apiGet(withPageSize(url));
    apptsData = data.results || data || [];
    renderApptsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setApptsPage(p) {
  apptsPage = p;
  renderApptsTable();
}

function renderApptsTable() {
  const el = document.getElementById('page');
  const filtered = apptsData.filter(a => {
    if (apptsStatusFilter && a.status !== apptsStatusFilter) return false;
    if (apptsModeFilter && a.visit_mode !== apptsModeFilter) return false;
    if (apptsSearch) {
      const q = apptsSearch.toLowerCase();
      const cust = `${a.customer?.first_name || ''} ${a.customer?.last_name || ''} ${a.customer?.email || ''}`.toLowerCase();
      const prov = `${a.provider?.user?.first_name || ''} ${a.provider?.user?.last_name || ''} ${a.provider?.user?.email || ''}`.toLowerCase();
      const off  = (a.offering?.title || '').toLowerCase();
      if (!cust.includes(q) && !prov.includes(q) && !off.includes(q)) return false;
    }
    return true;
  });

  const pg = paginateLocal(filtered, apptsPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>🗓️ مدیریت نوبت‌ها</h1><div class="page-header-sub">${filtered.length} نوبت</div></div>
      <button class="btn btn-ghost" onclick="renderAppointments()">🔄 بروزرسانی</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو در نام بیمار، پزشک، خدمت…" value="${escapeHTML(apptsSearch)}" oninput="apptsSearch=this.value;apptsPage=1;renderApptsTable()" />
        </div>
        <select onchange="selectedApptOrgId=this.value;apptsPage=1;renderAppointments()">
          ${isSuperAdmin() ? '<option value="">همه سازمان‌ها</option>' : ''}
          ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === selectedApptOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
        <select onchange="apptsModeFilter=this.value;apptsPage=1;renderApptsTable()">
          <option value="">همه انواع ویزیت</option>
          <option value="in_person" ${apptsModeFilter === 'in_person' ? 'selected' : ''}>حضوری</option>
          <option value="online_chat" ${apptsModeFilter === 'online_chat' ? 'selected' : ''}>چت آنلاین</option>
        </select>
        <select onchange="apptsStatusFilter=this.value;apptsPage=1;renderApptsTable()">
          <option value="">همه وضعیت‌ها</option>
          <option value="pending" ${apptsStatusFilter === 'pending' ? 'selected' : ''}>در انتظار تأیید</option>
          <option value="confirmed" ${apptsStatusFilter === 'confirmed' ? 'selected' : ''}>تأیید شده</option>
          <option value="completed" ${apptsStatusFilter === 'completed' ? 'selected' : ''}>انجام شده</option>
          <option value="cancelled_by_customer" ${apptsStatusFilter === 'cancelled_by_customer' ? 'selected' : ''}>لغو توسط بیمار</option>
          <option value="cancelled_by_provider" ${apptsStatusFilter === 'cancelled_by_provider' ? 'selected' : ''}>لغو توسط پزشک</option>
          <option value="no_show" ${apptsStatusFilter === 'no_show' ? 'selected' : ''}>غیبت (No-Show)</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>بیمار</th><th>پزشک / خدمت</th><th>نوع ویزیت</th><th>زمان شروع</th><th>وضعیت نوبت</th><th>وضعیت پرداخت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="7"><div class="empty"><div class="empty-icon">🗓️</div><div>نوبتی یافت نشد</div></div></td></tr>`
              : pg.items.map(a => `<tr>
                  <td><strong>${escapeHTML((a.customer?.first_name || '') + ' ' + (a.customer?.last_name || '')) || '—'}</strong><br><span class="td-muted dir-ltr">${escapeHTML(a.customer?.email || '')}</span></td>
                  <td>${escapeHTML((a.provider?.user?.first_name || '') + ' ' + (a.provider?.user?.last_name || ''))}<br><span class="td-muted">${escapeHTML(a.offering?.title || '')}</span></td>
                  <td>${a.visit_mode === 'online_chat' ? '<span class="badge badge-purple">💬 آنلاین</span>' : '<span class="badge badge-blue">🏥 حضوری</span>'}</td>
                  <td class="td-muted">${fmtDate(a.start_at)}</td>
                  <td>${statusBadge(a.status, APPT_STATUS_MAP)}</td>
                  <td>${a.payment ? statusBadge(a.payment.status, PAYMENT_STATUS_MAP) : '<span class="td-muted">رایگان/بدون پرداخت</span>'}<br><span class="td-muted">${fmtMoney(a.price)}</span></td>
                  <td>
                    <div class="row-actions">
                      <button class="btn btn-ghost btn-sm" onclick="openApptDetailModal('${a.id}')">👁️ جزئیات</button>
                      ${a.status === 'pending' ? `<button class="btn btn-success btn-sm" onclick="updateApptStatus('${a.id}','confirmed')">✅ تأیید</button>` : ''}
                      ${a.status === 'confirmed' ? `<button class="btn btn-success btn-sm" onclick="updateApptStatus('${a.id}','completed')">🏁 تکمیل</button>` : ''}
                      ${a.status === 'confirmed' ? `<button class="btn btn-warning btn-sm" onclick="updateApptStatus('${a.id}','no_show')">🚫 غیبت</button>` : ''}
                      ${['pending', 'confirmed'].includes(a.status) ? `<button class="btn btn-danger btn-sm" onclick="openCancelApptModal('${a.id}')">❌ لغو</button>` : ''}
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setApptsPage')}
    </div>
  `;
}

function openApptDetailModal(apptId) {
  const a = apptsData.find(x => x.id === apptId);
  if (!a) return;
  openModal('جزئیات کامل نوبت', `
    <div class="detail-grid">
      <div class="detail-item"><div class="detail-label">شناسه نوبت</div><div class="detail-value dir-ltr" style="font-size:0.75rem">${escapeHTML(a.id)}</div></div>
      <div class="detail-item"><div class="detail-label">وضعیت</div><div class="detail-value">${statusBadge(a.status, APPT_STATUS_MAP)}</div></div>
      <div class="detail-item"><div class="detail-label">بیمار</div><div class="detail-value">${escapeHTML(a.customer?.full_name || a.customer?.email || '—')} (${escapeHTML(a.customer?.phone_number || '—')})</div></div>
      <div class="detail-item"><div class="detail-label">پزشک</div><div class="detail-value">${escapeHTML(a.provider?.user?.full_name || a.provider?.user?.email || '—')}</div></div>
      <div class="detail-item"><div class="detail-label">سازمان / شعبه</div><div class="detail-value">${escapeHTML(a.organization?.name || '—')} / ${escapeHTML(a.branch?.name || 'بدون شعبه')}</div></div>
      <div class="detail-item"><div class="detail-label">خدمت و نوع ویزیت</div><div class="detail-value">${escapeHTML(a.offering?.title || '—')} (${a.visit_mode === 'online_chat' ? 'چت آنلاین' : 'حضوری'})</div></div>
      <div class="detail-item"><div class="detail-label">زمان شروع</div><div class="detail-value">${fmtDate(a.start_at)}</div></div>
      <div class="detail-item"><div class="detail-label">زمان پایان</div><div class="detail-value">${fmtDate(a.end_at)}</div></div>
      <div class="detail-item"><div class="detail-label">هزینه</div><div class="detail-value">${fmtMoney(a.price)}</div></div>
      <div class="detail-item"><div class="detail-label">اطلاعات پرداخت</div><div class="detail-value">${a.payment ? `${a.payment.method === 'online' ? 'آنلاین' : 'در کلینیک'} — ${PAYMENT_STATUS_MAP[a.payment.status]?.label || a.payment.status}` : '—'}</div></div>
      <div class="detail-item" style="grid-column:1/-1"><div class="detail-label">یادداشت بیمار (Notes)</div><div class="detail-value">${escapeHTML(a.notes || '—')}</div></div>
      ${a.cancelled_at ? `
        <div class="detail-item"><div class="detail-label">لغو شده در تاریخ</div><div class="detail-value">${fmtDate(a.cancelled_at)} توسط ${escapeHTML(a.cancelled_by?.email || 'سیستم')}</div></div>
        <div class="detail-item"><div class="detail-label">علت لغو</div><div class="detail-value">${escapeHTML(a.cancel_reason || '—')}</div></div>
      ` : ''}
    </div>
  `, `<button class="btn btn-ghost" onclick="closeModal()">بستن</button>`, true);
}

async function updateApptStatus(id, newStatus) {
  try {
    await apiPatch(`/appointments/${id}/status/`, { status: newStatus });
    toast('وضعیت نوبت بروزرسانی شد');
    await renderAppointments();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

function openCancelApptModal(apptId) {
  openModal('لغو نوبت', `
    <p style="font-size:0.86rem;color:var(--textSub);margin-bottom:14px">لطفاً در صورت تمایل علت لغو این نوبت را وارد کنید (در ایمیل و اعلان برای بیمار و پزشک ارسال می‌شود):</p>
    <div class="form-group">
      <label class="form-label">علت لغو نوبت</label>
      <textarea id="cancel-appt-reason" class="form-control" rows="3" placeholder="مثلاً: عدم حضور پزشک / درخواست بیمار…"></textarea>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-danger" onclick="submitCancelAppt('${apptId}')">تأیید و لغو نوبت</button>
  `);
}

async function submitCancelAppt(id) {
  const cancel_reason = document.getElementById('cancel-appt-reason')?.value.trim() || '';
  try {
    await apiPost(`/appointments/${id}/cancel/`, { cancel_reason });
    closeModal();
    toast('نوبت با موفقیت لغو شد');
    await renderAppointments();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   11. PAYMENTS (پرداخت‌ها)
═══════════════════════════════════════════════════════ */
let paymentsData = [];
let paymentsPage = 1;
let selectedPaymentOrgId = '';
let paymentStatusFilter = '';

async function renderPayments() {
  const el = document.getElementById('page');
  try {
    await loadCommonLists();
    if (!selectedPaymentOrgId && cachedOrgs.length > 0) {
      selectedPaymentOrgId = cachedOrgs[0].id;
    }

    if (!selectedPaymentOrgId) {
      el.innerHTML = `<div class="empty"><div class="empty-icon">💳</div><div class="empty-title">ابتدا یک سازمان ایجاد کنید</div></div>`;
      return;
    }

    let url = withPageSize(`/payments/organizations/${selectedPaymentOrgId}/`);
    if (paymentStatusFilter) url += `&status=${encodeURIComponent(paymentStatusFilter)}`;
    const data = await apiGet(url);
    paymentsData = data.results || data || [];
    renderPaymentsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setPaymentsPage(p) {
  paymentsPage = p;
  renderPaymentsTable();
}

function renderPaymentsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(paymentsData, paymentsPage);

  el.innerHTML = `
    <div class="page-header">
      <div><h1>💳 مدیریت پرداخت‌ها</h1><div class="page-header-sub">${paymentsData.length} تراکنش</div></div>
      <button class="btn btn-ghost" onclick="renderPayments()">🔄 بروزرسانی</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <select onchange="selectedPaymentOrgId=this.value;paymentsPage=1;renderPayments()">
          ${cachedOrgs.map(o => `<option value="${o.id}" ${o.id === selectedPaymentOrgId ? 'selected' : ''}>${escapeHTML(o.name)}</option>`).join('')}
        </select>
        <select onchange="paymentStatusFilter=this.value;paymentsPage=1;renderPayments()">
          <option value="">همه وضعیت‌ها</option>
          <option value="pending" ${paymentStatusFilter === 'pending' ? 'selected' : ''}>در انتظار پرداخت (pending)</option>
          <option value="paid" ${paymentStatusFilter === 'paid' ? 'selected' : ''}>پرداخت شده (paid)</option>
          <option value="failed" ${paymentStatusFilter === 'failed' ? 'selected' : ''}>ناموفق (failed)</option>
          <option value="cancelled" ${paymentStatusFilter === 'cancelled' ? 'selected' : ''}>لغو شده (cancelled)</option>
          <option value="refunded" ${paymentStatusFilter === 'refunded' ? 'selected' : ''}>بازپرداخت شده (refunded)</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>شناسه پرداخت</th><th>شناسه نوبت</th><th>مبلغ</th><th>روش پرداخت</th><th>وضعیت</th><th>تاریخ پرداخت</th><th>تاریخ ایجاد</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="8"><div class="empty"><div class="empty-icon">💳</div><div>تراکنشی یافت نشد</div></div></td></tr>`
              : pg.items.map(p => `<tr>
                  <td class="td-muted dir-ltr" title="${escapeHTML(p.id)}">${escapeHTML((p.id || '').substring(0, 8))}…</td>
                  <td class="td-muted dir-ltr" title="${escapeHTML(p.appointment)}">${escapeHTML(String(p.appointment || '').substring(0, 8))}…</td>
                  <td><strong>${fmtMoney(p.amount)}</strong></td>
                  <td>${p.method === 'online' ? '<span class="badge badge-blue">🌐 آنلاین</span>' : '<span class="badge badge-amber">🏥 حضوری (در کلینیک)</span>'}</td>
                  <td>${statusBadge(p.status, PAYMENT_STATUS_MAP)}</td>
                  <td class="td-muted">${fmtDate(p.paid_at)}</td>
                  <td class="td-muted">${fmtDate(p.created_at)}</td>
                  <td>
                    <div class="row-actions">
                      ${p.status === 'paid' ? `<button class="btn btn-danger btn-sm" onclick="refundPayment('${p.id}')">↩️ ثبت بازپرداخت</button>` : ''}
                      ${p.status === 'pending' && p.method === 'in_person' ? `<button class="btn btn-success btn-sm" onclick="markPaid('${p.id}')">✅ دریافت نقدی/کارتخوان</button>` : ''}
                    </div>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setPaymentsPage')}
    </div>
  `;
}

async function refundPayment(id) {
  if (!confirm('آیا از تغییر وضعیت این پرداخت به «بازپرداخت شده (Refunded)» اطمینان دارید؟')) return;
  try {
    await apiPost(`/payments/${id}/refund/`, {});
    toast('بازپرداخت با موفقیت ثبت شد');
    await renderPayments();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

async function markPaid(id) {
  try {
    await apiPost(`/payments/${id}/mark-paid/`, {});
    toast('پرداخت حضوری تایید شد');
    await renderPayments();
  } catch (e) {
    toast(formatApiError(e), 'error');
  }
}

/* ═══════════════════════════════════════════════════════
   12. CHATS (مشاهده مکالمات به صورت Read-Only)
═══════════════════════════════════════════════════════ */
let chatsData = [];
let chatsPage = 1;
let chatsSearch = '';
let usingAdminChatEndpoint = false;

async function renderChats() {
  const el = document.getElementById('page');
  try {
    // Try admin endpoint first (/api/v1/admin/conversations/), fallback to /api/v1/chat/conversations/
    try {
      const adminData = await apiGet(withPageSize('/admin/conversations/'));
      chatsData = adminData.results || adminData || [];
      usingAdminChatEndpoint = true;
    } catch {
      const userData = await apiGet(withPageSize('/chat/conversations/'));
      chatsData = userData.results || userData || [];
      usingAdminChatEndpoint = false;
    }
    renderChatsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setChatsPage(p) {
  chatsPage = p;
  renderChatsTable();
}

function renderChatsTable() {
  const el = document.getElementById('page');
  const filtered = chatsData.filter(c => {
    if (!chatsSearch) return true;
    const q = chatsSearch.toLowerCase();
    const cust = `${c.customer?.first_name || ''} ${c.customer?.last_name || ''} ${c.customer?.email || ''}`.toLowerCase();
    const prov = `${c.provider?.first_name || ''} ${c.provider?.last_name || ''} ${c.provider?.email || ''}`.toLowerCase();
    return cust.includes(q) || prov.includes(q);
  });

  const pg = paginateLocal(filtered, chatsPage);

  el.innerHTML = `
    <div class="page-header">
      <div>
        <h1>💬 مکالمات چت پزشکی (Read-Only)</h1>
        <div class="page-header-sub">نظارت فقط-خواندنی بر اتاق‌های گفت‌وگوی بیمار و پزشک</div>
      </div>
      <button class="btn btn-ghost" onclick="renderChats()">🔄 بروزرسانی</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو بر اساس نام یا ایمیل بیمار / پزشک…" value="${escapeHTML(chatsSearch)}" oninput="chatsSearch=this.value;chatsPage=1;renderChatsTable()" />
        </div>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>بیمار (Customer)</th><th>پزشک (Provider)</th><th>آخرین پیام</th><th>آخرین بروزرسانی</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">💬</div><div class="empty-title">مکالمه‌ای برای نمایش وجود ندارد</div><div class="empty-sub">${!usingAdminChatEndpoint ? 'توجه: در حال حاضر اندپوینت /chat/conversations/ فقط مکالمات کاربر لاگین‌شده را برمی‌گرداند. در گام بعدی با افزودن ویوی کوچک ادمین در بک‌اند، تمام مکالمات کلینیک اینجا لیست می‌شوند.' : ''}</div></div></td></tr>`
              : pg.items.map(c => `<tr>
                  <td><strong>${escapeHTML(c.customer?.full_name || '—')}</strong><br><span class="td-muted dir-ltr">${escapeHTML(c.customer?.email || '')}</span></td>
                  <td><strong>${escapeHTML(c.provider?.full_name || '—')}</strong><br><span class="td-muted dir-ltr">${escapeHTML(c.provider?.email || '')}</span></td>
                  <td class="td-muted">${c.last_message ? (c.last_message.is_deleted ? '🚫 <em>پیام حذف‌شده توسط پزشک</em>' : escapeHTML((c.last_message.content || `[فایل ${c.last_message.type}]`).substring(0, 50))) : 'بدون پیام'}</td>
                  <td class="td-muted">${fmtDate(c.updated_at)}</td>
                  <td>
                    <button class="btn btn-ghost btn-sm" onclick="openChatHistoryModal('${c.id}')">👁️ مشاهده تاریخچه پیام‌ها</button>
                  </td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setChatsPage')}
    </div>
  `;
}

async function openChatHistoryModal(convId) {
  const conv = chatsData.find(x => x.id === convId);
  if (!conv) return;

  openModal(
    `تاریخچه گفت‌وگو (Read-Only): ${conv.customer?.full_name || conv.customer?.email} ↔ ${conv.provider?.full_name || conv.provider?.email}`,
    `<div class="loading-center"><div class="spinner"></div></div>`,
    `<button class="btn btn-ghost" onclick="closeModal()">بستن</button>`,
    true
  );

  try {
    let res;
    if (usingAdminChatEndpoint) {
      res = await apiGet(`/admin/conversations/${convId}/messages/`);
    } else {
      res = await apiGet(`/chat/conversations/${convId}/messages/`);
    }
    const messages = (res.results || res || []).slice().reverse(); // chronological order

    const bodyEl = document.getElementById('modal-body');
    if (!bodyEl) return;

    if (messages.length === 0) {
      bodyEl.innerHTML = `<div class="empty"><div class="empty-icon">📭</div><div>هنوز پیامی در این گفت‌وگو ارسال نشده است</div></div>`;
      return;
    }

    bodyEl.innerHTML = `
      <div style="margin-bottom:10px;font-size:0.78rem;color:var(--textMuted)">
        🔒 این نما صرفاً جهت نظارت پزشکی (Read-Only) است و امکان ارسال یا ویرایش پیام توسط ادمین وجود ندارد.
      </div>
      <div class="chat-thread">
        ${messages.map(m => {
          const isDoctor = String(m.sender_id) === String(conv.provider?.id);
          const roleClass = isDoctor ? 'doctor' : 'patient';
          const senderName = isDoctor
            ? `👨‍⚕️ پزشک (${escapeHTML(conv.provider?.full_name || conv.provider?.email || '')})`
            : `👤 بیمار (${escapeHTML(conv.customer?.full_name || conv.customer?.email || '')})`;

          return `
            <div class="chat-bubble ${roleClass} ${m.is_deleted ? 'deleted' : ''}">
              <div class="chat-sender">
                <span>${senderName}</span>
                <span class="badge ${isDoctor ? 'badge-purple' : 'badge-blue'}">${escapeHTML(m.type)}</span>
              </div>
              ${m.is_deleted
                ? `<div>🚫 <em>این پیام در تاریخ ${fmtDate(m.deleted_at)} توسط پزشک حذف (Soft Delete) شده است.</em></div>`
                : `
                  ${m.content ? `<div>${escapeHTML(m.content)}</div>` : ''}
                  ${m.attachment ? `<div style="margin-top:6px"><a href="${escapeHTML(m.attachment)}" target="_blank" class="btn btn-ghost btn-sm">📎 مشاهده پیوست (${escapeHTML(m.file_name || m.type)})</a></div>` : ''}
                `
              }
              <div class="chat-time">${fmtDate(m.created_at)}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (e) {
    const bodyEl = document.getElementById('modal-body');
    if (bodyEl) bodyEl.innerHTML = errorHTML(e);
  }
}

/* ═══════════════════════════════════════════════════════
   13. NOTIFICATION DELIVERIES
═══════════════════════════════════════════════════════ */
let notifsData = [];
let notifsPage = 1;
let notifChannelFilter = '';
let notifStatusFilter = '';
let notifSearch = '';

async function renderNotifications() {
  const el = document.getElementById('page');
  try {
    let url = withPageSize('/admin/notification-deliveries/');
    if (notifChannelFilter) url += `&channel=${encodeURIComponent(notifChannelFilter)}`;
    if (notifStatusFilter) url += `&status=${encodeURIComponent(notifStatusFilter)}`;
    if (notifSearch) url += `&search=${encodeURIComponent(notifSearch)}`;
    const data = await apiGet(url);
    notifsData = data.results || data || [];
    renderNotifsTable();
  } catch (e) {
    el.innerHTML = errorHTML(e);
  }
}

function setNotifsPage(p) {
  notifsPage = p;
  renderNotifsTable();
}

function renderNotifsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(notifsData, notifsPage);
  const NOTIF_STATUS_MAP = {
    sent:    { label: 'ارسال شده', cls: 'badge-green' },
    failed:  { label: 'ناموفق',    cls: 'badge-rose'  },
    pending: { label: 'در صف',     cls: 'badge-amber' },
    skipped: { label: 'رد شده',    cls: 'badge-gray'  },
  };

  el.innerHTML = `
    <div class="page-header">
      <div><h1>🔔 لاگ ارسال نوتیفیکیشن</h1><div class="page-header-sub">${notifsData.length} رکورد</div></div>
      <button class="btn btn-ghost" onclick="renderNotifications()">🔄 بروزرسانی</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو در گیرنده یا موضوع…" value="${escapeHTML(notifSearch)}" onchange="notifSearch=this.value;notifsPage=1;renderNotifications()" />
        </div>
        <select onchange="notifChannelFilter=this.value;notifsPage=1;renderNotifications()">
          <option value="">همه کانال‌ها</option>
          <option value="email" ${notifChannelFilter === 'email' ? 'selected' : ''}>📧 ایمیل (email)</option>
          <option value="push" ${notifChannelFilter === 'push' ? 'selected' : ''}>📱 پوش نوتیفیکیشن (push)</option>
          <option value="sms" ${notifChannelFilter === 'sms' ? 'selected' : ''}>📟 پیامک (sms)</option>
          <option value="in_app" ${notifChannelFilter === 'in_app' ? 'selected' : ''}>🔔 درون‌برنامه‌ای (in_app)</option>
        </select>
        <select onchange="notifStatusFilter=this.value;notifsPage=1;renderNotifications()">
          <option value="">همه وضعیت‌ها</option>
          <option value="sent" ${notifStatusFilter === 'sent' ? 'selected' : ''}>ارسال شده (sent)</option>
          <option value="pending" ${notifStatusFilter === 'pending' ? 'selected' : ''}>در صف (pending)</option>
          <option value="failed" ${notifStatusFilter === 'failed' ? 'selected' : ''}>ناموفق (failed)</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>کانال</th><th>گیرنده</th><th>موضوع</th><th>نوع رویداد</th><th>وضعیت</th><th>زمان ارسال</th><th>پیام خطا</th></tr></thead>
          <tbody>
            ${pg.items.length === 0
              ? `<tr><td colspan="7"><div class="empty"><div class="empty-icon">🔔</div><div>لاگی یافت نشد</div></div></td></tr>`
              : pg.items.map(n => `<tr>
                  <td>${n.channel === 'email' ? '📧 ایمیل' : n.channel === 'push' ? '📱 پوش' : '📟 ' + escapeHTML(n.channel)}</td>
                  <td class="td-muted dir-ltr">${escapeHTML(n.recipient || '—')}</td>
                  <td>${escapeHTML(n.subject || '—')}</td>
                  <td class="td-muted dir-ltr" style="font-size:0.75rem">${escapeHTML(n.type || '')}</td>
                  <td>${statusBadge(n.status, NOTIF_STATUS_MAP)}</td>
                  <td class="td-muted">${fmtDate(n.sent_at || n.created_at)}</td>
                  <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.75rem;color:var(--rose)" title="${escapeHTML(n.error_message || '')}">${escapeHTML(n.error_message || '—')}</td>
                </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'setNotifsPage')}
    </div>
  `;
}
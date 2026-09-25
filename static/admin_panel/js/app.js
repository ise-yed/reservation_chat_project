/* ═══════════════════════════════════════════════════════
   CONFIG
═══════════════════════════════════════════════════════ */
const API = '/api/v1';
let authToken = localStorage.getItem('admin_token') || null;
let currentUser = JSON.parse(localStorage.getItem('admin_user') || 'null');

/* ═══════════════════════════════════════════════════════
   API HELPER
═══════════════════════════════════════════════════════ */
async function api(method, path, body = null, skipAuth = false) {
  const headers = { 'Content-Type': 'application/json' };
  if (authToken && !skipAuth) headers['Authorization'] = `Bearer ${authToken}`;
  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API + path, opts);
  if (res.status === 401) { doLogout(); return; }
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw data;
  return data;
}

async function apiGet(path) { return api('GET', path); }
async function apiPost(path, body) { return api('POST', path, body); }
async function apiPatch(path, body) { return api('PATCH', path, body); }
async function apiDelete(path) { return api('DELETE', path); }

/* ═══════════════════════════════════════════════════════
   AUTH
═══════════════════════════════════════════════════════ */
async function doLogin() {
  const email = document.getElementById('login-email').value.trim();
  const pw    = document.getElementById('login-password').value;
  const btn   = document.getElementById('btn-login-submit');
  const err   = document.getElementById('login-error');
  err.classList.remove('show');
  if (!email || !pw) { showErr(err, 'لطفاً ایمیل و رمز را وارد کنید'); return; }
  btn.disabled = true; btn.textContent = 'در حال ورود…';
  try {
    const data = await api('POST', '/auth/login/', { email, password: pw }, true);
    authToken = data.tokens?.access || data.access;
    const refreshToken = data.tokens?.refresh || data.refresh;
    localStorage.setItem('admin_token', authToken);
    if (refreshToken) localStorage.setItem('admin_refresh_token', refreshToken);
    // fetch me
    const me = await apiGet('/auth/me/');
    const adminRoles = ['staff','org_admin','super_admin'];
    if (!me.is_staff && !adminRoles.includes(me.role)) {
      showErr(err, 'شما دسترسی ادمین ندارید'); authToken = null; localStorage.removeItem('admin_token'); return;
    }
    currentUser = me;
    localStorage.setItem('admin_user', JSON.stringify(me));
    initApp();
  } catch(e) {
    const msg = typeof e === 'object' ? (e.detail || e.non_field_errors?.[0] || 'خطا در ورود') : 'خطا در ورود';
    showErr(err, msg);
  } finally { btn.disabled = false; btn.textContent = 'ورود'; }
}

function showErr(el, msg) { el.textContent = msg; el.classList.add('show'); }

document.getElementById('login-password').addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });

function doLogout() {
  authToken = null; currentUser = null;
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_refresh_token');
  localStorage.removeItem('admin_user');
  document.getElementById('app').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}

function initApp() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = 'flex';
  // populate user info
  const name = currentUser?.first_name || currentUser?.email?.split('@')[0] || 'ادمین';
  document.getElementById('user-name').textContent = currentUser?.email || name;
  document.getElementById('user-role').textContent = currentUser?.role || '';
  document.getElementById('user-avatar').textContent = (currentUser?.first_name?.[0] || currentUser?.email?.[0] || 'A').toUpperCase();
  navigate('dashboard');
}

// Auto-login if token exists
if (authToken && currentUser) {
  initApp();
}

/* ═══════════════════════════════════════════════════════
   ROUTER
═══════════════════════════════════════════════════════ */
const PAGE_TITLES = {
  dashboard: 'داشبورد', users: 'کاربران', organizations: 'سازمان‌ها',
  branches: 'شعب', providers: 'پزشکان', offerings: 'خدمات', categories: 'تخصص‌ها',
  holidays: 'تعطیلات سازمان', appointments: 'نوبت‌ها', payments: 'پرداخت‌ها',
  notifications: 'لاگ نوتیفیکیشن',
};

function navigate(page, params={}) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const target = document.querySelector(`.nav-item[onclick="navigate('${page}')"]`);
  if (target) target.classList.add('active');
  document.getElementById('topbar-title').textContent = PAGE_TITLES[page] || page;
  const pageEl = document.getElementById('page');
  pageEl.innerHTML = '<div class="loading-center"><div class="spinner"></div></div>';

  const routes = {
    dashboard: renderDashboard,
    users: renderUsers,
    organizations: renderOrganizations,
    branches: renderBranches,
    providers: renderProviders,
    offerings: renderOfferings,
    categories: renderCategories,
    holidays: renderHolidays,
    appointments: renderAppointments,
    payments: renderPayments,
    notifications: renderNotifications,
  };
  (routes[page] || (() => pageEl.innerHTML = '<div class="empty"><div class="empty-icon">🚧</div><div class="empty-title">صفحه در دست ساخت</div></div>'))(params);
}

/* ═══════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════ */
function toast(msg, type = 'success') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toast-container').appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

/* ═══════════════════════════════════════════════════════
   MODAL
═══════════════════════════════════════════════════════ */
function openModal(title, bodyHTML, footerHTML='') {
  document.getElementById('modal-title').textContent = title;
  document.getElementById('modal-body').innerHTML = bodyHTML;
  document.getElementById('modal-footer').innerHTML = footerHTML;
  document.getElementById('modal-overlay').classList.add('open');
}
function closeModal() { document.getElementById('modal-overlay').classList.remove('open'); }
function closeModalOnBackdrop(e) { if (e.target.id === 'modal-overlay') closeModal(); }

/* ═══════════════════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════════════════ */
function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString('fa-IR', { dateStyle:'short', timeStyle:'short' });
}
function fmtMoney(n) { return Number(n||0).toLocaleString('fa-IR') + ' تومان'; }

function statusBadge(status, map) {
  const m = map[status] || { label: status, cls: 'badge-gray' };
  return `<span class="badge ${m.cls}">${m.label}</span>`;
}

const APPT_STATUS_MAP = {
  pending:               { label: 'در انتظار',    cls: 'badge-amber'  },
  confirmed:             { label: 'تأیید شده',    cls: 'badge-green'  },
  cancelled_by_customer: { label: 'لغو توسط بیمار', cls: 'badge-rose'  },
  cancelled_by_provider: { label: 'لغو توسط پزشک',  cls: 'badge-rose'  },
  completed:             { label: 'انجام شده',    cls: 'badge-cyan'   },
  no_show:               { label: 'غیبت',         cls: 'badge-gray'   },
};
const PAYMENT_STATUS_MAP = {
  pending:  { label: 'در انتظار', cls: 'badge-amber'  },
  paid:     { label: 'پرداخت شده', cls: 'badge-green' },
  failed:   { label: 'ناموفق',    cls: 'badge-rose'   },
  cancelled:{ label: 'لغو شده',   cls: 'badge-gray'   },
  refunded: { label: 'بازپرداخت', cls: 'badge-cyan'   },
};
const ROLE_MAP = {
  customer:    { label: 'بیمار',       cls: 'badge-blue'   },
  provider:    { label: 'پزشک',        cls: 'badge-green'  },
  staff:       { label: 'استاف',       cls: 'badge-amber'  },
  org_admin:   { label: 'ادمین سازمان', cls: 'badge-purple' },
  super_admin: { label: 'سوپر ادمین',  cls: 'badge-rose'   },
};

function paginateLocal(items, page, perPage=20) {
  const total = items.length;
  const pages = Math.ceil(total / perPage);
  const slice = items.slice((page-1)*perPage, page*perPage);
  return { items: slice, total, pages, page };
}

function renderPagination(p, onPage) {
  if (p.pages <= 1) return '';
  let btns = '';
  for (let i = 1; i <= p.pages; i++) {
    btns += `<button class="page-btn${i===p.page?' active':''}" onclick="(${onPage})(${i})">${i}</button>`;
  }
  return `<div class="pagination"><span class="page-info">${p.total} مورد</span>${btns}</div>`;
}

/* ═══════════════════════════════════════════════════════
   DASHBOARD
═══════════════════════════════════════════════════════ */
async function renderDashboard() {
  const el = document.getElementById('page');
  try {
    const stats = await apiGet('/admin/dashboard/stats/');
    const appts = stats.appointments || {};
    const rev   = stats.revenue     || {};
    const prov  = stats.providers   || {};
    const users = stats.users       || {};
    const pymts = stats.payments    || {};
    const recent = stats.recent_appointments || [];

    const bySt  = appts.by_status  || {};
    const pyBySt = pymts.by_status || {};

    el.innerHTML = `
      <div class="page-header">
        <div>
          <h1>📊 داشبورد</h1>
          <div class="page-header-sub">نگاه کلی به عملکرد سیستم</div>
        </div>
      </div>

      <div class="stat-grid">
        <div class="stat-card" style="--card-color:var(--accent)">
          <div class="stat-icon">🗓️</div>
          <div class="stat-label">نوبت‌های امروز</div>
          <div class="stat-value">${appts.today ?? 0}</div>
          <div class="stat-sub">${appts.this_month ?? 0} نوبت این ماه</div>
        </div>
        <div class="stat-card" style="--card-color:var(--green)">
          <div class="stat-icon">💰</div>
          <div class="stat-label">درآمد این ماه</div>
          <div class="stat-value">${(rev.this_month||0).toLocaleString('fa-IR')}</div>
          <div class="stat-sub">کل: ${(rev.total||0).toLocaleString('fa-IR')} تومان</div>
        </div>
        <div class="stat-card" style="--card-color:var(--cyan)">
          <div class="stat-icon">👨‍⚕️</div>
          <div class="stat-label">پزشکان فعال</div>
          <div class="stat-value">${prov.active ?? 0}</div>
          <div class="stat-sub">&nbsp;</div>
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
        </div>
        <div class="stat-card" style="--card-color:var(--amber)">
          <div class="stat-icon">⏳</div>
          <div class="stat-label">نوبت در انتظار</div>
          <div class="stat-value">${bySt.pending ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--green)">
          <div class="stat-icon">💳</div>
          <div class="stat-label">پرداخت موفق</div>
          <div class="stat-value">${pyBySt.paid ?? 0}</div>
        </div>
        <div class="stat-card" style="--card-color:var(--rose)">
          <div class="stat-icon">❌</div>
          <div class="stat-label">پرداخت ناموفق</div>
          <div class="stat-value">${pyBySt.failed ?? 0}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">🗓️ آخرین نوبت‌ها</div>
        <div class="table-wrapper">
          <table>
            <thead><tr>
              <th>بیمار</th><th>پزشک</th><th>سازمان</th><th>زمان</th><th>وضعیت</th>
            </tr></thead>
            <tbody>
              ${recent.length === 0 ? `<tr><td colspan="5"><div class="empty"><div class="empty-icon">📭</div><div>نوبتی وجود ندارد</div></div></td></tr>` :
                recent.map(a => `<tr>
                  <td>${a['customer__first_name']||''} ${a['customer__last_name']||''}<br><span class="td-muted">${a['customer__email']||''}</span></td>
                  <td>${a['provider__user__first_name']||''} ${a['provider__user__last_name']||''}</td>
                  <td>${a['organization__name']||''}</td>
                  <td class="td-muted">${fmtDate(a.start_at)}</td>
                  <td>${statusBadge(a.status, APPT_STATUS_MAP)}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;
  } catch(e) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">خطا در بارگذاری</div><div class="empty-sub">${JSON.stringify(e)}</div></div>`;
  }
}

/* ═══════════════════════════════════════════════════════
   USERS
═══════════════════════════════════════════════════════ */
let usersData = []; let usersPage = 1; let usersSearch = ''; let usersRoleFilter = '';
async function renderUsers() {
  const el = document.getElementById('page');
  try {
    let url = '/admin/users/?ordering=-created_at';
    if (usersSearch) url += `&search=${encodeURIComponent(usersSearch)}`;
    if (usersRoleFilter) url += `&role=${usersRoleFilter}`;
    const data = await apiGet(url);
    usersData = data.results || data;
    renderUsersTable();
  } catch(e) {
    el.innerHTML = `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">خطا</div></div>`;
  }
}

function renderUsersTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(usersData, usersPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>👥 کاربران</h1><div class="page-header-sub">${usersData.length} کاربر</div></div>
      ${currentUser?.role === 'super_admin' ? `<button class="btn btn-primary" onclick="openCreateUserModal()">➕ کاربر جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="toolbar">
        <div class="search-box">
          <span>🔍</span>
          <input type="text" placeholder="جستجو بر اساس ایمیل / نام…" id="user-search-inp" value="${usersSearch}" oninput="usersSearch=this.value; usersPage=1; renderUsersTable()" />
        </div>
        <select id="user-role-filter" onchange="usersRoleFilter=this.value; usersPage=1; renderUsers()">
          <option value="">همه نقش‌ها</option>
          <option value="customer">بیمار</option>
          <option value="provider">پزشک</option>
          <option value="staff">استاف</option>
          <option value="org_admin">ادمین سازمان</option>
          <option value="super_admin">سوپر ادمین</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>ایمیل</th><th>نام</th><th>نقش</th><th>فعال</th><th>تأیید شده</th><th>تاریخ عضویت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.length === 0 ? `<tr><td colspan="7"><div class="empty"><div class="empty-icon">👻</div><div>نتیجه‌ای یافت نشد</div></div></td></tr>` :
              pg.items.filter(u => {
                if (!usersSearch) return true;
                const q = usersSearch.toLowerCase();
                return (u.email||'').toLowerCase().includes(q) || (u.first_name||'').includes(q) || (u.last_name||'').includes(q);
              }).map(u => `<tr>
                <td>${u.email}</td>
                <td>${u.first_name||''} ${u.last_name||''}</td>
                <td>${statusBadge(u.role, ROLE_MAP)}</td>
                <td>${u.is_active ? '<span class="badge badge-green">بله</span>' : '<span class="badge badge-gray">خیر</span>'}</td>
                <td>${u.is_verified ? '<span class="badge badge-green">بله</span>' : '<span class="badge badge-amber">خیر</span>'}</td>
                <td class="td-muted">${fmtDate(u.created_at)}</td>
                <td><div class="row-actions">
                  ${currentUser?.role === 'super_admin' ? `<button class="btn btn-ghost btn-sm" onclick='openEditUserModal(${JSON.stringify(u)})'>✏️ ویرایش</button>` : ''}
                </div></td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{usersPage=p;renderUsersTable()}')}
    </div>
  `;
  // restore filter value
  const sel = document.getElementById('user-role-filter');
  if (sel) sel.value = usersRoleFilter;
}

function openCreateUserModal() {
  openModal('کاربر جدید', `
    <div class="form-row">
      <div class="form-group"><label class="form-label">ایمیل *</label><input id="fu-email" class="form-control" placeholder="email@example.com"></div>
      <div class="form-group"><label class="form-label">رمز عبور *</label><input id="fu-pw" type="password" class="form-control" placeholder="حداقل ۸ کاراکتر"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام</label><input id="fu-fn" class="form-control" placeholder="نام"></div>
      <div class="form-group"><label class="form-label">نام خانوادگی</label><input id="fu-ln" class="form-control" placeholder="نام خانوادگی"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="fu-phone" class="form-control" placeholder="09…"></div>
      <div class="form-group"><label class="form-label">نقش</label>
        <select id="fu-role" class="form-control">
          <option value="customer">بیمار</option>
          <option value="provider">پزشک</option>
          <option value="staff">استاف</option>
          <option value="org_admin">ادمین سازمان</option>
          <option value="super_admin">سوپر ادمین</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateUser()">ذخیره</button>
  `);
}

async function submitCreateUser() {
  const body = {
    email: document.getElementById('fu-email').value,
    password: document.getElementById('fu-pw').value,
    first_name: document.getElementById('fu-fn').value,
    last_name: document.getElementById('fu-ln').value,
    phone_number: document.getElementById('fu-phone').value,
    role: document.getElementById('fu-role').value,
  };
  try {
    await apiPost('/admin/users/', body);
    closeModal(); toast('کاربر ایجاد شد');
    await renderUsers();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditUserModal(u) {
  openModal(`ویرایش: ${u.email}`, `
    <div class="form-row">
      <div class="form-group"><label class="form-label">نام</label><input id="eu-fn" class="form-control" value="${u.first_name||''}"></div>
      <div class="form-group"><label class="form-label">نام خانوادگی</label><input id="eu-ln" class="form-control" value="${u.last_name||''}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eu-phone" class="form-control" value="${u.phone_number||''}"></div>
      <div class="form-group"><label class="form-label">نقش</label>
        <select id="eu-role" class="form-control">
          <option value="customer" ${u.role==='customer'?'selected':''}>بیمار</option>
          <option value="provider" ${u.role==='provider'?'selected':''}>پزشک</option>
          <option value="staff" ${u.role==='staff'?'selected':''}>استاف</option>
          <option value="org_admin" ${u.role==='org_admin'?'selected':''}>ادمین سازمان</option>
          <option value="super_admin" ${u.role==='super_admin'?'selected':''}>سوپر ادمین</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">فعال</label>
        <select id="eu-active" class="form-control">
          <option value="true" ${u.is_active?'selected':''}>بله</option>
          <option value="false" ${!u.is_active?'selected':''}>خیر</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">تأیید شده</label>
        <select id="eu-verified" class="form-control">
          <option value="true" ${u.is_verified?'selected':''}>بله</option>
          <option value="false" ${!u.is_verified?'selected':''}>خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditUser('${u.id}')">ذخیره</button>
  `);
}

async function submitEditUser(id) {
  const body = {
    first_name: document.getElementById('eu-fn').value,
    last_name: document.getElementById('eu-ln').value,
    phone_number: document.getElementById('eu-phone').value,
    role: document.getElementById('eu-role').value,
    is_active: document.getElementById('eu-active').value === 'true',
    is_verified: document.getElementById('eu-verified').value === 'true',
  };
  try {
    await apiPatch(`/admin/users/${id}/`, body);
    closeModal(); toast('کاربر بروزرسانی شد');
    await renderUsers();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   ORGANIZATIONS
═══════════════════════════════════════════════════════ */
let orgsData = []; let orgsPage = 1;
async function renderOrganizations() {
  const el = document.getElementById('page');
  try {
    const data = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    orgsData = data.results || data;
    renderOrgsTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderOrgsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(orgsData, orgsPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>🏢 سازمان‌ها</h1><div class="page-header-sub">${orgsData.length} سازمان</div></div>
      ${currentUser?.role === 'super_admin' ? `<button class="btn btn-primary" onclick="openCreateOrgModal()">➕ سازمان جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام</th><th>Slug</th><th>شماره تماس</th><th>وضعیت</th><th>تاریخ</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(o => `<tr>
              <td><strong>${o.name}</strong></td>
              <td class="td-muted">${o.slug||''}</td>
              <td>${o.phone_number||'—'}</td>
              <td>${o.is_active?'<span class="badge badge-green">فعال</span>':'<span class="badge badge-gray">غیرفعال</span>'}</td>
              <td class="td-muted">${fmtDate(o.created_at)}</td>
              <td><div class="row-actions">
                <button class="btn btn-ghost btn-sm" onclick='openEditOrgModal(${JSON.stringify(o)})'>✏️</button>
              </div></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{orgsPage=p;renderOrgsTable()}')}
    </div>
  `;
}

function openCreateOrgModal() {
  openModal('سازمان جدید', `
    <div class="form-group"><label class="form-label">نام *</label><input id="fo-name" class="form-control"></div>
    <div class="form-group"><label class="form-label">Slug</label><input id="fo-slug" class="form-control" placeholder="auto"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="fo-desc" class="form-control" rows="2"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="fo-phone" class="form-control"></div>
      <div class="form-group"><label class="form-label">ایمیل</label><input id="fo-email" class="form-control"></div>
    </div>
    <div class="form-group"><label class="form-label">وبسایت</label><input id="fo-website" class="form-control"></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateOrg()">ذخیره</button>
  `);
}

async function submitCreateOrg() {
  const name = document.getElementById('fo-name').value.trim();
  if (!name) { toast('نام الزامی است', 'error'); return; }
  const body = {
    name,
    slug: document.getElementById('fo-slug').value || name.toLowerCase().replace(/\s+/g,'-'),
    description: document.getElementById('fo-desc').value,
    phone_number: document.getElementById('fo-phone').value,
    email: document.getElementById('fo-email').value,
    website: document.getElementById('fo-website').value,
  };
  try {
    await apiPost('/organizations/', body);
    closeModal(); toast('سازمان ایجاد شد');
    await renderOrganizations();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditOrgModal(o) {
  openModal(`ویرایش: ${o.name}`, `
    <div class="form-group"><label class="form-label">نام</label><input id="eo-name" class="form-control" value="${o.name||''}"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="eo-desc" class="form-control" rows="2">${o.description||''}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eo-phone" class="form-control" value="${o.phone_number||''}"></div>
      <div class="form-group"><label class="form-label">ایمیل</label><input id="eo-email" class="form-control" value="${o.email||''}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">وبسایت</label><input id="eo-website" class="form-control" value="${o.website||''}"></div>
      <div class="form-group"><label class="form-label">فعال</label>
        <select id="eo-active" class="form-control">
          <option value="true" ${o.is_active?'selected':''}>بله</option>
          <option value="false" ${!o.is_active?'selected':''}>خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditOrg('${o.id}')">ذخیره</button>
  `);
}

async function submitEditOrg(id) {
  const body = {
    name: document.getElementById('eo-name').value,
    description: document.getElementById('eo-desc').value,
    phone_number: document.getElementById('eo-phone').value,
    email: document.getElementById('eo-email').value,
    website: document.getElementById('eo-website').value,
    is_active: document.getElementById('eo-active').value === 'true',
  };
  try {
    await apiPatch(`/organizations/${id}/`, body);
    closeModal(); toast('سازمان بروزرسانی شد');
    await renderOrganizations();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   BRANCHES
═══════════════════════════════════════════════════════ */
let branchesData = []; let branchesPage = 1;
async function renderBranches() {
  const el = document.getElementById('page');
  try {
    // Need org list first
    const orgs = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    const orgList = orgs.results || orgs;
    if (orgList.length === 0) {
      el.innerHTML = `<div class="empty"><div class="empty-icon">🏢</div><div class="empty-title">ابتدا سازمان بسازید</div></div>`;
      return;
    }
    const firstOrg = orgList[0];
    const data = await apiGet(`/organizations/${firstOrg.id}/branches/`);
    branchesData = data.results || data;
    renderBranchesTable(orgList, firstOrg.id);
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderBranchesTable(orgList, selectedOrgId) {
  const el = document.getElementById('page');
  const pg = paginateLocal(branchesData, branchesPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>📍 شعب</h1></div>
      <button class="btn btn-primary" onclick="openCreateBranchModal('${selectedOrgId}')">➕ شعبه جدید</button>
    </div>
    <div class="card">
      <div class="toolbar">
        <select onchange="changeBranchOrg(this.value, ${JSON.stringify(orgList).replace(/"/g,'&quot;')})">
          ${orgList.map(o=>`<option value="${o.id}" ${o.id===selectedOrgId?'selected':''}>${o.name}</option>`).join('')}
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام</th><th>آدرس</th><th>شماره تماس</th><th>فعال</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(b=>`<tr>
              <td><strong>${b.name}</strong></td>
              <td>${b.address||'—'}</td>
              <td>${b.phone_number||'—'}</td>
              <td>${b.is_active?'<span class="badge badge-green">بله</span>':'<span class="badge badge-gray">خیر</span>'}</td>
              <td><button class="btn btn-ghost btn-sm" onclick='openEditBranchModal(${JSON.stringify(b)})'>✏️</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

async function changeBranchOrg(orgId, orgList) {
  const data = await apiGet(`/organizations/${orgId}/branches/`);
  branchesData = data.results || data;
  renderBranchesTable(orgList, orgId);
}

function openCreateBranchModal(orgId) {
  openModal('شعبه جدید', `
    <div class="form-group"><label class="form-label">نام *</label><input id="fb-name" class="form-control"></div>
    <div class="form-group"><label class="form-label">آدرس</label><textarea id="fb-addr" class="form-control" rows="2"></textarea></div>
    <div class="form-group"><label class="form-label">شماره تماس</label><input id="fb-phone" class="form-control"></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateBranch('${orgId}')">ذخیره</button>
  `);
}

async function submitCreateBranch(orgId) {
  const body = {
    name: document.getElementById('fb-name').value,
    address: document.getElementById('fb-addr').value,
    phone_number: document.getElementById('fb-phone').value,
  };
  try {
    await apiPost(`/organizations/${orgId}/branches/`, body);
    closeModal(); toast('شعبه ایجاد شد'); renderBranches();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditBranchModal(b) {
  openModal(`ویرایش: ${b.name}`, `
    <div class="form-group"><label class="form-label">نام</label><input id="eb-name" class="form-control" value="${b.name||''}"></div>
    <div class="form-group"><label class="form-label">آدرس</label><textarea id="eb-addr" class="form-control" rows="2">${b.address||''}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">شماره تماس</label><input id="eb-phone" class="form-control" value="${b.phone_number||''}"></div>
      <div class="form-group"><label class="form-label">فعال</label>
        <select id="eb-active" class="form-control">
          <option value="true" ${b.is_active?'selected':''}>بله</option>
          <option value="false" ${!b.is_active?'selected':''}>خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditBranch('${b.id}')">ذخیره</button>
  `);
}

async function submitEditBranch(id) {
  const body = {
    name: document.getElementById('eb-name').value,
    address: document.getElementById('eb-addr').value,
    phone_number: document.getElementById('eb-phone').value,
    is_active: document.getElementById('eb-active').value === 'true',
  };
  try {
    await apiPatch(`/organizations/branches/${id}/`, body);
    closeModal(); toast('شعبه بروزرسانی شد'); renderBranches();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   PROVIDERS
═══════════════════════════════════════════════════════ */
let providersData = []; let providersPage = 1;
async function renderProviders() {
  const el = document.getElementById('page');
  try {
    const orgs = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    const orgList = orgs.results || orgs;
    let url = (orgList.length && currentUser?.role !== 'super_admin') ? `/providers/organizations/${orgList[0].id}/` : '/providers/';
    const data = await apiGet(url);
    providersData = data.results || data;
    renderProvidersTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderProvidersTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(providersData, providersPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>👨‍⚕️ پزشکان</h1><div class="page-header-sub">${providersData.length} پزشک</div></div>
      <button class="btn btn-primary" onclick="openCreateProviderModal()">➕ پزشک جدید</button>
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>پزشک</th><th>سازمان</th><th>تخصص</th><th>مدت ویزیت (دقیقه)</th><th>فعال</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(p=>`<tr>
              <td><strong>${p.user?.first_name||''} ${p.user?.last_name||''}</strong><br><span class="td-muted">${p.user?.email||''}</span></td>
              <td>${p.organization?.name||''}</td>
              <td>${p.specialties?.map(s=>s.name||s).join(', ')||'—'}</td>
              <td>${p.default_slot_duration_minutes} دقیقه</td>
              <td>${p.is_active?'<span class="badge badge-green">فعال</span>':'<span class="badge badge-gray">غیرفعال</span>'}</td>
              <td><button class="btn btn-ghost btn-sm" onclick='openEditProviderModal(${JSON.stringify(p)})'>✏️</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{providersPage=p;renderProvidersTable()}')}
    </div>
  `;
}

function openCreateProviderModal() {
  openModal('پزشک جدید (ProviderProfile)', `
    <p style="color:var(--textMuted);font-size:0.83rem;margin-bottom:16px">برای ساخت پزشک نیاز به user_id و organization_id دارید.</p>
    <div class="form-group"><label class="form-label">User ID (uuid)</label><input id="fp-user" class="form-control" placeholder="uuid کاربر با نقش provider"></div>
    <div class="form-group"><label class="form-label">Organization ID (uuid)</label><input id="fp-org" class="form-control"></div>
    <div class="form-group"><label class="form-label">عنوان / تخصص</label><input id="fp-title" class="form-control" placeholder="مثلاً: متخصص قلب"></div>
    <div class="form-group"><label class="form-label">بیوگرافی</label><textarea id="fp-bio" class="form-control" rows="2"></textarea></div>
    <div class="form-group"><label class="form-label">مدت پیش‌فرض ویزیت (دقیقه)</label><input id="fp-dur" class="form-control" type="number" value="30"></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateProvider()">ذخیره</button>
  `);
}

async function submitCreateProvider() {
  const body = {
    user: document.getElementById('fp-user').value,
    organization: document.getElementById('fp-org').value,
    title: document.getElementById('fp-title').value,
    bio: document.getElementById('fp-bio').value,
    default_slot_duration_minutes: parseInt(document.getElementById('fp-dur').value)||30,
  };
  try {
    await apiPost('/providers/', body);
    closeModal(); toast('پزشک ایجاد شد'); renderProviders();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditProviderModal(p) {
  openModal(`ویرایش پزشک`, `
    <div class="form-group"><label class="form-label">عنوان</label><input id="ep-title" class="form-control" value="${p.title||''}"></div>
    <div class="form-group"><label class="form-label">بیوگرافی</label><textarea id="ep-bio" class="form-control" rows="2">${p.bio||''}</textarea></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">مدت ویزیت (دقیقه)</label><input id="ep-dur" class="form-control" type="number" value="${p.default_slot_duration_minutes||30}"></div>
      <div class="form-group"><label class="form-label">فعال</label>
        <select id="ep-active" class="form-control">
          <option value="true" ${p.is_active?'selected':''}>بله</option>
          <option value="false" ${!p.is_active?'selected':''}>خیر</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditProvider('${p.id}')">ذخیره</button>
  `);
}

async function submitEditProvider(id) {
  const body = {
    title: document.getElementById('ep-title').value,
    bio: document.getElementById('ep-bio').value,
    default_slot_duration_minutes: parseInt(document.getElementById('ep-dur').value)||30,
    is_active: document.getElementById('ep-active').value === 'true',
  };
  try {
    await apiPatch(`/providers/${id}/`, body);
    closeModal(); toast('پزشک بروزرسانی شد'); renderProviders();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   OFFERINGS
═══════════════════════════════════════════════════════ */
let offeringsData = []; let offeringsPage = 1;
async function renderOfferings() {
  const el = document.getElementById('page');
  try {
    const orgs = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    const orgList = orgs.results || orgs;
    let url = (orgList.length && currentUser?.role !== 'super_admin') ? `/offerings/organizations/${orgList[0].id}/` : '/offerings/';
    const data = await apiGet(url);
    offeringsData = data.results || data;
    renderOfferingsTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderOfferingsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(offeringsData, offeringsPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>📋 خدمات (Offerings)</h1><div class="page-header-sub">${offeringsData.length} خدمت</div></div>
      <button class="btn btn-primary" onclick="openCreateOfferingModal()">➕ خدمت جدید</button>
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>عنوان</th><th>پزشک</th><th>نوع ویزیت</th><th>مدت</th><th>قیمت</th><th>فعال</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(o=>`<tr>
              <td><strong>${o.title}</strong></td>
              <td>${o.provider?.user?.first_name||''} ${o.provider?.user?.last_name||''}</td>
              <td>${o.visit_mode==='in_person'?'<span class="badge badge-blue">حضوری</span>':'<span class="badge badge-purple">آنلاین</span>'}</td>
              <td>${o.duration_minutes} دقیقه</td>
              <td>${fmtMoney(o.price)}</td>
              <td>${o.is_active?'<span class="badge badge-green">بله</span>':'<span class="badge badge-gray">خیر</span>'}</td>
              <td><button class="btn btn-ghost btn-sm" onclick='openEditOfferingModal(${JSON.stringify(o)})'>✏️</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{offeringsPage=p;renderOfferingsTable()}')}
    </div>
  `;
}

function openCreateOfferingModal() {
  openModal('خدمت جدید', `
    <div class="form-group"><label class="form-label">عنوان *</label><input id="fof-title" class="form-control"></div>
    <div class="form-group"><label class="form-label">Provider Profile ID</label><input id="fof-prov" class="form-control" placeholder="uuid"></div>
    <div class="form-group"><label class="form-label">Organization ID</label><input id="fof-org" class="form-control" placeholder="uuid"></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">نوع ویزیت</label>
        <select id="fof-mode" class="form-control">
          <option value="in_person">حضوری</option>
          <option value="online">آنلاین</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">مدت (دقیقه)</label><input id="fof-dur" class="form-control" type="number" value="30"></div>
    </div>
    <div class="form-group"><label class="form-label">قیمت (تومان)</label><input id="fof-price" class="form-control" type="number" value="0"></div>
    <div class="form-group"><label class="form-label">نیاز به تأیید ادمین؟</label>
      <select id="fof-appr" class="form-control"><option value="false">خیر</option><option value="true">بله</option></select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateOffering()">ذخیره</button>
  `);
}

async function submitCreateOffering() {
  const body = {
    title: document.getElementById('fof-title').value,
    provider: document.getElementById('fof-prov').value,
    organization: document.getElementById('fof-org').value,
    visit_mode: document.getElementById('fof-mode').value,
    duration_minutes: parseInt(document.getElementById('fof-dur').value)||30,
    price: document.getElementById('fof-price').value,
    requires_approval: document.getElementById('fof-appr').value === 'true',
  };
  try {
    await apiPost('/offerings/', body);
    closeModal(); toast('خدمت ایجاد شد'); renderOfferings();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditOfferingModal(o) {
  openModal(`ویرایش: ${o.title}`, `
    <div class="form-group"><label class="form-label">عنوان</label><input id="eof-title" class="form-control" value="${o.title||''}"></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">مدت (دقیقه)</label><input id="eof-dur" class="form-control" type="number" value="${o.duration_minutes||30}"></div>
      <div class="form-group"><label class="form-label">قیمت</label><input id="eof-price" class="form-control" type="number" value="${o.price||0}"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">فعال</label>
        <select id="eof-active" class="form-control">
          <option value="true" ${o.is_active?'selected':''}>بله</option>
          <option value="false" ${!o.is_active?'selected':''}>خیر</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">نیاز به تأیید</label>
        <select id="eof-appr" class="form-control">
          <option value="false" ${!o.requires_approval?'selected':''}>خیر</option>
          <option value="true" ${o.requires_approval?'selected':''}>بله</option>
        </select>
      </div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditOffering('${o.id}')">ذخیره</button>
  `);
}

async function submitEditOffering(id) {
  const body = {
    title: document.getElementById('eof-title').value,
    duration_minutes: parseInt(document.getElementById('eof-dur').value)||30,
    price: document.getElementById('eof-price').value,
    is_active: document.getElementById('eof-active').value === 'true',
    requires_approval: document.getElementById('eof-appr').value === 'true',
  };
  try {
    await apiPatch(`/offerings/${id}/`, body);
    closeModal(); toast('خدمت بروزرسانی شد'); renderOfferings();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   CATEGORIES
═══════════════════════════════════════════════════════ */
let catsData = []; let catsPage = 1;
async function renderCategories() {
  const el = document.getElementById('page');
  try {
    const data = await apiGet('/categories/admin/');
    catsData = data.results || data;
    renderCatsTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderCatsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(catsData, catsPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>🏷️ تخصص‌ها</h1><div class="page-header-sub">${catsData.length} تخصص</div></div>
      ${currentUser?.role === 'super_admin' ? `<button class="btn btn-primary" onclick="openCreateCatModal()">➕ تخصص جدید</button>` : ''}
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>نام</th><th>Slug</th><th>توضیحات</th><th>فعال</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(c=>`<tr>
              <td><strong>${c.name}</strong></td>
              <td class="td-muted">${c.slug||''}</td>
              <td class="td-muted">${(c.description||'').substring(0,60)}${(c.description||'').length>60?'…':''}</td>
              <td>${c.is_active?'<span class="badge badge-green">فعال</span>':'<span class="badge badge-gray">غیرفعال</span>'}</td>
              <td><div class="row-actions">
                ${currentUser?.role === 'super_admin' ? `<button class="btn btn-ghost btn-sm" onclick='openEditCatModal(${JSON.stringify(c)})'>✏️</button>` : ''}
                ${currentUser?.role === 'super_admin' ? `<button class="btn btn-danger btn-sm" onclick="deleteCat('${c.id}','${c.name}')">🗑️</button>` : ''}
              </div></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{catsPage=p;renderCatsTable()}')}
    </div>
  `;
}

function openCreateCatModal() {
  openModal('تخصص جدید', `
    <div class="form-group"><label class="form-label">نام *</label><input id="fc-name" class="form-control"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="fc-desc" class="form-control" rows="2"></textarea></div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateCat()">ذخیره</button>
  `);
}

async function submitCreateCat() {
  const body = { name: document.getElementById('fc-name').value, description: document.getElementById('fc-desc').value };
  try {
    await apiPost('/categories/admin/', body);
    closeModal(); toast('تخصص ایجاد شد'); renderCategories();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

function openEditCatModal(c) {
  openModal(`ویرایش: ${c.name}`, `
    <div class="form-group"><label class="form-label">نام</label><input id="ec-name" class="form-control" value="${c.name||''}"></div>
    <div class="form-group"><label class="form-label">توضیحات</label><textarea id="ec-desc" class="form-control" rows="2">${c.description||''}</textarea></div>
    <div class="form-group"><label class="form-label">فعال</label>
      <select id="ec-active" class="form-control">
        <option value="true" ${c.is_active?'selected':''}>بله</option>
        <option value="false" ${!c.is_active?'selected':''}>خیر</option>
      </select>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitEditCat('${c.id}')">ذخیره</button>
  `);
}

async function submitEditCat(id) {
  const body = {
    name: document.getElementById('ec-name').value,
    description: document.getElementById('ec-desc').value,
    is_active: document.getElementById('ec-active').value === 'true',
  };
  try {
    await apiPatch(`/categories/admin/${id}/`, body);
    closeModal(); toast('تخصص بروزرسانی شد'); renderCategories();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

async function deleteCat(id, name) {
  if (!confirm(`آیا تخصص "${name}" حذف شود؟`)) return;
  try {
    await apiDelete(`/categories/admin/${id}/`);
    toast('تخصص غیرفعال شد'); renderCategories();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   HOLIDAYS
═══════════════════════════════════════════════════════ */
let holidaysData = []; let holidaysPage = 1;
async function renderHolidays() {
  const el = document.getElementById('page');
  try {
    const data = await apiGet('/availability/holidays/');
    holidaysData = data.results || data;
    renderHolidaysTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderHolidaysTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(holidaysData, holidaysPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>📅 تعطیلات سازمان</h1></div>
      <button class="btn btn-primary" onclick="openCreateHolidayModal()">➕ تعطیلی جدید</button>
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>عنوان</th><th>از</th><th>تا</th><th>سازمان</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(h=>`<tr>
              <td><strong>${h.title||h.name||'—'}</strong></td>
              <td class="td-muted">${fmtDate(h.start_date||h.date)}</td>
              <td class="td-muted">${fmtDate(h.end_date||h.date)}</td>
              <td>${h.organization?.name||''}</td>
              <td><button class="btn btn-danger btn-sm" onclick="deleteHoliday('${h.id}')">🗑️</button></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function openCreateHolidayModal() {
  openModal('تعطیلی جدید', `
    <div class="form-group"><label class="form-label">عنوان *</label><input id="fh-title" class="form-control" placeholder="مثلاً: عید نوروز"></div>
    <div class="form-group"><label class="form-label">Organization ID</label><input id="fh-org" class="form-control" placeholder="uuid"></div>
    <div class="form-row">
      <div class="form-group"><label class="form-label">از تاریخ</label><input id="fh-start" class="form-control" type="date"></div>
      <div class="form-group"><label class="form-label">تا تاریخ</label><input id="fh-end" class="form-control" type="date"></div>
    </div>
  `, `
    <button class="btn btn-ghost" onclick="closeModal()">انصراف</button>
    <button class="btn btn-primary" onclick="submitCreateHoliday()">ذخیره</button>
  `);
}

async function submitCreateHoliday() {
  const body = {
    title: document.getElementById('fh-title').value,
    organization: document.getElementById('fh-org').value,
    start_date: document.getElementById('fh-start').value,
    end_date: document.getElementById('fh-end').value,
  };
  try {
    await apiPost('/availability/holidays/', body);
    closeModal(); toast('تعطیلی ثبت شد'); renderHolidays();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

async function deleteHoliday(id) {
  if (!confirm('آیا این تعطیلی حذف شود؟')) return;
  try {
    await apiDelete(`/availability/holidays/${id}/`);
    toast('حذف شد'); renderHolidays();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   APPOINTMENTS
═══════════════════════════════════════════════════════ */
let apptsData = []; let apptsPage = 1; let apptsStatus = '';
async function renderAppointments() {
  const el = document.getElementById('page');
  try {
    const orgs = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    const orgList = orgs.results || orgs;
    let url = orgList.length ? `/appointments/organizations/${orgList[0].id}/` : '/appointments/';
    const data = await apiGet(url);
    apptsData = data.results || data;
    renderApptsTable(orgList, orgList[0]?.id);
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderApptsTable(orgList, selectedOrgId) {
  const el = document.getElementById('page');
  let filtered = apptsStatus ? apptsData.filter(a=>a.status===apptsStatus) : apptsData;
  const pg = paginateLocal(filtered, apptsPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>🗓️ نوبت‌ها</h1><div class="page-header-sub">${filtered.length} نوبت</div></div>
    </div>
    <div class="card">
      <div class="toolbar">
        ${orgList ? `<select onchange="changeApptOrg(this.value, ${JSON.stringify(orgList).replace(/"/g,'&quot;')})">
          ${orgList.map(o=>`<option value="${o.id}" ${o.id===selectedOrgId?'selected':''}>${o.name}</option>`).join('')}
        </select>` : ''}
        <select id="appt-status-filter" onchange="apptsStatus=this.value;apptsPage=1;renderApptsTable(${JSON.stringify(orgList||[]).replace(/"/g,'&quot;')},'${selectedOrgId}')">
          <option value="">همه وضعیت‌ها</option>
          <option value="pending" ${apptsStatus==='pending'?'selected':''}>در انتظار</option>
          <option value="confirmed" ${apptsStatus==='confirmed'?'selected':''}>تأیید شده</option>
          <option value="completed" ${apptsStatus==='completed'?'selected':''}>انجام شده</option>
          <option value="cancelled_by_customer">لغو توسط بیمار</option>
          <option value="cancelled_by_provider">لغو توسط پزشک</option>
          <option value="no_show">غیبت</option>
        </select>
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>بیمار</th><th>پزشک</th><th>زمان شروع</th><th>وضعیت</th><th>قیمت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(a=>`<tr>
              <td>${a.customer?.email||a.customer||''}</td>
              <td>${a.provider?.user?.first_name||''} ${a.provider?.user?.last_name||''}</td>
              <td class="td-muted">${fmtDate(a.start_at)}</td>
              <td>${statusBadge(a.status, APPT_STATUS_MAP)}</td>
              <td>${fmtMoney(a.price)}</td>
              <td><div class="row-actions">
                ${a.status==='pending'?`<button class="btn btn-ghost btn-sm" onclick="updateApptStatus('${a.id}','confirmed')">✅ تأیید</button>`:''}
                ${['pending','confirmed'].includes(a.status)?`<button class="btn btn-danger btn-sm" onclick="cancelAppt('${a.id}')">❌ لغو</button>`:''}
                ${a.status==='confirmed'?`<button class="btn btn-ghost btn-sm" onclick="updateApptStatus('${a.id}','completed')">🏁 تکمیل</button>`:''}
              </div></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, `p=>{apptsPage=p;renderApptsTable(${JSON.stringify(orgList||[]).replace(/"/g,'&quot;')},'${selectedOrgId}')}`)}
    </div>
  `;
}

async function changeApptOrg(orgId, orgList) {
  const data = await apiGet(`/appointments/organizations/${orgId}/`);
  apptsData = data.results || data;
  renderApptsTable(orgList, orgId);
}

async function updateApptStatus(id, newStatus) {
  try {
    await apiPatch(`/appointments/${id}/status/`, { status: newStatus });
    toast('وضعیت نوبت تغییر کرد');
    renderAppointments();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

async function cancelAppt(id) {
  if (!confirm('آیا این نوبت لغو شود؟')) return;
  try {
    await apiPost(`/appointments/${id}/cancel/`, {});
    toast('نوبت لغو شد'); renderAppointments();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   PAYMENTS
═══════════════════════════════════════════════════════ */
let paymentsData = []; let paymentsPage = 1;
async function renderPayments() {
  const el = document.getElementById('page');
  try {
    const orgs = await apiGet(currentUser?.role === 'super_admin' ? '/organizations/' : '/organizations/my/');
    const orgList = orgs.results || orgs;
    let url = orgList.length ? `/payments/organizations/${orgList[0].id}/` : '/payments/my/';
    const data = await apiGet(url);
    paymentsData = data.results || data;
    renderPaymentsTable(orgList, orgList[0]?.id);
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderPaymentsTable(orgList, selectedOrgId) {
  const el = document.getElementById('page');
  const pg = paginateLocal(paymentsData, paymentsPage);
  el.innerHTML = `
    <div class="page-header">
      <div><h1>💳 پرداخت‌ها</h1><div class="page-header-sub">${paymentsData.length} پرداخت</div></div>
    </div>
    <div class="card">
      <div class="toolbar">
        ${orgList ? `<select onchange="changePaymentsOrg(this.value, ${JSON.stringify(orgList).replace(/"/g,'&quot;')})">
          ${orgList.map(o=>`<option value="${o.id}" ${o.id===selectedOrgId?'selected':''}>${o.name}</option>`).join('')}
        </select>` : ''}
      </div>
      <div class="table-wrapper">
        <table>
          <thead><tr><th>شناسه</th><th>مبلغ</th><th>روش</th><th>وضعیت</th><th>تاریخ پرداخت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${pg.items.map(p=>`<tr>
              <td class="td-muted" style="font-size:0.75rem">${p.id?.substring(0,8)}…</td>
              <td><strong>${fmtMoney(p.amount)}</strong></td>
              <td>${p.method==='online'?'<span class="badge badge-blue">آنلاین</span>':'<span class="badge badge-amber">نقدی</span>'}</td>
              <td>${statusBadge(p.status, PAYMENT_STATUS_MAP)}</td>
              <td class="td-muted">${fmtDate(p.paid_at)}</td>
              <td><div class="row-actions">
                ${p.status==='paid'?`<button class="btn btn-danger btn-sm" onclick="refundPayment('${p.id}')">↩️ بازپرداخت</button>`:''}
                ${p.status==='pending' && p.method==='in_person'?`<button class="btn btn-ghost btn-sm" onclick="markPaid('${p.id}')">✅ نقدی پرداخت شد</button>`:''}
              </div></td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, `p=>{paymentsPage=p;renderPaymentsTable(${JSON.stringify(orgList||[]).replace(/"/g,'&quot;')},'${selectedOrgId}')}`)}
    </div>
  `;
}

async function changePaymentsOrg(orgId, orgList) {
  const data = await apiGet(`/payments/organizations/${orgId}/`);
  paymentsData = data.results || data;
  renderPaymentsTable(orgList, orgId);
}

async function refundPayment(id) {
  if (!confirm('آیا این پرداخت بازپرداخت شود؟')) return;
  try {
    await apiPost(`/payments/${id}/refund/`, {});
    toast('بازپرداخت انجام شد'); renderPayments();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

async function markPaid(id) {
  try {
    await apiPost(`/payments/${id}/mark-paid/`, {});
    toast('پرداخت نقدی ثبت شد'); renderPayments();
  } catch(e) { toast(JSON.stringify(e), 'error'); }
}

/* ═══════════════════════════════════════════════════════
   NOTIFICATION DELIVERIES
═══════════════════════════════════════════════════════ */
let notifsData = []; let notifsPage = 1;
async function renderNotifications() {
  const el = document.getElementById('page');
  try {
    const data = await apiGet('/admin/notification-deliveries/');
    notifsData = data.results || data;
    renderNotifsTable();
  } catch(e) { el.innerHTML = errorHTML(e); }
}

function renderNotifsTable() {
  const el = document.getElementById('page');
  const pg = paginateLocal(notifsData, notifsPage);
  const NOTIF_STATUS_MAP = {
    sent:    { label: 'ارسال شد',   cls: 'badge-green' },
    failed:  { label: 'ناموفق',     cls: 'badge-rose'  },
    pending: { label: 'در صف',      cls: 'badge-amber' },
  };
  el.innerHTML = `
    <div class="page-header">
      <div><h1>🔔 لاگ نوتیفیکیشن</h1><div class="page-header-sub">${notifsData.length} رکورد</div></div>
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>کانال</th><th>گیرنده</th><th>موضوع</th><th>نوع</th><th>وضعیت</th><th>ارسال شده در</th><th>خطا</th></tr></thead>
          <tbody>
            ${pg.items.map(n=>`<tr>
              <td>${n.channel==='email'?'📧 ایمیل':n.channel==='push'?'📱 پوش':'📟 '+n.channel}</td>
              <td class="td-muted">${n.recipient||'—'}</td>
              <td>${n.subject||'—'}</td>
              <td class="td-muted" style="font-size:0.75rem">${n.type||''}</td>
              <td>${statusBadge(n.status, NOTIF_STATUS_MAP)}</td>
              <td class="td-muted">${fmtDate(n.sent_at)}</td>
              <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.75rem;color:var(--rose)">${n.error_message||''}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
      ${renderPagination(pg, 'p=>{notifsPage=p;renderNotifsTable()}')}
    </div>
  `;
}

/* ═══════════════════════════════════════════════════════
   UTILITY
═══════════════════════════════════════════════════════ */
function errorHTML(e) {
  return `<div class="empty"><div class="empty-icon">⚠️</div><div class="empty-title">خطا در بارگذاری</div><div class="empty-sub">${JSON.stringify(e)}</div></div>`;
}
const API_URL = '';
let currentUser = null;
let token = localStorage.getItem('token');
let allUsers = [];
let allOrgs = [];
let allPlans = [];
let allSubs = [];

// ── DOM Elements ──────────────────────────────────────────
const logoutBtn = document.getElementById('logout-btn');
const currentUserNameSpan = document.getElementById('current-user-name');

// Nav items
const navLinks = {
    users:   document.getElementById('nav-users'),
    orgs:    document.getElementById('nav-orgs'),
    plans:   document.getElementById('nav-plans'),
    subs:    document.getElementById('nav-subs'),
    members: document.getElementById('nav-members'),
    usage:   document.getElementById('nav-usage'),
    search:  document.getElementById('nav-search'),
};

// Sections
const sections = {
    users:   document.getElementById('section-users'),
    orgs:    document.getElementById('section-orgs'),
    plans:   document.getElementById('section-plans'),
    subs:    document.getElementById('section-subs'),
    members: document.getElementById('section-members'),
    usage:   document.getElementById('section-usage'),
    search:  document.getElementById('section-search'),
};

// ── Nav Switching ─────────────────────────────────────────
Object.keys(navLinks).forEach(key => {
    navLinks[key].addEventListener('click', (e) => {
        e.preventDefault();
        switchSection(key);
    });
});

function switchSection(key) {
    Object.values(navLinks).forEach(a => a.classList.remove('active'));
    Object.values(sections).forEach(s => s.classList.remove('active'));
    navLinks[key].classList.add('active');
    sections[key].classList.add('active');

    // Fetch data when switching
    if (key === 'users')   fetchUsers();
    else if (key === 'orgs')    fetchOrganizations();
    else if (key === 'plans')   fetchPlans();
    else if (key === 'subs')    fetchSubscriptions();
    else if (key === 'members') fetchOrgMembers();
    else if (key === 'usage')   fetchUsage();
}

// ── Close buttons for all modals ──────────────────────────
document.querySelectorAll('.close').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-modal');
        document.getElementById(modalId).style.display = 'none';
    });
});
window.addEventListener('click', (e) => {
    document.querySelectorAll('.modal').forEach(m => {
        if (e.target === m) m.style.display = 'none';
    });
});

// ── Init ──────────────────────────────────────────────────
logoutBtn.addEventListener('click', logout);
document.addEventListener('DOMContentLoaded', init);

async function init() {
    if (!token) { window.location.href = '/login'; return; }
    try {
        await fetchCurrentUser();
        await fetchUsers();
    } catch (error) {
        console.error('Init error:', error);
        if (error.status === 401) logout();
    }
}

async function fetchCurrentUser() {
    const res = await fetch(`${API_URL}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    currentUser = await res.json();
    currentUserNameSpan.textContent = currentUser.full_name || currentUser.email;

    if (currentUser.role !== 'admin' && currentUser.role !== 'super_admin') {
        alert('Access denied. Admin privileges required for the global dashboard.');
        logout();
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// ── Global Search (name or email) ────────────────────────
const searchQueryInput = document.getElementById('search-email-input');
const searchBtn = document.getElementById('search-btn');
searchBtn.addEventListener('click', () => doSearch());
searchQueryInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

async function doSearch() {
    const query = searchQueryInput.value.trim();
    if (!query) return;
    try {
        const res = await fetch(`${API_URL}/admin/search?query=${encodeURIComponent(query)}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Search failed');
        const data = await res.json();
        renderSearchResults(data);
        navLinks.search.style.display = 'block';
        requestAnimationFrame(() => switchSection('search'));
    } catch (err) { alert(err.message); }
}

function renderSearchResults(data) {
    document.getElementById('search-query-label').textContent = `— "${data.query}"`;
    const container = document.getElementById('search-results-container');

    const tables = [
        {
            title: 'Users',
            rows: data.users,
            cols: ['id', 'full_name', 'email', 'role', 'is_active', 'email_verified'],
            labels: ['ID', 'Name', 'Email', 'Role', 'Active', 'Verified'],
            format: { is_active: v => v ? 'Yes' : 'No', email_verified: v => v ? 'Yes' : 'No', role: v => `<span class="badge badge-${v}">${v}</span>` }
        },
        {
            title: 'Organizations',
            rows: data.organizations,
            cols: ['id', 'name', 'slug', 'type', 'created_at'],
            labels: ['ID', 'Name', 'Slug', 'Type', 'Created'],
            format: { type: v => `<span class="badge badge-${v}">${v}</span>`, created_at: v => v ? new Date(v).toLocaleDateString() : '-' }
        },
        {
            title: 'Memberships',
            rows: data.memberships,
            cols: ['id', 'org_name', 'user_email', 'role', 'joined_at'],
            labels: ['ID', 'Organization', 'Email', 'Role', 'Joined'],
            format: { role: v => `<span class="badge badge-${v}">${v}</span>`, joined_at: v => v ? new Date(v).toLocaleDateString() : '-' }
        },
        {
            title: 'Subscriptions',
            rows: data.subscriptions,
            cols: ['id', 'org_name', 'plan_name', 'type', 'current_period_start', 'current_period_end', 'cancel_at_period_end'],
            labels: ['ID', 'Org', 'Plan', 'Billing', 'Start', 'End', 'Cancel?'],
            format: { type: v => `<span class="badge badge-${v}">${v}</span>`, cancel_at_period_end: v => v ? 'Yes' : 'No' }
        },
        {
            title: 'Usage Records',
            rows: data.usages,
            cols: ['id', 'org_name', 'sub_description', 'minutes_used', 'created_at'],
            labels: ['ID', 'Org', 'Subscription', 'Minutes Used', 'Created'],
            format: { created_at: v => v ? new Date(v).toLocaleDateString() : '-' }
        },
    ];

    let html = '';
    tables.forEach(t => {
        html += `<div class="search-group">
            <h3 class="search-group-title">${t.title} <span class="count-badge">${t.rows.length}</span></h3>`;
        if (t.rows.length === 0) {
            html += `<p class="empty-state">No matching ${t.title.toLowerCase()} found.</p>`;
        } else {
            html += `<div class="table-container"><table>
                <thead><tr>${t.labels.map(l => `<th>${l}</th>`).join('')}</tr></thead>
                <tbody>${t.rows.map(row =>
                    `<tr>${t.cols.map(col => {
                        const val = row[col] ?? '-';
                        const formatted = (t.format && t.format[col]) ? t.format[col](val) : val;
                        return `<td>${formatted}</td>`;
                    }).join('')}</tr>`
                ).join('')}</tbody>
            </table></div>`;
        }
        html += '</div>';
    });
    container.innerHTML = html;
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  USERS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const usersTableBody = document.querySelector('#users-table tbody');
const userModal = document.getElementById('user-modal');
const userForm = document.getElementById('user-form');
document.getElementById('add-user-btn').addEventListener('click', () => openUserModal());
userForm.addEventListener('submit', handleUserSubmit);

// Live filter — matches name OR email
document.getElementById('filter-users').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderUsers(allUsers.filter(u =>
        (u.email || '').toLowerCase().includes(q) ||
        (u.full_name || '').toLowerCase().includes(q)
    ));
});

async function fetchUsers() {
    const res = await fetch(`${API_URL}/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allUsers = await res.json();
    renderUsers(allUsers);
}

function renderUsers(users) {
    usersTableBody.innerHTML = '';
    if (users.length === 0) {
        usersTableBody.innerHTML = '<tr><td colspan="7" class="empty-cell">No users found.</td></tr>';
        return;
    }
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.full_name || '-'}</td>
            <td class="cell-wrap">${user.email}</td>
            <td><span class="badge badge-${user.role}">${user.role}</span></td>
            <td>${user.is_active ? '<span class="badge badge-active">Active</span>' : '<span class="badge badge-inactive">Inactive</span>'}</td>
            <td>${user.email_verified ? 'Yes' : 'No'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editUser(${user.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteUser(${user.id})">Delete</button>` : ''}
            </td>`;
        usersTableBody.appendChild(tr);
    });
}

async function handleUserSubmit(e) {
    e.preventDefault();
    const userId = document.getElementById('user-id').value;
    const formData = {
        full_name: document.getElementById('full-name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        dob: document.getElementById('dob').value || null,
        role: document.getElementById('role').value,
        is_active: document.getElementById('is-active').checked,
        email_verified: document.getElementById('email-verified').checked,
    };
    const pw = document.getElementById('password').value;
    if (pw) formData.password = pw;

    try {
        let res;
        if (userId) {
            res = await fetch(`${API_URL}/admin/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            if (!pw) { alert('Password is required for new users'); return; }
            res = await fetch(`${API_URL}/admin/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        userModal.style.display = 'none';
        fetchUsers();
    } catch (err) { alert(err.message); }
}

function openUserModal(user = null) {
    userModal.style.display = 'block';
    if (user) {
        document.getElementById('modal-title').textContent = 'Edit User';
        document.getElementById('user-id').value = user.id;
        document.getElementById('full-name').value = user.full_name || '';
        document.getElementById('email').value = user.email;
        document.getElementById('phone').value = user.phone || '';
        document.getElementById('dob').value = user.dob || '';
        document.getElementById('role').value = user.role;
        document.getElementById('is-active').checked = user.is_active;
        document.getElementById('email-verified').checked = user.email_verified || false;
        document.getElementById('password-hint').style.display = 'block';
        document.getElementById('password').required = false;
    } else {
        document.getElementById('modal-title').textContent = 'Add User';
        userForm.reset();
        document.getElementById('user-id').value = '';
        document.getElementById('email-verified').checked = false;
        document.getElementById('password-hint').style.display = 'none';
        document.getElementById('password').required = true;
    }
}

window.editUser = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/users/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch user');
        openUserModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deleteUser = async (id) => {
    if (!confirm('Delete this user? This will also delete their organization.')) return;
    try {
        const res = await fetch(`${API_URL}/admin/users/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete user');
        fetchUsers();
    } catch (err) { alert(err.message); }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ORGANIZATIONS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const orgsTableBody = document.querySelector('#orgs-table tbody');
const orgModal = document.getElementById('org-modal');
const orgForm = document.getElementById('org-form');
document.getElementById('add-org-btn').addEventListener('click', () => openOrgModal());
orgForm.addEventListener('submit', handleOrgSubmit);

document.getElementById('filter-orgs').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderOrganizations(allOrgs.filter(o => o.name.toLowerCase().includes(q)));
});

async function fetchOrganizations() {
    const res = await fetch(`${API_URL}/admin/organizations`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allOrgs = await res.json();
    renderOrganizations(allOrgs);
}

function renderOrganizations(orgs) {
    orgsTableBody.innerHTML = '';
    if (orgs.length === 0) {
        orgsTableBody.innerHTML = '<tr><td colspan="7" class="empty-cell">No organizations found.</td></tr>';
        return;
    }
    orgs.forEach(org => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${org.id}</td>
            <td>${org.name}</td>
            <td><code>${org.slug}</code></td>
            <td>${org.owner_name || '-'}</td>
            <td><span class="badge badge-${org.type}">${org.type}</span></td>
            <td>${new Date(org.created_at).toLocaleDateString()}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editOrg(${org.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteOrg(${org.id})">Delete</button>` : ''}
            </td>`;
        orgsTableBody.appendChild(tr);
    });
}

async function handleOrgSubmit(e) {
    e.preventDefault();
    const orgId = document.getElementById('org-id').value;
    try {
        let res;
        if (orgId) {
            const formData = {
                name: document.getElementById('org-name').value,
                type: document.getElementById('org-type').value,
            };
            res = await fetch(`${API_URL}/admin/organizations/${orgId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            const formData = {
                name: document.getElementById('org-name').value,
                type: document.getElementById('org-type').value,
                owner_id: parseInt(document.getElementById('org-owner').value),
            };
            res = await fetch(`${API_URL}/admin/organizations`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        orgModal.style.display = 'none';
        fetchOrganizations();
    } catch (err) { alert(err.message); }
}

async function openOrgModal(org = null) {
    if (allUsers.length === 0) await fetchUsers();
    const ownerSelect = document.getElementById('org-owner');
    ownerSelect.innerHTML = allUsers.map(u => `<option value="${u.id}">${u.full_name || u.email} (${u.email})</option>`).join('');

    orgModal.style.display = 'block';
    if (org) {
        document.getElementById('org-modal-title').textContent = 'Edit Organization';
        document.getElementById('org-id').value = org.id;
        document.getElementById('org-name').value = org.name;
        document.getElementById('org-type').value = org.type;
        document.getElementById('org-owner-group').style.display = 'none';
    } else {
        document.getElementById('org-modal-title').textContent = 'Add Organization';
        orgForm.reset();
        document.getElementById('org-id').value = '';
        document.getElementById('org-owner-group').style.display = 'block';
    }
}

window.editOrg = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/organizations/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch organization');
        openOrgModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deleteOrg = async (id) => {
    if (!confirm('Delete this organization and all its members?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/organizations/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete organization');
        fetchOrganizations();
    } catch (err) { alert(err.message); }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  PLANS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const plansTableBody = document.querySelector('#plans-table tbody');
const planModal = document.getElementById('plan-modal');
const planForm = document.getElementById('plan-form');
document.getElementById('add-plan-btn').addEventListener('click', () => openPlanModal());
planForm.addEventListener('submit', handlePlanSubmit);

async function fetchPlans() {
    const res = await fetch(`${API_URL}/admin/plans`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allPlans = await res.json();
    renderPlans(allPlans);
}

function renderPlans(plans) {
    plansTableBody.innerHTML = '';
    if (plans.length === 0) {
        plansTableBody.innerHTML = '<tr><td colspan="7" class="empty-cell">No plans found.</td></tr>';
        return;
    }
    plans.forEach(plan => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${plan.id}</td>
            <td>${plan.name}</td>
            <td>$${Number(plan.price_month).toFixed(2)}</td>
            <td>$${Number(plan.price_year).toFixed(2)}</td>
            <td>${plan.token_quota.toLocaleString()}</td>
            <td>${plan.max_users}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editPlan(${plan.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deletePlan(${plan.id})">Delete</button>` : ''}
            </td>`;
        plansTableBody.appendChild(tr);
    });
}

async function handlePlanSubmit(e) {
    e.preventDefault();
    const planId = document.getElementById('plan-id').value;
    const formData = {
        name: document.getElementById('plan-name').value,
        price_month: parseFloat(document.getElementById('plan-price-month').value),
        price_year: parseFloat(document.getElementById('plan-price-year').value),
        token_quota: parseInt(document.getElementById('plan-token-quota').value),
        max_users: parseInt(document.getElementById('plan-max-users').value),
    };
    try {
        let res;
        if (planId) {
            res = await fetch(`${API_URL}/admin/plans/${planId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            res = await fetch(`${API_URL}/admin/plans`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        planModal.style.display = 'none';
        fetchPlans();
    } catch (err) { alert(err.message); }
}

function openPlanModal(plan = null) {
    planModal.style.display = 'block';
    if (plan) {
        document.getElementById('plan-modal-title').textContent = 'Edit Plan';
        document.getElementById('plan-id').value = plan.id;
        document.getElementById('plan-name').value = plan.name;
        document.getElementById('plan-price-month').value = plan.price_month;
        document.getElementById('plan-price-year').value = plan.price_year;
        document.getElementById('plan-token-quota').value = plan.token_quota;
        document.getElementById('plan-max-users').value = plan.max_users;
    } else {
        document.getElementById('plan-modal-title').textContent = 'Add Plan';
        planForm.reset();
        document.getElementById('plan-id').value = '';
    }
}

window.editPlan = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/plans/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch plan');
        openPlanModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deletePlan = async (id) => {
    if (!confirm('Delete this plan?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/plans/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete plan');
        fetchPlans();
    } catch (err) { alert(err.message); }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SUBSCRIPTIONS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const subsTableBody = document.querySelector('#subs-table tbody');
const subModal = document.getElementById('sub-modal');
const subForm = document.getElementById('sub-form');
document.getElementById('add-sub-btn').addEventListener('click', () => openSubModal());
subForm.addEventListener('submit', handleSubSubmit);

async function fetchSubscriptions() {
    const res = await fetch(`${API_URL}/admin/subscriptions`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allSubs = await res.json();
    renderSubscriptions(allSubs);
}

function renderSubscriptions(subs) {
    subsTableBody.innerHTML = '';
    if (subs.length === 0) {
        subsTableBody.innerHTML = '<tr><td colspan="8" class="empty-cell">No subscriptions found.</td></tr>';
        return;
    }
    subs.forEach(sub => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${sub.id}</td>
            <td>${sub.org_name || sub.org_id}</td>
            <td>${sub.plan_name || sub.plan_id}</td>
            <td><span class="badge badge-${sub.type}">${sub.type}</span></td>
            <td>${sub.current_period_start || '-'}</td>
            <td>${sub.current_period_end || '-'}</td>
            <td>${sub.cancel_at_period_end ? 'Yes' : 'No'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editSub(${sub.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteSub(${sub.id})">Delete</button>` : ''}
            </td>`;
        subsTableBody.appendChild(tr);
    });
}

async function handleSubSubmit(e) {
    e.preventDefault();
    const subId = document.getElementById('sub-id').value;
    try {
        let res;
        if (subId) {
            const formData = {
                plan_id: parseInt(document.getElementById('sub-plan').value),
                type: document.getElementById('sub-type').value,
                cancel_at_period_end: document.getElementById('sub-cancel').checked,
            };
            res = await fetch(`${API_URL}/admin/subscriptions/${subId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            const formData = {
                org_id: parseInt(document.getElementById('sub-org').value),
                plan_id: parseInt(document.getElementById('sub-plan').value),
                type: document.getElementById('sub-type').value,
            };
            res = await fetch(`${API_URL}/admin/subscriptions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        subModal.style.display = 'none';
        fetchSubscriptions();
    } catch (err) { alert(err.message); }
}

async function openSubModal(sub = null) {
    if (allOrgs.length === 0) {
        const res = await fetch(`${API_URL}/admin/organizations`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) allOrgs = await res.json();
    }
    if (allPlans.length === 0) {
        const res = await fetch(`${API_URL}/admin/plans`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) allPlans = await res.json();
    }
    document.getElementById('sub-org').innerHTML = allOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    document.getElementById('sub-plan').innerHTML = allPlans.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

    subModal.style.display = 'block';
    if (sub) {
        document.getElementById('sub-modal-title').textContent = 'Edit Subscription';
        document.getElementById('sub-id').value = sub.id;
        document.getElementById('sub-org').value = sub.org_id;
        document.getElementById('sub-plan').value = sub.plan_id;
        document.getElementById('sub-type').value = sub.type;
        document.getElementById('sub-cancel').checked = sub.cancel_at_period_end;
        document.getElementById('sub-org-group').style.display = 'none';
        document.getElementById('sub-cancel-group').style.display = 'block';
    } else {
        document.getElementById('sub-modal-title').textContent = 'Add Subscription';
        subForm.reset();
        document.getElementById('sub-id').value = '';
        document.getElementById('sub-org-group').style.display = 'block';
        document.getElementById('sub-cancel-group').style.display = 'none';
    }
}

window.editSub = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/subscriptions/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch subscription');
        openSubModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deleteSub = async (id) => {
    if (!confirm('Delete this subscription?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/subscriptions/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete subscription');
        fetchSubscriptions();
    } catch (err) { alert(err.message); }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  ORG MEMBERS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let allMembers = [];
const membersTableBody = document.querySelector('#members-table tbody');
const memberModal = document.getElementById('member-modal');
const memberForm = document.getElementById('member-form');
document.getElementById('add-member-btn').addEventListener('click', () => openMemberModal());
memberForm.addEventListener('submit', handleMemberSubmit);

document.getElementById('filter-members').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderOrgMembers(allMembers.filter(m =>
        (m.user_email || '').toLowerCase().includes(q) ||
        (m.org_name || '').toLowerCase().includes(q)
    ));
});

async function fetchOrgMembers() {
    const res = await fetch(`${API_URL}/admin/org-members`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allMembers = await res.json();
    renderOrgMembers(allMembers);
}

function renderOrgMembers(members) {
    membersTableBody.innerHTML = '';
    if (members.length === 0) {
        membersTableBody.innerHTML = '<tr><td colspan="7" class="empty-cell">No members found.</td></tr>';
        return;
    }
    members.forEach(m => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${m.id}</td>
            <td>${m.org_name || m.org_id}</td>
            <td>${m.user_name || '-'}</td>
            <td class="cell-wrap">${m.user_email || '-'}</td>
            <td><span class="badge badge-${m.role}">${m.role}</span></td>
            <td>${m.joined_at ? new Date(m.joined_at).toLocaleDateString() : '-'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editMember(${m.id})">Edit Role</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteMember(${m.id})">Remove</button>` : ''}
            </td>`;
        membersTableBody.appendChild(tr);
    });
}

async function handleMemberSubmit(e) {
    e.preventDefault();
    const memberId = document.getElementById('member-id').value;
    try {
        let res;
        if (memberId) {
            const formData = { role: document.getElementById('member-role').value };
            res = await fetch(`${API_URL}/admin/org-members/${memberId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            const formData = {
                org_id: parseInt(document.getElementById('member-org').value),
                user_id: parseInt(document.getElementById('member-user').value),
                role: document.getElementById('member-role').value,
            };
            res = await fetch(`${API_URL}/admin/org-members`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        memberModal.style.display = 'none';
        fetchOrgMembers();
    } catch (err) { alert(err.message); }
}

async function openMemberModal(member = null) {
    if (allOrgs.length === 0) {
        const res = await fetch(`${API_URL}/admin/organizations`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) allOrgs = await res.json();
    }
    if (allUsers.length === 0) await fetchUsers();

    document.getElementById('member-org').innerHTML = allOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    document.getElementById('member-user').innerHTML = allUsers.map(u => `<option value="${u.id}">${u.full_name || u.email} (${u.email})</option>`).join('');

    memberModal.style.display = 'block';
    if (member) {
        document.getElementById('member-modal-title').textContent = 'Edit Member Role';
        document.getElementById('member-id').value = member.id;
        document.getElementById('member-role').value = member.role;
        document.getElementById('member-org-group').style.display = 'none';
        document.getElementById('member-user-group').style.display = 'none';
    } else {
        document.getElementById('member-modal-title').textContent = 'Add Org Member';
        memberForm.reset();
        document.getElementById('member-id').value = '';
        document.getElementById('member-org-group').style.display = 'block';
        document.getElementById('member-user-group').style.display = 'block';
    }
}

window.editMember = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/org-members/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch member');
        openMemberModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deleteMember = async (id) => {
    if (!confirm('Remove this member from the organization?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/org-members/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to remove member');
        fetchOrgMembers();
    } catch (err) { alert(err.message); }
};

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  SUBSCRIPTION USAGE CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

let allUsage = [];
const usageTableBody = document.querySelector('#usage-table tbody');
const usageModal = document.getElementById('usage-modal');
const usageForm = document.getElementById('usage-form');
document.getElementById('add-usage-btn').addEventListener('click', () => openUsageModal());
usageForm.addEventListener('submit', handleUsageSubmit);

document.getElementById('filter-usage').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    renderUsage(allUsage.filter(u => (u.org_name || '').toLowerCase().includes(q)));
});

async function fetchUsage() {
    const res = await fetch(`${API_URL}/admin/subscription-usage`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    allUsage = await res.json();
    renderUsage(allUsage);
}

function renderUsage(usages) {
    usageTableBody.innerHTML = '';
    if (usages.length === 0) {
        usageTableBody.innerHTML = '<tr><td colspan="7" class="empty-cell">No usage records found.</td></tr>';
        return;
    }
    usages.forEach(u => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${u.id}</td>
            <td>${u.org_name || u.org_id}</td>
            <td>${u.sub_description || u.subscription_id}</td>
            <td><strong>${Number(u.minutes_used).toFixed(2)}</strong> min</td>
            <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
            <td>${u.updated_at ? new Date(u.updated_at).toLocaleDateString() : '-'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editUsage(${u.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteUsage(${u.id})">Delete</button>` : ''}
            </td>`;
        usageTableBody.appendChild(tr);
    });
}

async function handleUsageSubmit(e) {
    e.preventDefault();
    const usageId = document.getElementById('usage-id').value;
    try {
        let res;
        if (usageId) {
            const formData = { minutes_used: parseFloat(document.getElementById('usage-minutes').value) };
            res = await fetch(`${API_URL}/admin/subscription-usage/${usageId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        } else {
            const formData = {
                org_id: parseInt(document.getElementById('usage-org').value),
                subscription_id: parseInt(document.getElementById('usage-sub').value),
                minutes_used: parseFloat(document.getElementById('usage-minutes').value),
            };
            res = await fetch(`${API_URL}/admin/subscription-usage`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(formData),
            });
        }
        if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed'); }
        usageModal.style.display = 'none';
        fetchUsage();
    } catch (err) { alert(err.message); }
}

async function openUsageModal(usage = null) {
    if (allOrgs.length === 0) {
        const res = await fetch(`${API_URL}/admin/organizations`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) allOrgs = await res.json();
    }
    if (allSubs.length === 0) {
        const res = await fetch(`${API_URL}/admin/subscriptions`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) allSubs = await res.json();
    }
    document.getElementById('usage-org').innerHTML = allOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');
    document.getElementById('usage-sub').innerHTML = allSubs.map(s => `<option value="${s.id}">${s.org_name || s.org_id} — ${s.plan_name || s.plan_id} (${s.type})</option>`).join('');

    usageModal.style.display = 'block';
    if (usage) {
        document.getElementById('usage-modal-title').textContent = 'Edit Usage Record';
        document.getElementById('usage-id').value = usage.id;
        document.getElementById('usage-minutes').value = usage.minutes_used;
        document.getElementById('usage-org-group').style.display = 'none';
        document.getElementById('usage-sub-group').style.display = 'none';
    } else {
        document.getElementById('usage-modal-title').textContent = 'Add Usage Record';
        usageForm.reset();
        document.getElementById('usage-id').value = '';
        document.getElementById('usage-org-group').style.display = 'block';
        document.getElementById('usage-sub-group').style.display = 'block';
    }
}

window.editUsage = async (id) => {
    try {
        const res = await fetch(`${API_URL}/admin/subscription-usage/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to fetch usage record');
        openUsageModal(await res.json());
    } catch (err) { alert(err.message); }
};

window.deleteUsage = async (id) => {
    if (!confirm('Delete this usage record?')) return;
    try {
        const res = await fetch(`${API_URL}/admin/subscription-usage/${id}`, {
            method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Failed to delete usage record');
        fetchUsage();
    } catch (err) { alert(err.message); }
};

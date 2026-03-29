const API_URL = '';
let currentUser = null;
let token = localStorage.getItem('token');
let allUsers = [];
let allOrgs = [];
let allPlans = [];

// ── DOM Elements ──────────────────────────────────────────
const logoutBtn = document.getElementById('logout-btn');
const currentUserNameSpan = document.getElementById('current-user-name');

// Nav items
const navLinks = {
    users: document.getElementById('nav-users'),
    orgs: document.getElementById('nav-orgs'),
    plans: document.getElementById('nav-plans'),
    subs: document.getElementById('nav-subs'),
};

// Sections
const sections = {
    users: document.getElementById('section-users'),
    orgs: document.getElementById('section-orgs'),
    plans: document.getElementById('section-plans'),
    subs: document.getElementById('section-subs'),
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
    if (key === 'users') fetchUsers();
    else if (key === 'orgs') fetchOrganizations();
    else if (key === 'plans') fetchPlans();
    else if (key === 'subs') fetchSubscriptions();
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

    // The dashboard is strictly for admins / super_admins
    if (currentUser.role !== 'admin' && currentUser.role !== 'super_admin') {
        alert('Access denied. Admin privileges required for the global dashboard.');
        logout();
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
//  USERS CRUD
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

const usersTableBody = document.querySelector('#users-table tbody');
const userModal = document.getElementById('user-modal');
const userForm = document.getElementById('user-form');
document.getElementById('add-user-btn').addEventListener('click', () => openUserModal());
userForm.addEventListener('submit', handleUserSubmit);

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
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.full_name || '-'}</td>
            <td>${user.email}</td>
            <td>${user.phone || '-'}</td>
            <td>${user.dob || '-'}</td>
            <td><span class="badge badge-${user.role}">${user.role}</span></td>
            <td>${user.is_active ? 'Active' : 'Inactive'}</td>
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
        document.getElementById('password-hint').style.display = 'block';
        document.getElementById('password').required = false;
    } else {
        document.getElementById('modal-title').textContent = 'Add User';
        userForm.reset();
        document.getElementById('user-id').value = '';
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
    if (!confirm('Delete this user?')) return;
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
    // Populate owner select from users
    if (allUsers.length === 0) await fetchUsers();
    const ownerSelect = document.getElementById('org-owner');
    ownerSelect.innerHTML = allUsers.map(u => `<option value="${u.id}">${u.full_name || u.email}</option>`).join('');

    orgModal.style.display = 'block';
    if (org) {
        document.getElementById('org-modal-title').textContent = 'Edit Organization';
        document.getElementById('org-id').value = org.id;
        document.getElementById('org-name').value = org.name;
        document.getElementById('org-type').value = org.type;
        document.getElementById('org-owner-group').style.display = 'none'; // Cannot change owner on edit
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
    const subs = await res.json();
    renderSubscriptions(subs);
}

function renderSubscriptions(subs) {
    subsTableBody.innerHTML = '';
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
    // Populate org and plan selects
    if (allOrgs.length === 0) {
        const res = await fetch(`${API_URL}/admin/organizations`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) allOrgs = await res.json();
    }
    if (allPlans.length === 0) {
        const res = await fetch(`${API_URL}/admin/plans`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) allPlans = await res.json();
    }

    const orgSelect = document.getElementById('sub-org');
    orgSelect.innerHTML = allOrgs.map(o => `<option value="${o.id}">${o.name}</option>`).join('');

    const planSelect = document.getElementById('sub-plan');
    planSelect.innerHTML = allPlans.map(p => `<option value="${p.id}">${p.name}</option>`).join('');

    subModal.style.display = 'block';
    if (sub) {
        document.getElementById('sub-modal-title').textContent = 'Edit Subscription';
        document.getElementById('sub-id').value = sub.id;
        document.getElementById('sub-org').value = sub.org_id;
        document.getElementById('sub-plan').value = sub.plan_id;
        document.getElementById('sub-type').value = sub.type;
        document.getElementById('sub-cancel').checked = sub.cancel_at_period_end;
        document.getElementById('sub-org-group').style.display = 'none'; // Cannot change org on edit
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

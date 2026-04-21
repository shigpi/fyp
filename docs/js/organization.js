// API_URL is defined in config.js (loaded before this script)
const token = localStorage.getItem('token');

// Elements
const currentUserNameSpan = document.getElementById('current-user-name');
const currentOrgRoleSpan = document.getElementById('current-org-role');
const membersTableBody = document.querySelector('#members-table tbody');
const addMemberBtn = document.getElementById('add-member-btn');
const memberModal = document.getElementById('member-modal');
const memberForm = document.getElementById('member-form');
const logoutBtn = document.getElementById('logout-btn');

let currentUser = null;
let currentOrg = null;
let targetOrgId = null;

// Modals Setup
document.querySelectorAll('.close').forEach(btn => {
    btn.addEventListener('click', () => {
        const modalId = btn.getAttribute('data-modal');
        document.getElementById(modalId).style.display = 'none';
    });
});
window.addEventListener('click', (e) => {
    if (e.target === memberModal) memberModal.style.display = 'none';
});

// Init
document.addEventListener('DOMContentLoaded', init);
logoutBtn.addEventListener('click', logout);
addMemberBtn.addEventListener('click', () => openMemberModal());
memberForm.addEventListener('submit', handleMemberSubmit);

async function init() {
    if (!token) { window.location.href = PAGES.login; return; }
    try {
        await fetchCurrentUserAndOrg();
        if (targetOrgId) {
            await fetchMembers();
        } else {
            alert('You are not a part of any team organization.');
            window.location.href = PAGES.appStore;
        }
    } catch (error) {
        console.error('Init error:', error);
        if (error.status === 401) logout();
    }
}

async function fetchCurrentUserAndOrg() {
    // 1. Get user profile
    const userRes = await fetch(`${API_URL}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!userRes.ok) throw { status: userRes.status };
    currentUser = await userRes.json();
    currentUserNameSpan.textContent = currentUser.full_name || currentUser.email;

    // 2. Get user orgs to find the Team org
    const orgsRes = await fetch(`${API_URL}/users/me/organizations`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!orgsRes.ok) throw { status: orgsRes.status };
    const memberships = await orgsRes.json();
    
    // Find the first team they are an owner or admin of
    currentOrg = memberships.find(m => 
        m.organization && m.organization.type === 'team' && 
        (m.role === 'owner' || m.role === 'admin')
    );

    if (currentOrg) {
        targetOrgId = currentOrg.organization.id;
        currentOrgRoleSpan.textContent = `Role: ${currentOrg.role.charAt(0).toUpperCase() + currentOrg.role.slice(1)}`;
        
        // Admins can't add other admins, only Owners can.
        if (currentOrg.role === 'admin') {
            document.getElementById('role').innerHTML = '<option value="member">Member</option>';
        }
    }
}

async function fetchMembers() {
    const res = await fetch(`${API_URL}/organizations/${targetOrgId}/members`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw { status: res.status };
    const members = await res.json();
    renderMembers(members);
}

function renderMembers(members) {
    membersTableBody.innerHTML = '';
    members.forEach(member => {
        const tr = document.createElement('tr');
        
        let actions = '';
        // Logic for what buttons to show based on requester's role
        if (member.user_id === currentUser.id) {
            actions = '<span style="color:var(--text-light); font-size:0.75rem;">(You)</span>';
        } else if (currentOrg.role === 'owner') {
            // Owners can edit/delete anyone
            actions = `
                <button class="action-btn edit-btn" onclick="editMember(${member.id}, '${member.role}')">Edit Role</button>
                <button class="action-btn delete-btn" onclick="deleteMember(${member.id})">Remove</button>
            `;
        } else if (currentOrg.role === 'admin') {
            // Admins can only edit/delete regular members
            if (member.role === 'member') {
                actions = `
                    <button class="action-btn edit-btn" onclick="editMember(${member.id}, '${member.role}')">Edit Role</button>
                    <button class="action-btn delete-btn" onclick="deleteMember(${member.id})">Remove</button>
                `;
            } else {
                actions = '<span style="color:var(--text-light); font-size:0.75rem;">Cannot modify</span>';
            }
        }

        tr.innerHTML = `
            <td>${member.full_name || '-'}</td>
            <td>${member.email}</td>
            <td><span class="badge badge-${member.role}">${member.role}</span></td>
            <td>${new Date(member.joined_at).toLocaleDateString()}</td>
            <td>${actions}</td>
        `;
        membersTableBody.appendChild(tr);
    });
}

function openMemberModal(memberId = null, currentRole = 'member') {
    memberModal.style.display = 'block';
    if (memberId) {
        document.getElementById('modal-title').textContent = 'Edit Member Role';
        document.getElementById('member-id').value = memberId;
        document.getElementById('user-id-group').style.display = 'none';
        document.getElementById('user-id').removeAttribute('required');
        document.getElementById('role').value = currentRole;
    } else {
        document.getElementById('modal-title').textContent = 'Add User to Organization';
        memberForm.reset();
        document.getElementById('member-id').value = '';
        document.getElementById('user-id-group').style.display = 'block';
        document.getElementById('user-id').setAttribute('required', 'true');
    }
}

window.editMember = (id, role) => {
    openMemberModal(id, role);
};

window.deleteMember = async (id) => {
    if (!confirm('Are you sure you want to remove this member from the organization?')) return;
    try {
        const res = await fetch(`${API_URL}/organizations/${targetOrgId}/members/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to remove member');
        }
        fetchMembers();
    } catch (err) { alert(err.message); }
};

async function handleMemberSubmit(e) {
    e.preventDefault();
    const memberId = document.getElementById('member-id').value;
    const role = document.getElementById('role').value;

    try {
        let res;
        if (memberId) {
            // Update
            res = await fetch(`${API_URL}/organizations/${targetOrgId}/members/${memberId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ role: role }),
            });
        } else {
            // Create
            const userId = parseInt(document.getElementById('user-id').value);
            res = await fetch(`${API_URL}/organizations/${targetOrgId}/members`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ user_id: userId, role: role }),
            });
        }

        if (!res.ok) { 
            const err = await res.json(); 
            throw new Error(err.detail || 'Failed to save member'); 
        }
        memberModal.style.display = 'none';
        fetchMembers();
    } catch (err) { 
        alert(err.message); 
    }
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = PAGES.login;
}

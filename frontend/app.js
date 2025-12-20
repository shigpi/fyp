const API_URL = '';
let currentUser = null;
let token = localStorage.getItem('token');

// DOM Elements
const usersTableBody = document.querySelector('#users-table tbody');
const modal = document.getElementById('user-modal');
const modalTitle = document.getElementById('modal-title');
const userForm = document.getElementById('user-form');
const addUserBtn = document.getElementById('add-user-btn');
const closeBtn = document.querySelector('.close');
const logoutBtn = document.getElementById('logout-btn');
const currentUserNameSpan = document.getElementById('current-user-name');

// Event Listeners
document.addEventListener('DOMContentLoaded', init);
addUserBtn.addEventListener('click', () => openModal());
closeBtn.addEventListener('click', closeModal);
window.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});
userForm.addEventListener('submit', handleFormSubmit);
logoutBtn.addEventListener('click', logout);

async function init() {
    if (!token) {
        window.location.href = '/admin/login';
        return;
    }

    try {
        await fetchCurrentUser();
        await fetchUsers();
    } catch (error) {
        console.error('Initialization error:', error);
        if (error.status === 401) {
            logout();
        }
    }
}

async function fetchCurrentUser() {
    const response = await fetch(`${API_URL}/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw { status: response.status };

    currentUser = await response.json();
    currentUserNameSpan.textContent = currentUser.full_name || currentUser.email;

    // Check if user is admin
    if (currentUser.role !== 'admin' && currentUser.role !== 'super_admin') {
        alert('Access denied. You must be an admin to view this page.');
        logout();
    }
}

async function fetchUsers() {
    const response = await fetch(`${API_URL}/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw { status: response.status };

    const users = await response.json();
    renderUsers(users);
}

function renderUsers(users) {
    usersTableBody.innerHTML = '';
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.full_name || '-'}</td>
            <td>${user.email}</td>
            <td><span class="badge badge-${user.role}">${user.role}</span></td>
            <td>${user.is_active ? 'Active' : 'Inactive'}</td>
            <td>
                <button class="action-btn edit-btn" onclick="editUser(${user.id})">Edit</button>
                ${currentUser.role === 'super_admin' ? `<button class="action-btn delete-btn" onclick="deleteUser(${user.id})">Delete</button>` : ''}
            </td>
        `;
        usersTableBody.appendChild(tr);
    });
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const userId = document.getElementById('user-id').value;
    const formData = {
        full_name: document.getElementById('full-name').value,
        email: document.getElementById('email').value,
        role: document.getElementById('role').value,
        is_active: document.getElementById('is-active').checked
    };

    const password = document.getElementById('password').value;
    if (password) {
        formData.password = password;
    }

    try {
        let response;
        if (userId) {
            // Update
            response = await fetch(`${API_URL}/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });
        } else {
            // Create
            if (!password) {
                alert('Password is required for new users');
                return;
            }
            response = await fetch(`${API_URL}/admin/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Operation failed');
        }

        closeModal();
        fetchUsers();
    } catch (error) {
        alert(error.message);
    }
}

window.editUser = async (id) => {
    try {
        const response = await fetch(`${API_URL}/admin/users/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch user details');

        const user = await response.json();
        openModal(user);
    } catch (error) {
        alert(error.message);
    }
};

window.deleteUser = async (id) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
        const response = await fetch(`${API_URL}/admin/users/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to delete user');

        fetchUsers();
    } catch (error) {
        alert(error.message);
    }
};

function openModal(user = null) {
    modal.style.display = 'block';
    if (user) {
        modalTitle.textContent = 'Edit User';
        document.getElementById('user-id').value = user.id;
        document.getElementById('full-name').value = user.full_name || '';
        document.getElementById('email').value = user.email;
        document.getElementById('role').value = user.role;
        document.getElementById('is-active').checked = user.is_active;
        document.getElementById('password-hint').style.display = 'block';
        document.getElementById('password').required = false;
    } else {
        modalTitle.textContent = 'Add User';
        userForm.reset();
        document.getElementById('user-id').value = '';
        document.getElementById('password-hint').style.display = 'none';
        document.getElementById('password').required = true;
    }
}

function closeModal() {
    modal.style.display = 'none';
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/admin/login';
}

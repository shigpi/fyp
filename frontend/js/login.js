const API_URL = '';
const loginForm = document.getElementById('login-form');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error('Login failed. Please check your credentials.');
        }

        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        const userRole = data.user.role;
        const orgId = data.user.organization_id;

        // Redirect logic based on role
        if (userRole === 'super_admin' || userRole === 'admin') {
            window.location.href = '/dashboard';
        } else {
            // For regular users, we need to check if they are owner/admin of a TEAM org.
            // Let's do a quick fetch to see their org memberships.
            const orgsRes = await fetch(`${API_URL}/users/me/organizations`, {
                headers: { 'Authorization': `Bearer ${data.access_token}` }
            });
            
            let isTeamAdmin = false;
            if (orgsRes.ok) {
                const memberships = await orgsRes.json();
                isTeamAdmin = memberships.some(m => 
                    m.organization && m.organization.type === 'team' && 
                    (m.role === 'owner' || m.role === 'admin')
                );
            }

            if (isTeamAdmin) {
                window.location.href = '/organization';
            } else {
                window.location.href = '/app-store';
            }
        }
    } catch (error) {
        alert(error.message);
    }
});

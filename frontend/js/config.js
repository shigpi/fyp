/**
 * VoiceScribe Frontend Configuration
 * 
 * This file centralises the API base URL and site navigation paths
 * so all pages and scripts use a single source of truth.
 */

// ── API Backend ──────────────────────────────────────────────────────────────
// Production (API Gateway / Lambda)
const API_URL = 'https://um90p4chb0.execute-api.ap-south-1.amazonaws.com/prod';

// Local development — uncomment this and comment the line above:
// const API_URL = '';

// ── Site Navigation ──────────────────────────────────────────────────────────
// Base path for the site on GitHub Pages (e.g., /fyp/frontend)
// Set to '' for local dev or root-level hosting.
const SITE_BASE = '/fyp/frontend';

// Page paths (used by JS redirects)
const PAGES = {
    home:           SITE_BASE + '/index.html',
    login:          SITE_BASE + '/pages/org/login.html',
    register:       SITE_BASE + '/pages/auth/register.html',
    verifyOtp:      SITE_BASE + '/pages/auth/verify_otp.html',
    forgotPassword: SITE_BASE + '/pages/auth/forgot_password.html',
    resetPassword:  SITE_BASE + '/pages/auth/reset_password.html',
    admin:          SITE_BASE + '/pages/admin/admin.html',
    organization:   SITE_BASE + '/pages/org/organization.html',
    appStore:       SITE_BASE + '/pages/misc/app_store_redirect.html',
};

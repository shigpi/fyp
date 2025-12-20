import 'package:app/pages/subscription_page.dart';
import 'package:app/pages/profile_page.dart';
import 'package:app/pages/settings_page.dart';
import 'package:app/pages/login_page.dart';
import 'package:app/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class Sidebar extends StatefulWidget {
  const Sidebar({super.key});

  @override
  State<Sidebar> createState() => _SidebarState();
}

class _SidebarState extends State<Sidebar> {
  final _storage = const FlutterSecureStorage();
  final _apiService = ApiService();
  String _userName = 'Loading...';
  String _userEmail = 'Loading...';

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
  }

  Future<void> _loadUserInfo() async {
    final name = await _storage.read(key: 'user_name');
    final email = await _storage.read(key: 'user_email');
    
    if (name != null && email != null) {
      if (mounted) {
        setState(() {
          _userName = name;
          _userEmail = email;
        });
      }
    } else {
      // Fallback: fetch from API
      final profile = await _apiService.getUserProfile();
      if (profile != null && mounted) {
        setState(() {
          _userName = profile['full_name'] ?? 'User';
          _userEmail = profile['email'] ?? 'Email';
        });
        // Cache it for next time
        await _storage.write(key: 'user_name', value: _userName);
        await _storage.write(key: 'user_email', value: _userEmail);
      } else if (mounted) {
        setState(() {
          _userName = 'User';
          _userEmail = 'Email';
        });
      }
    }
  }

  void _navigateToSubscription(BuildContext context) {
    Navigator.of(context).pop(); // Close sidebar
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => const SubscriptionPage()),
    );
  }

  void _navigateToProfile(BuildContext context) {
    Navigator.of(context).pop();
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => const ProfilePage()),
    );
  }

  void _navigateToSettings(BuildContext context) {
    Navigator.of(context).pop();
    Navigator.of(context).push(
      MaterialPageRoute(builder: (context) => const SettingsPage()),
    );
  }

  Future<void> _handleLogout(BuildContext context) async {
    await _apiService.logout();
    if (mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const LoginPage()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A0A), // Neutral 950
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(top: BorderSide(color: Color(0xFF262626))),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle
            Center(
              child: Container(
                margin: const EdgeInsets.only(top: 10, bottom: 6),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: const Color(0xFF404040), // Neutral 700
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Menu',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close, size: 20, color: Color(0xFFA3A3A3)),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: Color(0xFF171717)),

            // Profile Section
            Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  Container(
                    width: 48,
                    height: 48,
                    decoration: BoxDecoration(
                      color: const Color(0xFF171717),
                      shape: BoxShape.circle,
                      border: Border.all(color: const Color(0xFF262626)),
                    ),
                    child: const Icon(Icons.person, color: Color(0xFFA3A3A3)),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _userName,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _userEmail,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF737373),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: Color(0xFF171717)),

            // Menu Items
            _buildMenuItem(
              icon: Icons.person_outline,
              label: 'View Profile',
              onTap: () => _navigateToProfile(context),
            ),
            _buildMenuItem(
              icon: Icons.settings_outlined,
              label: 'Settings',
              onTap: () => _navigateToSettings(context),
            ),
            _buildMenuItem(
              icon: Icons.credit_card,
              label: 'Manage Subscription',
              onTap: () => _navigateToSubscription(context),
            ),

            const Divider(height: 1, color: Color(0xFF171717)),

            // Logout
            _buildMenuItem(
              icon: Icons.logout,
              label: 'Log Out',
              onTap: () => _handleLogout(context),
              textColor: const Color(0xFFA3A3A3),
              hoverColor: Colors.redAccent,
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildMenuItem({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    Color? textColor,
    Color? hoverColor,
  }) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Row(
          children: [
            Icon(icon, size: 20, color: const Color(0xFFA3A3A3)),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  color: textColor ?? const Color(0xFFD4D4D4), // Neutral 300
                ),
              ),
            ),
            const Icon(Icons.chevron_right, size: 20, color: Color(0xFF525252)),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:app/services/api_service.dart';
import 'package:app/pages/profile_page.dart';
import 'package:app/pages/subscription_page.dart';
import 'package:app/pages/login_page.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _apiService = ApiService();
  bool _isLoggingOut = false;
  bool _isDeletingAccount = false;

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open link')),
        );
      }
    }
  }

  Future<void> _handleLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF171717),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Log Out', style: TextStyle(color: Colors.white)),
        content: const Text(
          'Are you sure you want to log out?',
          style: TextStyle(color: Color(0xFFA3A3A3)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFFA3A3A3))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Log Out', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _isLoggingOut = true);
    await _apiService.logout();
    if (!mounted) return;

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => const LoginPage()),
      (route) => false,
    );
  }

  Future<void> _handleDeleteAccount() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF171717),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text('Delete Account', style: TextStyle(color: Colors.redAccent)),
        content: const Text(
          'This action is permanent and cannot be undone. All your data, including your organization, will be deleted.',
          style: TextStyle(color: Color(0xFFA3A3A3)),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel', style: TextStyle(color: Color(0xFFA3A3A3))),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete', style: TextStyle(color: Colors.redAccent)),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;

    setState(() => _isDeletingAccount = true);
    try {
      await _apiService.deleteAccount();
      if (!mounted) return;

      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const LoginPage()),
        (route) => false,
      );
    } catch (e) {
      if (!mounted) return;
      setState(() => _isDeletingAccount = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to delete account: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: const Icon(Icons.arrow_back, color: Color(0xFFA3A3A3), size: 20),
                  ),
                  const SizedBox(width: 12),
                  const Text(
                    'Settings',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: Color(0xFF171717)),

            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                   _buildSectionTitle('Account'),
                   _buildSettingTile(Icons.person_outline, 'Personal Information', onTap: () {
                     Navigator.of(context).push(
                       MaterialPageRoute(builder: (context) => const ProfilePage()),
                     );
                   }),
                   _buildSettingTile(Icons.lock_outline, 'Password & Security', onTap: () {}),
                   _buildSettingTile(Icons.notifications_none, 'Notifications', onTap: () {}),
                   _buildSettingTile(Icons.credit_card, 'Subscription', onTap: () {
                     Navigator.of(context).push(
                       MaterialPageRoute(builder: (context) => const SubscriptionPage()),
                     );
                   }),
                   
                   const SizedBox(height: 24),
                   _buildSectionTitle('Preferences'),
                   _buildSettingTile(Icons.palette_outlined, 'Appearance', trailing: 'Dark Mode', onTap: () {}),
                   
                   const SizedBox(height: 24),
                   _buildSectionTitle('About'),
                   _buildSettingTile(Icons.info_outline, 'Version', trailing: '1.0.0', onTap: () {}),
                   _buildSettingTile(Icons.description_outlined, 'Privacy Policy', onTap: () {
                     // TODO: Replace with actual Privacy Policy URL
                     _openUrl('https://example.com/privacy');
                   }),
                   _buildSettingTile(Icons.gavel_outlined, 'Terms of Service', onTap: () {
                     // TODO: Replace with actual Terms of Service URL
                     _openUrl('https://example.com/terms');
                   }),
                   _buildSettingTile(Icons.help_outline, 'Help & Support', onTap: () {}),

                   const SizedBox(height: 24),
                   _buildSectionTitle('Danger Zone'),
                   _buildSettingTile(
                     Icons.logout,
                     _isLoggingOut ? 'Logging out...' : 'Log Out',
                     onTap: _isLoggingOut ? null : _handleLogout,
                     textColor: Colors.white,
                   ),
                   _buildSettingTile(
                     Icons.delete_forever_outlined,
                     _isDeletingAccount ? 'Deleting...' : 'Delete Account',
                     onTap: _isDeletingAccount ? null : _handleDeleteAccount,
                     textColor: Colors.redAccent,
                   ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, left: 4),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Color(0xFF737373),
          letterSpacing: 1.2,
        ),
      ),
    );
  }

  Widget _buildSettingTile(IconData icon, String title, {String? trailing, VoidCallback? onTap, Color? textColor}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF171717),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF262626)),
      ),
      child: ListTile(
        onTap: onTap,
        leading: Icon(icon, color: textColor ?? const Color(0xFFA3A3A3), size: 20),
        title: Text(
          title,
          style: TextStyle(color: textColor ?? Colors.white, fontSize: 14),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (trailing != null)
              Text(
                trailing,
                style: const TextStyle(color: Color(0xFF737373), fontSize: 13),
              ),
            const SizedBox(width: 4),
            const Icon(Icons.chevron_right, color: Color(0xFF525252), size: 20),
          ],
        ),
      ),
    );
  }
}

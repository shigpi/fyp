import 'package:flutter/material.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

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
                   _buildSettingTile(Icons.person_outline, 'Personal Information', onTap: () {}),
                   _buildSettingTile(Icons.lock_outline, 'Password & Security', onTap: () {}),
                   _buildSettingTile(Icons.notifications_none, 'Notifications', onTap: () {}),
                   
                   const SizedBox(height: 24),
                   _buildSectionTitle('Preferences'),
                   _buildSettingTile(Icons.palette_outlined, 'Appearance', trailing: 'Dark Mode', onTap: () {}),
                   _buildSettingTile(Icons.language_outlined, 'Language', trailing: 'English', onTap: () {}),
                   
                   const SizedBox(height: 24),
                   _buildSectionTitle('About'),
                   _buildSettingTile(Icons.info_outline, 'Version', trailing: '1.0.0', onTap: () {}),
                   _buildSettingTile(Icons.description_outlined, 'Privacy Policy', onTap: () {}),
                   _buildSettingTile(Icons.help_outline, 'Help & Support', onTap: () {}),
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

  Widget _buildSettingTile(IconData icon, String title, {String? trailing, VoidCallback? onTap}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF171717),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF262626)),
      ),
      child: ListTile(
        onTap: onTap,
        leading: Icon(icon, color: const Color(0xFFA3A3A3), size: 20),
        title: Text(
          title,
          style: const TextStyle(color: Colors.white, fontSize: 14),
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

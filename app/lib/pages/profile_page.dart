import 'package:flutter/material.dart';
import 'package:app/services/api_service.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final _apiService = ApiService();
  Map<String, dynamic>? _userProfile;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    try {
      final profile = await _apiService.getUserProfile();
      if (mounted) {
        setState(() {
          _userProfile = profile;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load profile: $e')),
        );
      }
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
                    'Profile',
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
              child: _isLoading 
                ? const Center(child: CircularProgressIndicator())
                : _userProfile == null 
                  ? const Center(child: Text('Failed to load profile data', style: TextStyle(color: Colors.white)))
                  : ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  // Avatar and Basic Info
                  Center(
                    child: Column(
                      children: [
                        Container(
                          width: 80,
                          height: 80,
                          decoration: BoxDecoration(
                            color: const Color(0xFF171717),
                            shape: BoxShape.circle,
                            border: Border.all(color: const Color(0xFF262626)),
                          ),
                          child: const Icon(Icons.person, color: Color(0xFFA3A3A3), size: 40),
                        ),
                        const SizedBox(height: 16),
                        Text(
                          _userProfile?['full_name'] ?? 'User',
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          _userProfile?['email'] ?? '',
                          style: const TextStyle(
                            fontSize: 14,
                            color: Color(0xFF737373),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Profile Details
                  _buildProfileItem('Full Name', _userProfile?['full_name'] ?? '-'),
                  _buildProfileItem('Email', _userProfile?['email'] ?? '-'),
                  _buildProfileItem('Phone', _userProfile?['phone'] ?? '-'),
                  _buildProfileItem('Date of Birth', _userProfile?['dob'] ?? '-'),
                  if (_userProfile?['organization_id'] != null)
                    _buildProfileItem('Organization ID', _userProfile?['organization_id'].toString() ?? '-'),
                  
                  const SizedBox(height: 32),
                  
                  // Edit Button
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () {},
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: const Text('Edit Profile'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileItem(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              color: Color(0xFF737373),
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: const Color(0xFF171717),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFF262626)),
            ),
            child: Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

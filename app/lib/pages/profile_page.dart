import 'package:flutter/material.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

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
              child: ListView(
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
                        const Text(
                          'John Doe',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          'john.doe@email.com',
                          style: TextStyle(
                            fontSize: 14,
                            color: Color(0xFF737373),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Profile Details
                  _buildProfileItem('Full Name', 'John Doe'),
                  _buildProfileItem('Email', 'john.doe@email.com'),
                  _buildProfileItem('Phone', '+1 234 567 8900'),
                  _buildProfileItem('Location', 'London, UK'),
                  
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

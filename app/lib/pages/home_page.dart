import 'package:app/pages/history_page.dart';
import 'package:app/transcription_page.dart';
import 'package:app/widgets/sidebar.dart';
import 'package:flutter/material.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  void _startRecording(String mode) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const TranscriptionPage(), // We'll update this to accept mode later
      ),
    );
  }

  void _openSidebar() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) => const Sidebar(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: const BoxDecoration(
                border: Border(
                  bottom: BorderSide(color: Color(0xFF171717)), // Neutral 900
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: const Color(0xFF171717),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF262626)),
                        ),
                        child: const Icon(Icons.mic, color: Colors.white, size: 16),
                      ),
                      const SizedBox(width: 10),
                      const Text(
                        'VoiceScribe',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: Colors.white,
                        ),
                      ),
                    ],
                  ),
                  IconButton(
                    onPressed: _openSidebar,
                    icon: const Icon(Icons.menu, color: Color(0xFFA3A3A3)),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),

            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      'Choose Transcription Mode',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Select your preferred language mode',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFF737373), // Neutral 500
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Options
                    _buildOptionCard(
                      title: 'Multilingual Transcription',
                      description: 'Automatic language detection',
                      icon: Icons.language,
                      onTap: () => _startRecording('multilingual'),
                    ),
                    const SizedBox(height: 10),
                    _buildOptionCard(
                      title: 'English Transcription',
                      description: 'Optimized for English',
                      icon: Icons.mic,
                      onTap: () => _startRecording('english'),
                    ),
                    const SizedBox(height: 10),
                    _buildOptionCard(
                      title: 'Nepali Transcription',
                      description: 'नेपाली भाषा',
                      icon: Icons.translate,
                      onTap: () => _startRecording('nepali'),
                    ),
                    const SizedBox(height: 24),
                    
                    // History Option
                    _buildOptionCard(
                      title: 'View History',
                      description: 'Access past transcriptions',
                      icon: Icons.history,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const HistoryPage(),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOptionCard({
    required String title,
    required String description,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF171717), // Neutral 900
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF262626)),
        ),
        child: Row(
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: const Color(0xFF262626), // Neutral 800
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF404040)), // Neutral 700
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    description,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF737373), // Neutral 500
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
}

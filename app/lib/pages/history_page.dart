import 'package:flutter/material.dart';

class HistoryPage extends StatelessWidget {
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    // Mock data for history
    final historyItems = [
      {
        'date': 'Today, 10:30 AM',
        'duration': '2:15',
        'preview': 'The quick brown fox jumps over the lazy dog. This is a test transcription...',
        'mode': 'English',
      },
      {
        'date': 'Yesterday, 4:45 PM',
        'duration': '5:30',
        'preview': 'नमस्ते, यो नेपाली ट्रान्सक्रिप्शनको नमूना हो।',
        'mode': 'Nepali',
      },
      {
        'date': 'Dec 5, 2025',
        'duration': '1:05',
        'preview': 'Bonjour, comment allez-vous? This is a multilingual test.',
        'mode': 'Multilingual',
      },
    ];

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
                    'History',
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

            // Content
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.all(20),
                itemCount: historyItems.length,
                separatorBuilder: (context, index) => const SizedBox(height: 12),
                itemBuilder: (context, index) {
                  final item = historyItems[index];
                  return Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF171717), // Neutral 900
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF262626)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              item['date'] as String,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF262626),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                item['mode'] as String,
                                style: const TextStyle(
                                  color: Color(0xFFA3A3A3),
                                  fontSize: 10,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          item['preview'] as String,
                          style: const TextStyle(
                            color: Color(0xFFA3A3A3), // Neutral 400
                            fontSize: 13,
                            height: 1.5,
                          ),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            const Icon(Icons.access_time, size: 14, color: Color(0xFF737373)),
                            const SizedBox(width: 4),
                            Text(
                              item['duration'] as String,
                              style: const TextStyle(
                                color: Color(0xFF737373), // Neutral 500
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

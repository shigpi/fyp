import 'package:flutter/material.dart';
import 'package:app/services/history_service.dart';
import 'package:intl/intl.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  final HistoryService _historyService = HistoryService();
  List<Map<String, dynamic>> _historyItems = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final items = await _historyService.getHistory();
    if (mounted) {
      setState(() {
        _historyItems = items;
        _isLoading = false;
      });
    }
  }

  String _formatDateString(String isoDate) {
    try {
      final date = DateTime.parse(isoDate).toLocal();
      final now = DateTime.now();

      final today = DateTime(now.year, now.month, now.day);
      final yesterday = today.subtract(const Duration(days: 1));
      final dateToCheck = DateTime(date.year, date.month, date.day);

      if (dateToCheck == today) {
        return 'Today, ${DateFormat('h:mm a').format(date)}';
      } else if (dateToCheck == yesterday) {
        return 'Yesterday, ${DateFormat('h:mm a').format(date)}';
      }
      return DateFormat('MMM d, yyyy - h:mm a').format(date);
    } catch (_) {
      return isoDate;
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
              child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: Colors.white))
                : _historyItems.isEmpty
                  ? const SizedBox.shrink()
                  : ListView.separated(
                      padding: const EdgeInsets.all(20),
                      itemCount: _historyItems.length,
                      separatorBuilder: (context, index) => const SizedBox(height: 12),
                      itemBuilder: (context, index) {
                        final item = _historyItems[index];
                        return GestureDetector(
                          onTap: () {
                            showModalBottomSheet(
                              context: context,
                              backgroundColor: const Color(0xFF171717),
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                              ),
                              isScrollControlled: true,
                              builder: (context) {
                                return DraggableScrollableSheet(
                                  initialChildSize: 0.6,
                                  minChildSize: 0.3,
                                  maxChildSize: 0.9,
                                  expand: false,
                                  builder: (context, scrollController) {
                                    return Padding(
                                      padding: const EdgeInsets.all(20.0),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Center(
                                            child: Container(
                                              width: 40,
                                              height: 4,
                                              decoration: BoxDecoration(
                                                color: const Color(0xFF262626),
                                                borderRadius: BorderRadius.circular(2),
                                              ),
                                            ),
                                          ),
                                          const SizedBox(height: 20),
                                          Row(
                                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                            children: [
                                              Text(
                                                _formatDateString(item['date'] as String? ?? ''),
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 16,
                                                  fontWeight: FontWeight.w600,
                                                ),
                                              ),
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                                decoration: BoxDecoration(
                                                  color: const Color(0xFF262626),
                                                  borderRadius: BorderRadius.circular(4),
                                                ),
                                                child: Text(
                                                  item['mode'] as String? ?? 'Unknown',
                                                  style: const TextStyle(
                                                    color: Color(0xFFA3A3A3),
                                                    fontSize: 12,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 16),
                                          const Text(
                                            'Transcription:',
                                            style: TextStyle(
                                              color: Color(0xFFA3A3A3),
                                              fontSize: 14,
                                              fontWeight: FontWeight.w500,
                                            ),
                                          ),
                                          const SizedBox(height: 8),
                                          Expanded(
                                            child: SingleChildScrollView(
                                              controller: scrollController,
                                              child: Text(
                                                item['text'] as String? ?? (item['preview'] as String? ?? ''),
                                                style: const TextStyle(
                                                  color: Colors.white,
                                                  fontSize: 16,
                                                  height: 1.6,
                                                ),
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    );
                                  },
                                );
                              },
                            );
                          },
                          child: Container(
                            padding: const EdgeInsets.all(16),
                            decoration: BoxDecoration(
                              color: const Color(0xFF171717),
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
                                      _formatDateString(item['date'] as String? ?? ''),
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
                                        item['mode'] as String? ?? 'Unknown',
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
                                  item['preview'] as String? ?? '',
                                  style: const TextStyle(
                                    color: Color(0xFFA3A3A3),
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
                                      item['duration'] as String? ?? '0:00',
                                      style: const TextStyle(
                                        color: Color(0xFF737373),
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ],
                            ),
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

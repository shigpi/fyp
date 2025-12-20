import 'dart:async';
import 'package:flutter/material.dart';

class TranscriptionPage extends StatefulWidget {
  const TranscriptionPage({super.key});

  @override
  State<TranscriptionPage> createState() => _TranscriptionPageState();
}

class _TranscriptionPageState extends State<TranscriptionPage>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  bool _isLoading = false;
  String? _transcript;
  int _recordingTime = 0;
  Timer? _timer;
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _animationController.dispose();
    super.dispose();
  }

  void _toggleRecording() {
    if (_isRecording) {
      // Stop recording
      _timer?.cancel();
      setState(() {
        _isRecording = false;
        _isLoading = true;
      });

      // Simulate processing
      Future.delayed(const Duration(seconds: 2), () {
        setState(() {
          _isLoading = false;
          _transcript =
              "This is a mock transcript. In a real app, this would be the text generated from your speech. The quick brown fox jumps over the lazy dog. Flutter is amazing for building beautiful UIs.";
        });
      });
    } else {
      // Start recording
      setState(() {
        _isRecording = true;
        _transcript = null;
        _recordingTime = 0;
      });

      _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
        setState(() {
          _recordingTime++;
        });
      });
    }
  }

  String _formatTime(int seconds) {
    final mins = (seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (seconds % 60).toString().padLeft(2, '0');
    return '$mins:$secs';
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
                    'Multilingual Mode',
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
              child: _buildContent(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(
              width: 48,
              height: 48,
              child: CircularProgressIndicator(
                color: Colors.white,
                strokeWidth: 4,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Processing transcription...',
              style: TextStyle(
                color: Color(0xFFA3A3A3),
                fontSize: 14,
              ),
            ),
          ],
        ),
      );
    } else if (_transcript != null) {
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Transcription Result',
              style: TextStyle(
                color: Colors.white,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF171717), // Neutral 900
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF262626)),
                ),
                child: SingleChildScrollView(
                  child: Text(
                    _transcript!,
                    style: const TextStyle(
                      color: Color(0xFFE5E5E5), // Neutral 200
                      fontSize: 14,
                      height: 1.6,
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton(
                onPressed: () {
                  setState(() {
                    _transcript = null;
                    _recordingTime = 0;
                  });
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('New Recording'),
              ),
            ),
          ],
        ),
      );
    } else {
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (_isRecording) ...[
            const Text(
              'Recording...',
              style: TextStyle(
                color: Color(0xFFA3A3A3),
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              _formatTime(_recordingTime),
              style: const TextStyle(
                color: Colors.white,
                fontSize: 24,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 40),
          ] else
            const Padding(
              padding: EdgeInsets.only(bottom: 40),
              child: Text(
                'Tap to start recording',
                style: TextStyle(
                  color: Color(0xFFA3A3A3),
                  fontSize: 14,
                ),
              ),
            ),
          
          GestureDetector(
            onTap: _toggleRecording,
            child: Stack(
              alignment: Alignment.center,
              children: [
                if (_isRecording)
                  FadeTransition(
                    opacity: _animationController,
                    child: Container(
                      width: 120,
                      height: 120,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.white.withOpacity(0.1),
                      ),
                    ),
                  ),
                Container(
                  width: 96,
                  height: 96,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: _isRecording ? Colors.white : const Color(0xFF171717),
                    border: Border.all(
                      color: _isRecording ? Colors.white : const Color(0xFF404040),
                      width: 2,
                    ),
                  ),
                  child: Icon(
                    _isRecording ? Icons.stop : Icons.mic,
                    color: _isRecording ? Colors.black : Colors.white,
                    size: 36,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 40),
          Text(
            _isRecording ? 'Tap the square to stop' : 'Tap the microphone to begin',
            style: const TextStyle(
              color: Color(0xFF737373),
              fontSize: 12,
            ),
          ),
        ],
      );
    }
  }
}

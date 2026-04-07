import 'dart:async';
import 'package:app/services/api_service.dart';
import 'package:app/services/history_service.dart';
import 'package:app/services/recording_service.dart';
import 'package:app/services/api_exception.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class TranscriptionPage extends StatefulWidget {
  final String mode;
  final String? initialAudioPath;
  const TranscriptionPage({super.key, required this.mode, this.initialAudioPath});

  @override
  State<TranscriptionPage> createState() => _TranscriptionPageState();
}

class _TranscriptionPageState extends State<TranscriptionPage>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  bool _isLoading = false;
  bool _isTransliterating = false;
  String? _transcript;
  int _recordingTime = 0;
  Timer? _timer;
  late AnimationController _animationController;
  final RecordingService _recordingService = RecordingService();
  final ApiService _apiService = ApiService();
  final HistoryService _historyService = HistoryService();

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    if (widget.initialAudioPath != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _runTranscription(widget.initialAudioPath!);
      });
    }
  }

  Future<void> _runTranscription(String path) async {
    setState(() {
      _isLoading = true;
    });

    try {
      String? languageCode;
      if (widget.mode == 'nepali') {
        languageCode = 'ne';
      } else if (widget.mode == 'english') {
        languageCode = 'en';
      }
      
      final transcription = await _apiService.transcribe(path, language: languageCode);
      
      if (mounted) {
        setState(() {
          _transcript = transcription;
        });
      }

      if (transcription != null && transcription.isNotEmpty) {
        await _historyService.addHistory({
          'date': DateTime.now().toIso8601String(),
          'mode': widget.mode == 'nepali' ? 'Nepali' : widget.mode == 'english' ? 'English' : 'Multilingual',
          'text': transcription,
          'preview': transcription.length > 100 ? '${transcription.substring(0, 100)}...' : transcription,
          'duration': _formatTime(_recordingTime),
        });
      }
    } catch (e) {
      if (e is ApiException && e.statusCode == 401) {
        final storage = const FlutterSecureStorage();
        await storage.write(key: 'pending_audio_path', value: path);
        await storage.write(key: 'pending_audio_mode', value: widget.mode);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _animationController.dispose();
    _recordingService.dispose();
    super.dispose();
  }

  void _toggleRecording() async {
    if (_isRecording) {
      // Stop recording
      _timer?.cancel();
      setState(() {
        _isRecording = false;
      });

      try {
        final path = await _recordingService.stopRecording();
        if (path != null) {
          await _runTranscription(path);
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e')),
          );
        }
      }
    } else {
      // Start recording
      final hasPermission = await _recordingService.checkPermission();
      if (!hasPermission) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission denied')),
          );
        }
        return;
      }

      setState(() {
        _isRecording = true;
        _transcript = null;
        _recordingTime = 0;
      });

      await _recordingService.startRecording();

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

  Future<void> _transliterateText() async {
    if (_transcript == null || _transcript!.isEmpty) return;
    
    setState(() {
      _isTransliterating = true;
    });
    
    try {
      final transliterated = await _apiService.transliterate(_transcript!);
      setState(() {
         // Displaying the transliterated text as the new transcript or appending it.
         // Let's replace the whole text so they can see the converted nepali output easily.
         _transcript = transliterated;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error transliterating: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isTransliterating = false;
        });
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
                  Text(
                    widget.mode == 'nepali' 
                      ? 'Nepali Transcription' 
                      : widget.mode == 'english' 
                        ? 'English Transcription' 
                        : 'Multilingual Mode',
                    style: const TextStyle(
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
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Transcription Result',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                GestureDetector(
                  onTap: () {
                    Clipboard.setData(ClipboardData(text: _transcript!));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Copied to clipboard')),
                    );
                  },
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: const Color(0xFF262626),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.copy, color: Color(0xFFA3A3A3), size: 18),
                  ),
                ),
              ],
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
                  child: SelectableText(
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
            const SizedBox(height: 12),
            if (widget.mode != 'english') ...[
              SizedBox(
                width: double.infinity,
                height: 48,
                child: OutlinedButton(
                  onPressed: _isTransliterating ? null : _transliterateText,
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white,
                    side: const BorderSide(color: Color(0xFF404040)),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isTransliterating
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                        )
                      : const Text('Transliterate to Nepali'),
                ),
              ),
              const SizedBox(height: 12),
            ],
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

import 'package:flutter/material.dart';
// import 'dart:async';

class TranscriptionPage extends StatefulWidget {
  const TranscriptionPage({super.key});

  @override
  State<TranscriptionPage> createState() => _TranscriptionPageState();
}

class _TranscriptionPageState extends State<TranscriptionPage>
    with SingleTickerProviderStateMixin {
  bool _isRecording = false;
  String _transcript = '';
  late AnimationController _animationController;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  void _toggleRecording() {
    setState(() {
      if (_isRecording) {
        // Stop recording
        _isRecording = false;
        // Generate mock transcript
        _transcript =
            "This is a mock transcript. In a real app, this would be the text generated from your speech. The quick brown fox jumps over the lazy dog. Flutter is amazing for building beautiful UIs.";
      } else {
        // Start recording
        _isRecording = true;
        _transcript = ''; // Clear previous transcript
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text(
          'Transcription',
          style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2),
        ),
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              const Color(0xFF0F2027), // Deep Blue
              const Color(0xFF203A43), // Teal-ish
              const Color(0xFF2C5364), // Darker Teal
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: _buildContent(colorScheme),
                ),
              ),
              _buildBottomControls(colorScheme),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent(ColorScheme colorScheme) {
    if (_isRecording) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            FadeTransition(
              opacity: _animationController,
              child: Icon(
                Icons.mic,
                size: 80,
                color: colorScheme.primary,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              'Listening...',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w300,
                color: colorScheme.onSurface.withOpacity(0.8),
              ),
            ),
          ],
        ),
      );
    } else if (_transcript.isNotEmpty) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: colorScheme.surface.withOpacity(0.8),
          borderRadius: BorderRadius.circular(24),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Transcript',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: colorScheme.primary,
                  letterSpacing: 1.5,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                _transcript,
                style: TextStyle(
                  fontSize: 18,
                  height: 1.6,
                  color: colorScheme.onSurface,
                ),
              ),
            ],
          ),
        ),
      );
    } else {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.graphic_eq,
              size: 80,
              color: colorScheme.onSurface.withOpacity(0.2),
            ),
            const SizedBox(height: 16),
            Text(
              'Tap to Record',
              style: TextStyle(
                fontSize: 20,
                color: colorScheme.onSurface.withOpacity(0.5),
              ),
            ),
          ],
        ),
      );
    }
  }

  Widget _buildBottomControls(ColorScheme colorScheme) {
    return Container(
      padding: const EdgeInsets.only(bottom: 48, top: 24),
      child: GestureDetector(
        onTap: _toggleRecording,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 300),
          height: 80,
          width: 80,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: _isRecording ? Colors.redAccent : colorScheme.primary,
            boxShadow: [
              BoxShadow(
                color: (_isRecording ? Colors.redAccent : colorScheme.primary)
                    .withOpacity(0.4),
                blurRadius: 20,
                spreadRadius: 5,
              ),
            ],
          ),
          child: Icon(
            _isRecording ? Icons.stop : Icons.mic,
            color: Colors.white,
            size: 36,
          ),
        ),
      ),
    );
  }
}

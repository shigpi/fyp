import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path/path.dart' as p;

class RecordingService {
  final AudioRecorder _audioRecorder = AudioRecorder();
  String? _currentPath;

  Future<bool> checkPermission() async {
    final status = await Permission.microphone.status;
    print('Microphone permission status: $status');
    
    if (status.isGranted) {
      return true;
    }
    
    if (status.isPermanentlyDenied) {
      print('Microphone permission permanently denied. Please enable it in settings.');
      return false;
    }

    final result = await Permission.microphone.request();
    print('Requested microphone permission, result: $result');
    return result.isGranted;
  }

  Future<void> startRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        final directory = await getApplicationDocumentsDirectory();
        final fileName = 'recording_${DateTime.now().millisecondsSinceEpoch}.wav';
        _currentPath = p.join(directory.path, fileName);

        const config = RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        );

        await _audioRecorder.start(config, path: _currentPath!);
        print('Recording started: $_currentPath');
      } else {
        print('Microphone permission not granted');
      }
    } catch (e) {
      print('Error starting recording: $e');
    }
  }

  Future<String?> stopRecording() async {
    try {
      final path = await _audioRecorder.stop();
      print('Recording stopped: $path');
      return path;
    } catch (e) {
      print('Error stopping recording: $e');
      return null;
    }
  }

  void dispose() {
    _audioRecorder.dispose();
  }
}

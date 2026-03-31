import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';

class HistoryService {
  static const String _fileName = 'transcription_history.json';

  Future<File> get _localFile async {
    final directory = await getApplicationDocumentsDirectory();
    return File('${directory.path}/$_fileName');
  }

  Future<List<Map<String, dynamic>>> getHistory() async {
    try {
      final file = await _localFile;
      if (!await file.exists()) {
        return [];
      }

      final contents = await file.readAsString();
      final List<dynamic> jsonList = jsonDecode(contents);
      return List<Map<String, dynamic>>.from(jsonList);
    } catch (e) {
      print('Error reading history: $e');
      return [];
    }
  }

  Future<void> addHistory(Map<String, dynamic> item) async {
    try {
      final file = await _localFile;
      List<Map<String, dynamic>> history = [];

      if (await file.exists()) {
        final contents = await file.readAsString();
        final List<dynamic> jsonList = jsonDecode(contents);
        history = List<Map<String, dynamic>>.from(jsonList);
      }

      // Add new item at the beginning
      history.insert(0, item);

      await file.writeAsString(jsonEncode(history));
    } catch (e) {
      print('Error writing history: $e');
    }
  }

  Future<void> clearHistory() async {
     try {
       final file = await _localFile;
       if (await file.exists()) {
         await file.delete();
       }
     } catch (e) {
       print('Error clearing history: $e');
     }
  }

  Future<void> deleteHistoryItem(int index) async {
    try {
      final file = await _localFile;
      if (!await file.exists()) return;

      final contents = await file.readAsString();
      final List<dynamic> jsonList = jsonDecode(contents);
      final history = List<Map<String, dynamic>>.from(jsonList);

      if (index < 0 || index >= history.length) return;

      history.removeAt(index);
      await file.writeAsString(jsonEncode(history));
    } catch (e) {
      print('Error deleting history item: $e');
      rethrow;
    }
  }
}

import 'dart:convert';

class ApiException implements Exception {
  final int? statusCode;
  final String message;

  ApiException(this.statusCode, String responseBody) : message = _parseMessage(responseBody);
  ApiException.message(this.message) : statusCode = null;

  static String _parseMessage(String responseBody) {
    try {
      final decoded = jsonDecode(responseBody);
      if (decoded is Map<String, dynamic>) {
        if (decoded.containsKey('detail')) {
          final detail = decoded['detail'];
          if (detail is String) return detail;
          if (detail is List && detail.isNotEmpty) {
            return detail.map((e) => e['msg']?.toString() ?? 'Validation error').join(', ');
          }
        }
        if (decoded.containsKey('message')) {
          return decoded['message'].toString();
        }
      }
    } catch (_) {
      // Ignored
    }
    return responseBody.isEmpty ? 'An unknown error occurred' : responseBody;
  }

  @override
  String toString() => message;
}

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/material.dart';
import 'package:app/main.dart';
import 'package:app/pages/login_page.dart';
import 'api_exception.dart';

class ApiService {
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  // static const String baseUrl = 'http://10.0.2.2:8000'; 
  static const String baseUrl = 'https://um90p4chb0.execute-api.ap-south-1.amazonaws.com/prod';

  // Frontend pages hosted on GitHub Pages (used by WebView for register, etc.)
  static const String webUrl = 'https://shigpi.github.io/fyp';

  final _storage = const FlutterSecureStorage();

  void _checkUnauthorized(int statusCode) {
    if (statusCode == 401) {
      logout();
      if (navigatorKey.currentContext != null) {
        ScaffoldMessenger.of(navigatorKey.currentContext!).showSnackBar(
          const SnackBar(content: Text('Connection timed out. Please sign in again.')),
        );
      }
      navigatorKey.currentState?.pushAndRemoveUntil(
        MaterialPageRoute(builder: (context) => const LoginPage()),
        (route) => false,
      );
    }
  }


  Future<Map<String, dynamic>> register(String name, String email, String password, {String? phone, String? dob}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'full_name': name,
        if (phone != null && phone.isNotEmpty) 'phone': phone,
        if (dob != null && dob.isNotEmpty) 'dob': dob,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      if (data['user'] != null) {
        await _storage.write(key: 'token', value: data['access_token']);
        await _storage.write(key: 'user_name', value: data['user']['full_name']?.toString() ?? 'User');
        await _storage.write(key: 'user_email', value: data['user']['email']?.toString() ?? 'Email');
        if (data['user']['organization_id'] != null) {
          await _storage.write(key: 'org_id', value: data['user']['organization_id'].toString());
        }
      } else {
        await _storage.write(key: 'token', value: data['access_token']);
      }
      return data;
    } else {
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<Map<String, dynamic>?> getUserProfile() async {
    final token = await getToken();
    if (token == null) return null;

    final response = await http.get(
      Uri.parse('$baseUrl/users/me'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _checkUnauthorized(response.statusCode);
      return null;
    }
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'token');
  }

  Future<String?> logout() async {
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'user_name');
    await _storage.delete(key: 'user_email');
    await _storage.delete(key: 'org_id');
    return null;
  }

  Future<String> transcribe(String audioPath, {String? language}) async {
    final token = await getToken();
    
    var uri = Uri.parse('$baseUrl/transcribe');
    if (language != null) {
      uri = uri.replace(queryParameters: {'language': language});
    }
    
    var request = http.MultipartRequest('POST', uri);
    
    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    request.files.add(await http.MultipartFile.fromPath('file', audioPath));

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['transcription'];
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<String> transliterate(String text) async {
    final token = await getToken();
    
    final response = await http.post(
      Uri.parse('$baseUrl/transliterate'),
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      },
      body: jsonEncode({'text': text}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['transliterated_text'];
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<List<Map<String, dynamic>>?> getPlans() async {
    final token = await getToken();
    if (token == null) return null;

    final response = await http.get(
      Uri.parse('$baseUrl/users/plans'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      final List<dynamic> plans = jsonDecode(response.body);
      return plans.cast<Map<String, dynamic>>();
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<Map<String, dynamic>> verifyEsewaPayment(Map<String, dynamic> payload) async {
    final token = await getToken();
    final orgIdStr = await _storage.read(key: 'org_id');
    final orgId = int.tryParse(orgIdStr ?? '0') ?? 0;
    
    payload['org_id'] = orgId;

    final response = await http.post(
      Uri.parse('$baseUrl/users/subscription/esewa'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }


  Future<bool> verifyToken() async {
    final token = await getToken();
    if (token == null) return false;

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/users/me'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>?> getCurrentSubscription() async {
    final token = await getToken();
    if (token == null) return null;

    final response = await http.get(
      Uri.parse('$baseUrl/users/me/subscription'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final body = response.body;
      if (body == 'null' || body.isEmpty) return null;
      return jsonDecode(body);
    } else {
      _checkUnauthorized(response.statusCode);
      return null;
    }
  }

  Future<void> deleteAccount() async {
    final token = await getToken();
    if (token == null) throw ApiException.message('Not authenticated');

    final response = await http.delete(
      Uri.parse('$baseUrl/users/me'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      await logout();
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }

  Future<int?> getMostPopularPlanId() async {
    final token = await getToken();
    if (token == null) return null;

    final response = await http.get(
      Uri.parse('$baseUrl/users/plans/most-popular'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      final body = jsonDecode(response.body);
      return body['plan_id'] as int?;
    } else {
      _checkUnauthorized(response.statusCode);
      return null;
    }
  }

  Future<String?> resendVerificationEmail() async {
    final token = await getToken();
    if (token == null) return null;
    
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/send-email-verification'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['verification_token'] as String?;
      }
    } catch (_) {
      // Background request, ignore errors
    }
    return null;
  }

  /// Fetches the eSewa SDK credentials from the backend.
  /// Returns a map with keys: `client_id`, `secret_id`, `environment`.
  Future<Map<String, dynamic>> getEsewaConfig() async {
    final token = await getToken();
    if (token == null) throw ApiException.message('Not authenticated');

    final response = await http.get(
      Uri.parse('$baseUrl/users/esewa-config'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $token',
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      _checkUnauthorized(response.statusCode);
      throw ApiException(response.statusCode, response.body);
    }
  }

}

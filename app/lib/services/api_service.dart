import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  // static const String baseUrl = 'http://10.0.2.2:8000'; 
  static const String baseUrl = 'http://127.0.0.1:8000'; 
  final _storage = const FlutterSecureStorage();

  Future<Map<String, dynamic>> register(String name, String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'full_name': name,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to register: ${response.body}');
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
      } else {
        await _storage.write(key: 'token', value: data['access_token']);
      }
      return data;
    } else {
      throw Exception('Failed to login: ${response.body}');
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
      return null;
    }
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'token');
  }

  Future<void> logout() async {
    await _storage.delete(key: 'token');
    await _storage.delete(key: 'user_name');
    await _storage.delete(key: 'user_email');
  }
}

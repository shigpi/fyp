import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  // Use 10.0.2.2 for Android emulator, localhost for iOS simulator
  // static const String baseUrl = 'http://10.0.2.2:8000'; 
  static const String baseUrl = 'https://full-classic-terrier.ngrok-free.app'; 
  final _storage = const FlutterSecureStorage();

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
        if (data['user']['organization_id'] != null) {
          await _storage.write(key: 'org_id', value: data['user']['organization_id'].toString());
        }
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
      throw Exception('Failed to transcribe: ${response.body}');
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
    final List<dynamic> plans = jsonDecode(response.body);
    if (response.statusCode == 200) {
      return plans.cast<Map<String, dynamic>>();
    } else {
      throw Exception('Failed to get plans: ${response.body}');
    }
  }


}

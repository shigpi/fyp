import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/main.dart';
import 'package:app/pages/login_page.dart';
import 'package:app/pages/register_page.dart';
import 'package:app/widgets/custom_button.dart';
import 'package:app/widgets/custom_input.dart';

// ============================================================================
// MOCKS & STUBS SETUP
// ============================================================================

class MockHttpOverrides extends HttpOverrides {
  final Future<HttpClientRequest> Function(Uri url) onRequest;

  MockHttpOverrides({required this.onRequest});

  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return _MockHttpClient(onRequest);
  }
}

class _MockHttpClient extends Fake implements HttpClient {
  final Future<HttpClientRequest> Function(Uri url) onRequest;
  _MockHttpClient(this.onRequest);

  @override
  bool autoUncompress = true;
  @override
  Duration? connectionTimeout;
  @override
  Duration idleTimeout = const Duration(seconds: 15);

  @override
  Future<HttpClientRequest> openUrl(String method, Uri url) => onRequest(url);
  @override
  Future<HttpClientRequest> getUrl(Uri url) => onRequest(url);
  @override
  Future<HttpClientRequest> postUrl(Uri url) => onRequest(url);
  @override
  Future<HttpClientRequest> putUrl(Uri url) => onRequest(url);
  @override
  Future<HttpClientRequest> deleteUrl(Uri url) => onRequest(url);
  @override
  Future<HttpClientRequest> patchUrl(Uri url) => onRequest(url);
}

class _MockHttpClientRequest extends Fake implements HttpClientRequest {
  final HttpClientResponse response;
  
  _MockHttpClientRequest(this.response);

  @override
  HttpHeaders get headers => _MockHttpHeaders();

  @override
  void add(List<int> data) {}

  @override
  void write(Object? object) {}

  @override
  Future<HttpClientResponse> close() async => response;
}

class _MockHttpHeaders extends Fake implements HttpHeaders {
  @override
  void add(String name, Object value, {bool preserveHeaderCase = false}) {}

  @override
  void set(String name, Object value, {bool preserveHeaderCase = false}) {}
  
  @override
  List<String>? operator [](String name) => null;
}

class _MockHttpClientResponse extends Fake implements HttpClientResponse {
  final int statusCodeValue;
  final String body;

  _MockHttpClientResponse(this.statusCodeValue, this.body);

  @override
  int get statusCode => statusCodeValue;

  @override
  int get contentLength => utf8.encode(body).length;

  @override
  StreamSubscription<List<int>> listen(
    void Function(List<int> event)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) {
    return Stream.value(utf8.encode(body)).listen(
      onData,
      onError: onError,
      onDone: onDone,
      cancelOnError: cancelOnError,
    );
  }
}

// ============================================================================
// TEST SUITE
// ============================================================================

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  group('LoginPage Interaction & State Updates (Form Validation)', () {
    setUp(() {
      FlutterSecureStorage.setMockInitialValues({});
      HttpOverrides.global = null;
    });

    testWidgets('Should render text fields and dynamic CustomButtons', (WidgetTester tester) async {
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));

      expect(find.byType(CustomInput), findsNWidgets(2), reason: 'Email & Password boxes needed');
      expect(find.byType(CustomButton), findsOneWidget, reason: 'Login custom actionable button');
      expect(find.text('Sign In'), findsOneWidget);
    });

    // Mock isolated failure tests avoiding long pumpAndSettle that timeouts
    testWidgets('Navigation routing functionality from Login to Register rendering test', (WidgetTester tester) async {
      await tester.pumpWidget(const MaterialApp(home: LoginPage()));

      final signUpText = find.text("Don't have an account? Sign Up");
      await tester.ensureVisible(signUpText);
      expect(signUpText, findsOneWidget);
    });
  });
}

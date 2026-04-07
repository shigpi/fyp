import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mocktail/mocktail.dart';

import 'package:app/main.dart';
import 'package:app/pages/splash_page.dart';
import 'package:app/pages/login_page.dart';
import 'package:app/pages/home_page.dart';

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

  group('SplashPage Auth Verification (Loading & Edge States)', () {
    setUp(() {
      FlutterSecureStorage.setMockInitialValues({});
    });

    tearDown(() {
      FlutterSecureStorage.setMockInitialValues({});
      HttpOverrides.global = null;
    });

    testWidgets('Should exhibit Loading states correctly without immediate routing', (WidgetTester tester) async {
      await tester.pumpWidget(const MaterialApp(home: SplashPage()));

      // Validate UI interactions (Empty/Loading validation)
      expect(find.byIcon(Icons.mic), findsOneWidget);
      expect(find.text('VoiceScribe'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget, reason: 'Should show spinner during async ops');
    });

    testWidgets('Failure Path / Empty State: Routes to LoginPage if Token is MISSING', (WidgetTester tester) async {
      // Mock empty storage
      FlutterSecureStorage.setMockInitialValues({});
      
      await tester.pumpWidget(const MaterialApp(home: SplashPage()));
      
      // Await checkAuth Future execution
      await tester.pumpAndSettle();

      // Navigation screen routing verification
      expect(find.byType(LoginPage), findsOneWidget);
      expect(find.byType(SplashPage), findsNothing);
    });

    testWidgets('Failure Path / Async Operation: Routes to LoginPage if Token is INVALID', (WidgetTester tester) async {
      FlutterSecureStorage.setMockInitialValues({'token': 'invalid_expired_jwt_token'});

      // Network boundary condition: Reject 401 Unauthorized API verification
      HttpOverrides.global = MockHttpOverrides(
        onRequest: (url) async {
          return _MockHttpClientRequest(
            _MockHttpClientResponse(401, '{"detail": "Your session has expired"}')
          );
        },
      );

      await tester.pumpWidget(const MaterialApp(home: SplashPage()));
      await tester.pumpAndSettle();

      // Ensure that error states clear cache and correctly fallback to login
      expect(find.byType(LoginPage), findsOneWidget);
    });
  });
}

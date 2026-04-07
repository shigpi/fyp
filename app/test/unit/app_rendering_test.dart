import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/main.dart';

void main() {
  setUpAll(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  group('MyApp Root Rendering Tests', () {
    testWidgets('Should validate root widget rendering, Theme changes, and App Key parameters', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      await tester.pump(); // Use pump instead of pumpAndSettle for Splash animations

      final materialAppFinder = find.byType(MaterialApp);
      expect(materialAppFinder, findsOneWidget, reason: 'Root application must contain MaterialApp');

      final MaterialApp app = tester.widget(materialAppFinder);
      expect(app.title, 'VoiceScribe', reason: 'Title should match defined app name');
      expect(app.debugShowCheckedModeBanner, false, reason: 'Debug banner must be disabled for production UX');
      
      // Theme Rendering Validation (Dark Mode Requirements)
      expect(app.theme?.brightness, Brightness.dark, reason: 'App requires dark UI rendering');
      expect(app.theme?.scaffoldBackgroundColor, Colors.black, reason: 'True black needed for OLED optimization');
      expect(app.navigatorKey, isNotNull, reason: 'Global navigator state key must be attached');
    });

    testWidgets('Null safety/Empty edge states when Navigator Key is queried early', (WidgetTester tester) async {
      await tester.pumpWidget(const MyApp());
      expect(navigatorKey.currentState, isNotNull, reason: 'Navigator state should not be null post-rendering');
    });
  });
}

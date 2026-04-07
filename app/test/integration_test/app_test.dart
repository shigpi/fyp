import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:app/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  // Note: For full E2E testing with the backend, you'll want to 
  // ensure the API is running or have an environment toggle for 
  // integration testing. We'll verify basic widget state logic in the app.

  group('end-to-end app level integration tests', () {
    testWidgets('App loads and starts at splash page correctly', (tester) async {
      app.main();
      await tester.pumpAndSettle(); // Wait for Flutter to finish building

      // This expects that the SplashPage logic will eventually
      // load and direct the user to the LoginPage since we start from fresh local stoarage.
      expect(find.text('VoiceScribe'), findsOneWidget);
      expect(find.text('Sign In'), findsOneWidget);
    });
  });
}

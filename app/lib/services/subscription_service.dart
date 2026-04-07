import 'package:app/services/api_service.dart';

class SubscriptionState {
  final List<Map<String, dynamic>> plans;
  final Map<String, dynamic>? activeSubscription;
  final bool emailVerified;
  final int? mostPopularPlanId;

  SubscriptionState({
    required this.plans,
    this.activeSubscription,
    required this.emailVerified,
    this.mostPopularPlanId,
  });
}

class SubscriptionService {
  final ApiService _apiService = ApiService();

  Future<SubscriptionState> loadSubscriptionData() async {
    final futures = await Future.wait([
      _apiService.getPlans(),
      _apiService.getCurrentSubscription(),
      _apiService.getUserProfile(),
      _apiService.getMostPopularPlanId(),
    ]);

    final plans = (futures[0] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final activeSubscription = futures[1] as Map<String, dynamic>?;
    final userProfile = futures[2] as Map<String, dynamic>?;
    final mostPopularPlanId = futures[3] as int?;

    final emailVerified = userProfile?['email_verified'] ?? false;

    return SubscriptionState(
      plans: plans,
      activeSubscription: activeSubscription,
      emailVerified: emailVerified,
      mostPopularPlanId: mostPopularPlanId,
    );
  }
}

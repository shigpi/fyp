import 'package:app/widgets/custom_button.dart';
import 'package:flutter/material.dart';
import 'package:app/services/api_service.dart';
import 'package:app/services/subscription_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:esewa_flutter_sdk/esewa_config.dart';
import 'package:esewa_flutter_sdk/esewa_flutter_sdk.dart';
import 'package:esewa_flutter_sdk/esewa_payment.dart';
import 'package:esewa_flutter_sdk/esewa_payment_success_result.dart';
import 'package:url_launcher/url_launcher.dart';

class SubscriptionPage extends StatefulWidget {
  const SubscriptionPage({super.key});

  @override
  State<SubscriptionPage> createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends State<SubscriptionPage> {
  String? _selectedPlan = 'free';
  List<Map<String, dynamic>> _plans = [];
  Map<String, dynamic>? _activeSubscription;
  bool _emailVerified = false;
  int? _mostPopularPlanId;
  bool _loading = true;
  bool _isYearly = false;
  final SubscriptionService _subService = SubscriptionService();

  @override
  void initState() {
    super.initState();
    _loadPlans();
  }

  Future<void> _loadPlans() async {
    try {
      final state = await _subService.loadSubscriptionData();

      setState(() {
        _plans = state.plans;
        _activeSubscription = state.activeSubscription;
        _emailVerified = state.emailVerified;
        _mostPopularPlanId = state.mostPopularPlanId;
        
        if (_activeSubscription != null && _activeSubscription!['status'] == 'active') {
          _selectedPlan = _activeSubscription!['plan_id']?.toString();
        } else {
          _selectedPlan = null;
        }
        
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load plans: $e')),
      );
    }
  }

  void _initEsewaPayment(Map<String, dynamic> plan) async {
    final storage = const FlutterSecureStorage();

    // Read org_id from secure storage
    final orgId = int.tryParse(await storage.read(key: 'org_id') ?? '');
    if (orgId == null) {
      debugPrint("No organization selected. Cannot proceed with payment.");
      return;
    }

    // Fetch eSewa SDK credentials securely from the backend
    final Map<String, dynamic> esewaConfig;
    try {
      esewaConfig = await ApiService().getEsewaConfig();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load payment config: $e')),
      );
      return;
    }

    final String clientId = esewaConfig['client_id'] ?? '';
    final String secretId = esewaConfig['secret_id'] ?? '';
    final bool isTest = (esewaConfig['environment'] ?? 'test') == 'test';

    if (clientId.isEmpty || secretId.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Payment configuration unavailable. Please try again later.')),
      );
      return;
    }

    try {
      // Prepare price safely
      final rawPrice = _isYearly ? plan['price_year'] : plan['price_month'];
      final price = double.tryParse(rawPrice.toString()) ?? 0;

      // Use non-numeric unique productId to satisfy eSewa SDK
      final uniqueProductId =
          "PLAN_${plan['id']}_${DateTime.now().millisecondsSinceEpoch}";

      EsewaFlutterSdk.initPayment(
        esewaConfig: EsewaConfig(
          clientId: clientId,
          secretId: secretId,
          environment: isTest ? Environment.test : Environment.live,
        ),
        esewaPayment: EsewaPayment(
          productId: uniqueProductId,
          productName: plan['name'].toString(),
          productPrice: price.toInt().toString(), // Integer string required
          callbackUrl: "https://example.com/callback", // Dummy URL for SDK interception
        ),
        onPaymentSuccess: (EsewaPaymentSuccessResult data) async {
          debugPrint(":::SUCCESS::: productId=${data.productId}");
          try {
            setState(() => _loading = true);

            final payload = {
              'org_id': orgId,
              'plan_id': int.tryParse(plan['id'].toString()) ?? 0,
              'type': _isYearly ? 'yearly' : 'monthly',
              'product_id': data.productId,
              'product_name': data.productName,
              'total_amount': data.totalAmount,
              'environment': data.environment,
              'code': data.code,
              'merchant_name': data.merchantName,
              'message': data.message,
              'date': data.date,
              'status': data.status,
              'ref_id': data.refId,
            };

            await ApiService().verifyEsewaPayment(payload);

            if (!mounted) return;

            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                  content:
                      Text('Payment Successful! Subscription activated.')),
            );

            _loadPlans();
          } catch (e) {
            if (!mounted) return;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Verification failed: $e')),
            );
            setState(() => _loading = false);
          }
        },
        onPaymentFailure: (data) {
          debugPrint(":::FAILURE::: ${data.toString()}");
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Payment Failed: ${data.message}')),
          );
        },
        onPaymentCancellation: (data) {
          debugPrint(":::CANCELLATION::: ${data.toString()}");
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Payment Cancelled.')),
          );
        },
      );
    } catch (e) {
      debugPrint('EXCEPTION: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Header
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.of(context).pop(),
                    child: Row(
                      children: const [
                        Icon(Icons.arrow_back, size: 16, color: Color(0xFFA3A3A3)),
                        SizedBox(width: 6),
                        Text(
                          'Back',
                          style: TextStyle(
                            color: Color(0xFFA3A3A3),
                            fontSize: 14,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 16),
                  const Text(
                    'Subscription Plans',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: Color(0xFF171717)),

            if (!_loading && !_emailVerified)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
                color: const Color(0xFFB1430F), // Muted dark orange banner
                child: Column(
                  children: [
                    const Text(
                      'Verify your email to subscribe.',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    CustomButton(
                      text: 'Verify Email',
                      backgroundColor: Colors.white,
                      textColor: Colors.black,
                      onPressed: () async {
                        try {
                          final verificationToken = await ApiService().resendVerificationEmail();
                          if (verificationToken != null) {
                            final Uri url = Uri.parse('${ApiService.baseUrl}/verify-otp?token=$verificationToken&app=flutter');
                            if (!await launchUrl(url, mode: LaunchMode.inAppWebView)) {
                              debugPrint('Could not launch $url');
                            }
                          } else {
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Failed to retrieve verification token')),
                            );
                          }
                        } catch (e) {
                          if (!mounted) return;
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Failed to send verification: $e')),
                          );
                        }
                      },
                    ),
                  ],
                ),
              ),

            // Plans List
            Expanded(
              child: _loading
                ? const Center(child: CircularProgressIndicator())
                : Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 16.0),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              'Monthly',
                              style: TextStyle(
                                color: !_isYearly ? Colors.white : const Color(0xFF737373),
                                fontWeight: !_isYearly ? FontWeight.w600 : FontWeight.normal,
                              ),
                            ),
                            const SizedBox(width: 8),
                            Switch(
                              value: _isYearly,
                              onChanged: (val) => setState(() => _isYearly = val),
                              activeColor: const Color(0xFF60A83A),
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Yearly',
                              style: TextStyle(
                                color: _isYearly ? Colors.white : const Color(0xFF737373),
                                fontWeight: _isYearly ? FontWeight.w600 : FontWeight.normal,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: ListView.builder(
                          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                          itemCount: _plans.length,
                          itemBuilder: (context, index) {
                            final plan = _plans[index];
                            final planId = plan['id']?.toString() ?? '';
                            final planIdInt = int.tryParse(planId);
                            final isPopular = planIdInt != null && _mostPopularPlanId == planIdInt;
                            
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 24),
                              child: _buildPlanCard(
                                id: planId,
                                name: plan['name'],
                                price: _isYearly ? 'NRs.${plan['price_year']}' : 'NRs.${plan['price_month']}',
                                period: _isYearly ? 'per year' : 'per month',
                                features: ['${plan['token_quota']} minutes/month'],
                                isPopular: isPopular,
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlanCard({
    required String id,
    required String name,
    required String price,
    required String period,
    required List<String> features,
    bool isPopular = false,
  }) {
    final intPlanId = int.tryParse(id);
    final hasActiveSub = _activeSubscription != null && _activeSubscription!['status'] == 'active';
    final isActivePlan = hasActiveSub && _activeSubscription!['plan_id'] == intPlanId;
    final isSelected = _selectedPlan == id;
    final canSubscribe = _emailVerified && !hasActiveSub;

    // Determine border color
    Color borderColor = const Color(0xFF262626);
    if (isActivePlan) {
      borderColor = const Color(0xFF60A83A); // Green for active
    } else if (isSelected) {
      borderColor = Colors.white; // White for currently selecting but not paid
    }

    // Determine button text and state
    String btnText;
    if (isActivePlan) {
      btnText = 'Current Plan';
    } else if (isSelected) {
      btnText = 'Pay with eSewa';
    } else {
      btnText = 'Select Plan';
    }

    VoidCallback? onPressed;
    if (isActivePlan) {
      onPressed = null;
    } else if (!hasActiveSub) {
      if (_emailVerified) {
        onPressed = () {
          if (isSelected) {
            final selectedPlanDetails = _plans.firstWhere(
                (p) => p['id'].toString() == id,
                orElse: () => <String, dynamic>{});
            if (selectedPlanDetails.isNotEmpty) {
              _initEsewaPayment(selectedPlanDetails);
            }
          } else {
            setState(() => _selectedPlan = id);
          }
        };
      } else {
        onPressed = null; // Disabled if email not verified
      }
    } else {
      onPressed = null; // Disabled if they have an active sub on a different plan
    }

    // Prepare badges
    final badges = <Widget>[];
    if (isActivePlan) {
      badges.add(
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: const Color(0xFF60A83A),
            borderRadius: BorderRadius.circular(100),
          ),
          child: const Text(
            'Current Plan',
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      );
    }
    if (isPopular) {
      if (badges.isNotEmpty) badges.add(const SizedBox(width: 8));
      badges.add(
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(100),
          ),
          child: const Text(
            'Most Popular',
            style: TextStyle(
              color: Colors.black,
              fontSize: 10,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF171717), // Neutral 900
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: borderColor,
          width: isActivePlan || isSelected ? 2 : 1,
        ),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          if (badges.isNotEmpty)
            Positioned(
              top: -26,
              left: 0,
              right: 0,
              child: Center(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: badges,
                ),
              ),
            ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 4),
              Row(
                crossAxisAlignment: CrossAxisAlignment.baseline,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    price,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w600,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '/$period',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF737373),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              ...features.map((feature) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.check, size: 16, color: Colors.white),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            feature,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Color(0xFFA3A3A3),
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )),
              const SizedBox(height: 16),
              CustomButton(
                text: btnText,
                onPressed: onPressed,
                backgroundColor: isSelected && canSubscribe ? const Color(0xFF60A83A) : const Color(0xFF262626), 
                textColor: Colors.white,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

import 'package:app/widgets/custom_button.dart';
import 'package:flutter/material.dart';
import 'package:app/services/api_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:esewa_flutter_sdk/esewa_config.dart';
import 'package:esewa_flutter_sdk/esewa_flutter_sdk.dart';
import 'package:esewa_flutter_sdk/esewa_payment.dart';
import 'package:esewa_flutter_sdk/esewa_payment_success_result.dart';
class SubscriptionPage extends StatefulWidget {
  const SubscriptionPage({super.key});

  @override
  State<SubscriptionPage> createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends State<SubscriptionPage> {
  String _selectedPlan = 'free';
  List<Map<String, dynamic>>? _plans = [];
  bool _loading = true;
  bool _isYearly = false;

  @override
  void initState() {
    super.initState();
    _loadPlans();
  }

  Future<void> _loadPlans() async {
    try {
      final plans = await ApiService().getPlans();
      final currentSub = await ApiService().getCurrentSubscription();
      setState(() {
        _plans = plans;
        if (currentSub != null && currentSub['plan_id'] != null) {
          _selectedPlan = currentSub['plan_id'].toString();
        }
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load plans: $e')),
      );
    }
  }

  void _initEsewaPayment(Map<String, dynamic> plan) async {
    final storage = FlutterSecureStorage();

    // Read org_id from secure storage
    final orgId = int.tryParse(await storage.read(key: 'org_id') ?? '');
    if (orgId == null) {
      debugPrint("No organization selected. Cannot proceed with payment.");
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
          clientId:
              'JB0BBQ4aD0UqIThFJwAKBgAXEUkEGQUBBAwdOgABHD4DChwUAB0R',
          secretId:
              'BhwIWQQADhIYSxILExMcAgFXFhcOBwAKBgAXEQ==',
          environment: Environment.test, // Use production only for live
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
                          itemCount: _plans?.length,
                          itemBuilder: (context, index) {
                            final plan = _plans?[index];
                            plan?['popular'] = true;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: _buildPlanCard(
                                id: plan?['id']?.toString() ?? '',
                                name: plan?['name'],
                                price: _isYearly ? 'NRs.${plan?['price_year']}' : 'NRs.${plan?['price_month']}',
                                period: _isYearly ? 'per year' : 'per month',
                                features: ['${plan?['token_quota']} minutes/month'],

                                color: plan?['popular'] == true // TODO: change color based on plan
                                    ? Colors.white
                                    : const Color(0xFF525252),
                                isPopular: plan?['popular'] ?? false,
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
    required Color color,
    bool isPopular = false,
  }) {
    final isSelected = _selectedPlan == id;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF171717), // Neutral 900
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isSelected ? color : const Color(0xFF262626),
          width: isSelected ? 2 : 1,
        ),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          if (isPopular)
            Positioned(
              top: -26,
              left: 0,
              right: 0,
              child: Center(
                child: Container(
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
                text: isSelected ? 'Pay with eSewa' : 'Select Plan',
                onPressed: () {
                  if (isSelected) {
                    final selectedPlanDetails = _plans?.firstWhere(
                        (p) => p['id'].toString() == id,
                        orElse: () => <String, dynamic>{});
                    if (selectedPlanDetails != null && selectedPlanDetails.isNotEmpty) {
                      _initEsewaPayment(selectedPlanDetails);
                    }
                  } else {
                    setState(() => _selectedPlan = id);
                  }
                },
                backgroundColor: isSelected ? const Color(0xFF60A83A) : const Color(0xFF262626), // eSewa green color when selected
                textColor: Colors.white,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

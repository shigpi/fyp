import 'package:app/widgets/custom_button.dart';
import 'package:flutter/material.dart';

class SubscriptionPage extends StatefulWidget {
  const SubscriptionPage({super.key});

  @override
  State<SubscriptionPage> createState() => _SubscriptionPageState();
}

class _SubscriptionPageState extends State<SubscriptionPage> {
  String _selectedPlan = 'free';

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
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  _buildPlanCard(
                    id: 'free',
                    name: 'Free',
                    price: '\$0',
                    period: 'forever',
                    features: [
                      '10 minutes of transcription per month',
                      'Basic language support',
                      'Standard quality',
                      'Export as text'
                    ],
                    color: const Color(0xFF525252),
                  ),
                  const SizedBox(height: 12),
                  _buildPlanCard(
                    id: 'premium',
                    name: 'Premium',
                    price: '\$9.99',
                    period: 'per month',
                    features: [
                      '5 hours of transcription per month',
                      'All languages supported',
                      'High quality transcription',
                      'Export as text, PDF, DOCX',
                      'Priority processing',
                      'Speaker identification'
                    ],
                    color: Colors.white,
                    isPopular: true,
                  ),
                  const SizedBox(height: 12),
                  _buildPlanCard(
                    id: 'ultra',
                    name: 'Ultra',
                    price: '\$19.99',
                    period: 'per month',
                    features: [
                      'Unlimited transcription',
                      'All languages supported',
                      'Highest quality transcription',
                      'All export formats',
                      'Priority processing',
                      'Speaker identification',
                      'Custom vocabulary',
                      'API access',
                      '24/7 support'
                    ],
                    color: const Color(0xFF525252),
                  ),
                  const SizedBox(height: 12),
                  _buildPlanCard(
                    id: 'student',
                    name: 'Student',
                    price: '\$4.99',
                    period: 'per month',
                    features: [
                      '3 hours of transcription per month',
                      'All languages supported',
                      'High quality transcription',
                      'Export as text, PDF',
                      'Valid student ID required'
                    ],
                    color: const Color(0xFF525252),
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
                text: isSelected ? 'Current Plan' : 'Select Plan',
                onPressed: () => setState(() => _selectedPlan = id),
                backgroundColor: isSelected ? Colors.white : const Color(0xFF262626),
                textColor: isSelected ? Colors.black : Colors.white,
              ),
            ],
          ),
        ],
      ),
    );
  }
}

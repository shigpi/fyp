import 'package:app/widgets/custom_button.dart';
import 'package:app/widgets/custom_input.dart';
import 'package:app/services/api_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _phoneController = TextEditingController();
  final _dobController = TextEditingController();

  final _apiService = ApiService();

  Future<void> _handleRegister() async {
    if (_passwordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match')),
      );
      return;
    }

    try {
      await _apiService.register(
        _nameController.text,
        _emailController.text,
        _passwordController.text,
        phone: _phoneController.text,
        dob: _dobController.text,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration successful! Please login.')),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString())),
        );
      }
    }
  }

  void _showDatePicker() {
    showCupertinoModalPopup(
      context: context,
      builder: (_) => Container(
        height: 300,
        color: const Color(0xFF171717),
        child: Column(
          children: [
            Container(
              height: 48,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  CupertinoButton(
                    padding: EdgeInsets.zero,
                    child: const Text('Done', style: TextStyle(color: Colors.blue)),
                    onPressed: () => Navigator.of(context).pop(),
                  )
                ],
              ),
            ),
            Expanded(
              child: CupertinoTheme(
                data: const CupertinoThemeData(
                  textTheme: CupertinoTextThemeData(
                    dateTimePickerTextStyle: TextStyle(color: Colors.white, fontSize: 20),
                  ),
                ),
                child: CupertinoDatePicker(
                  mode: CupertinoDatePickerMode.date,
                  initialDateTime: DateTime(2000, 1, 1),
                  maximumDate: DateTime.now(),
                  onDateTimeChanged: (DateTime newDate) {
                    setState(() {
                      _dobController.text = "${newDate.year}-${newDate.month.toString().padLeft(2, '0')}-${newDate.day.toString().padLeft(2, '0')}";
                    });
                  },
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _phoneController.dispose();
    _dobController.dispose();
    super.dispose();
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
                ],
              ),
            ),

            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Logo and Title
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: const Color(0xFF171717), // Neutral 900
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFF262626)),
                      ),
                      child: const Icon(Icons.mic, color: Colors.white, size: 24),
                    ),
                    const SizedBox(height: 16),
                    const Text(
                      'Create Account',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Join VoiceScribe today',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFFA3A3A3), // Neutral 400
                      ),
                    ),
                    const SizedBox(height: 32),

                    // Form
                    CustomInput(
                      controller: _nameController,
                      hintText: 'Full Name',
                    ),
                    const SizedBox(height: 10),
                    CustomInput(
                      controller: _emailController,
                      hintText: 'Email',
                      keyboardType: TextInputType.emailAddress,
                    ),
                    const SizedBox(height: 10),
                    CustomInput(
                      controller: _phoneController,
                      hintText: 'Phone Number (Optional)',
                      keyboardType: TextInputType.phone,
                    ),
                    const SizedBox(height: 10),
                    GestureDetector(
                      onTap: _showDatePicker,
                      child: AbsorbPointer(
                        child: CustomInput(
                          controller: _dobController,
                          hintText: 'Date of Birth (YYYY-MM-DD)',
                          keyboardType: TextInputType.datetime,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    CustomInput(
                      controller: _passwordController,
                      hintText: 'Password',
                      obscureText: true,
                    ),
                    const SizedBox(height: 10),
                    CustomInput(
                      controller: _confirmPasswordController,
                      hintText: 'Confirm Password',
                      obscureText: true,
                    ),
                    const SizedBox(height: 12),
                    CustomButton(
                      text: 'Create Account',
                      onPressed: _handleRegister,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

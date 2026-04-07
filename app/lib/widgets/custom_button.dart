import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final bool isOutline;
  final Color? backgroundColor;
  final Color? textColor;

  const CustomButton({
    super.key,
    required this.text,
    required this.onPressed,
    this.isOutline = false,
    this.backgroundColor,
    this.textColor,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        // Allow disabled state when onPressed is null
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: isOutline
              ? Colors.transparent
              : (backgroundColor ?? Colors.white),
          foregroundColor:
              textColor ?? (isOutline ? Colors.white : Colors.black),
          elevation: 0,
          side: isOutline ? const BorderSide(color: Colors.white) : null,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          disabledBackgroundColor: const Color(0xFF333333),
          disabledForegroundColor: const Color(0xFF737373),
        ),
        child: Text(
          text,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }
}

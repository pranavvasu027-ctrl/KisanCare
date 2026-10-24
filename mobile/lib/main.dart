import 'package:flutter/material.dart';
import 'app/theme.dart';
import 'features/home/home_screen.dart';

void main() {
  runApp(const KisanCareApp());
}

class KisanCareApp extends StatelessWidget {
  const KisanCareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KisanCare',
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

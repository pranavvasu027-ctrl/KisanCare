import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class DecisionSupportScreen extends StatelessWidget {
  const DecisionSupportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Decision Support (Auth Required)')),
      body: const EmptyStateWidget(
        icon: Icons.lock_outline,
        title: 'Authentication Required',
        message: 'The Decision Engine requires a valid Supabase session and a populated Farm Digital Twin. Please complete the backend authentication setup (Phase 8/9).',
      ),
    );
  }
}

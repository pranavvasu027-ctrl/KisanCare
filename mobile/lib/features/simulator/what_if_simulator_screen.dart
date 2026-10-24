import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class WhatIfSimulatorScreen extends StatelessWidget {
  const WhatIfSimulatorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('What-If Simulator')),
      body: const EmptyStateWidget(
        icon: Icons.science,
        title: 'Simulator Not Connected',
        message: 'API integration for the what-if simulator is pending.',
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class MyFarmScreen extends StatelessWidget {
  const MyFarmScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Farm')),
      body: const EmptyStateWidget(
        icon: Icons.landscape,
        title: 'Farm Details Unavailable',
        message: 'Detailed farm management will be implemented soon.',
      ),
    );
  }
}

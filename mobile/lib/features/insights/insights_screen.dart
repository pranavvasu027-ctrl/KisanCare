import 'package:flutter/material.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  final List<Map<String, dynamic>> models = const [
    {'name': 'Crop Recommendation', 'status': 'Available', 'icon': Icons.psychology, 'color': Colors.green},
    {'name': 'Cost Prediction', 'status': 'Auth Required', 'icon': Icons.attach_money, 'color': Colors.orange},
    {'name': 'Market Price Forecasting', 'status': 'Historical (CSV)', 'icon': Icons.insights, 'color': Colors.blue},
    {'name': 'Yield Prediction', 'status': 'Under Development', 'icon': Icons.grass, 'color': Colors.grey},
    {'name': 'Disease/Pest Risk', 'status': 'Under Development', 'icon': Icons.pest_control, 'color': Colors.grey},
    {'name': 'Irrigation Prediction', 'status': 'Under Development', 'icon': Icons.water_drop, 'color': Colors.grey},
    {'name': 'Farm Risk Assessment', 'status': 'Under Development', 'icon': Icons.warning_amber, 'color': Colors.grey},
    {'name': 'Post-Harvest Loss', 'status': 'Under Development', 'icon': Icons.inventory, 'color': Colors.grey},
    {'name': 'NPK Prediction', 'status': 'Under Development', 'icon': Icons.science, 'color': Colors.grey},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ML Model Portfolio')),
      body: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: models.length,
        itemBuilder: (context, index) {
          final model = models[index];
          return Card(
            child: ListTile(
              leading: Icon(model['icon'], color: model['color']),
              title: Text(model['name']),
              subtitle: Text(model['status']),
              trailing: model['status'] == 'Available'
                  ? const Icon(Icons.check_circle, color: Colors.green)
                  : const Icon(Icons.pending, color: Colors.grey),
            ),
          );
        },
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../core/api_client.dart';

class CostAnalysisScreen extends StatefulWidget {
  const CostAnalysisScreen({super.key});

  @override
  State<CostAnalysisScreen> createState() => _CostAnalysisScreenState();
}

class _CostAnalysisScreenState extends State<CostAnalysisScreen> {
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _result;

  // The 20-feature schema requires 14 fields from DB, 6 from user payload.
  // We only collect the user payload features here.
  final TextEditingController _sunlightCtrl = TextEditingController(text: '8.0');
  final TextEditingController _fertilizerCtrl = TextEditingController(text: '50.0');
  final TextEditingController _pesticideCtrl = TextEditingController(text: '2.0');
  final TextEditingController _seedQualityCtrl = TextEditingController(text: '8.0');
  final TextEditingController _waterEffCtrl = TextEditingController(text: '2.5');
  final TextEditingController _diseaseRiskCtrl = TextEditingController(text: '10.0');

  Future<void> _fetchCostPrediction() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _result = null;
    });

    try {
      // NOTE: This endpoint requires a valid Supabase JWT token and Digital Twin.
      // We are passing hardcoded farm_id/field_id/season_id to trigger the real RLS endpoint.
      final response = await ApiClient.post(
        '/api/v1/farms/FARM123/fields/FIELD123/seasons/SEASON123/predict-cost',
        body: {
          'sunlight_hours_day': double.tryParse(_sunlightCtrl.text),
          'fertilizer_kg_ha': double.tryParse(_fertilizerCtrl.text),
          'pesticide_litre_ha': double.tryParse(_pesticideCtrl.text),
          'seed_quality_score': double.tryParse(_seedQualityCtrl.text),
          'water_efficiency_t_per_1000m3': double.tryParse(_waterEffCtrl.text),
          'disease_pest_risk_pct': double.tryParse(_diseaseRiskCtrl.text),
        },
      );

      setState(() {
        _isLoading = false;
        if (response != null && response['status'] == 'insufficient_data') {
          _error = 'Insufficient data: \${response["warnings"]?.join(", ")}';
        } else if (response != null && response['status'] == 'success') {
          _result = response['prediction'];
        } else {
          _error = 'Failed to fetch cost prediction.';
        }
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        // This will correctly show 401 Unauthorized if auth is not set up!
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cost Analysis (Auth Required)')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'The Cost Prediction model requires 20 precise features. 14 are pulled securely from your Farm Digital Twin in Supabase. Please provide the remaining 6 operational inputs below:',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            TextField(controller: _sunlightCtrl, decoration: const InputDecoration(labelText: 'Sunlight Hours/Day')),
            TextField(controller: _fertilizerCtrl, decoration: const InputDecoration(labelText: 'Fertilizer (kg/ha)')),
            TextField(controller: _pesticideCtrl, decoration: const InputDecoration(labelText: 'Pesticide (L/ha)')),
            TextField(controller: _seedQualityCtrl, decoration: const InputDecoration(labelText: 'Seed Quality (1-10)')),
            TextField(controller: _waterEffCtrl, decoration: const InputDecoration(labelText: 'Water Efficiency (t/1000m³)')),
            TextField(controller: _diseaseRiskCtrl, decoration: const InputDecoration(labelText: 'Disease Risk %')),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : _fetchCostPrediction,
              child: _isLoading
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Predict Total Cost'),
            ),
            const SizedBox(height: 24),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.red.shade100,
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            if (_result != null) ...[
              Card(
                color: Colors.green.shade50,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      const Text('Prediction Successful', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
                      const SizedBox(height: 16),
                      Text('Total Cost: ₹\${_result!["predicted_total_cost_inr"]}', style: const TextStyle(fontSize: 18)),
                      Text('Cost per Hectare: ₹\${_result!["predicted_cost_per_hectare_inr"]}'),
                      const SizedBox(height: 8),
                      const Text('Note: Revenue and Profit cannot be calculated as Market Price models are unavailable.', style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic)),
                    ],
                  ),
                ),
              )
            ]
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../core/api_client.dart';

class CropRecommendationScreen extends StatefulWidget {
  const CropRecommendationScreen({super.key});

  @override
  State<CropRecommendationScreen> createState() => _CropRecommendationScreenState();
}

class _CropRecommendationScreenState extends State<CropRecommendationScreen> {
  bool _isLoading = false;
  String? _error;
  List<dynamic> _recommendations = [];
  List<dynamic> _filtered = [];

  // Hardcoded valid test inputs for the unauthenticated endpoint
  final String _district = 'NASHIK';
  final String _season = 'Rabi';
  final String _waterAvailability = 'Medium';

  Future<void> _fetchRecommendations() async {
    setState(() {
      _isLoading = true;
      _error = null;
      _recommendations = [];
      _filtered = [];
    });

    try {
      final response = await ApiClient.post(
        '/api/v1/crop-recommendation',
        body: {
          'district': _district,
          'season': _season,
          'water_availability': _waterAvailability,
          'top_k': 3,
        },
      );

      setState(() {
        _isLoading = false;
        if (response != null && response['status'] == 'SUCCESS') {
          _recommendations = response['recommendations'] ?? [];
          _filtered = response['filtered_candidates'] ?? [];
        } else {
          _error = 'Failed to fetch recommendations.';
        }
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crop Recommendation')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    Text('District: $_district | Season: $_season | Water: $_waterAvailability'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _isLoading ? null : _fetchRecommendations,
                      child: _isLoading
                          ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : const Text('Get Recommendations'),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.red.shade100,
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            if (_recommendations.isNotEmpty) ...[
              const Text('Top Recommendations:', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              Expanded(
                child: ListView.builder(
                  itemCount: _recommendations.length,
                  itemBuilder: (context, index) {
                    final rec = _recommendations[index];
                    return ListTile(
                      leading: CircleAvatar(child: Text('#\${rec["rank"]}')),
                      title: Text(rec['crop']),
                      subtitle: Text('Suitability Score: \${rec["predicted_area_frequency"]}'),
                    );
                  },
                ),
              ),
            ],
            if (_filtered.isNotEmpty) ...[
              const Divider(),
              const Text('Filtered Constraints:', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.orange)),
              Expanded(
                child: ListView.builder(
                  itemCount: _filtered.length,
                  itemBuilder: (context, index) {
                    final f = _filtered[index];
                    return ListTile(
                      title: Text(f['crop'], style: const TextStyle(color: Colors.grey)),
                      subtitle: Text(f['filter_reason']),
                    );
                  },
                ),
              ),
            ]
          ],
        ),
      ),
    );
  }
}

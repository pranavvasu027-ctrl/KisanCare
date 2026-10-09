import 'dart:convert';
import 'package:http/http.dart' as http;

void main() async {
  final url = Uri.parse('http://127.0.0.1:8000/api/v1/crop-recommendation');
  print('Sending POST request to: \$url');
  
  try {
    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'district': 'NASHIK',
        'season': 'Rabi',
        'water_availability': 'Medium',
        'top_k': 3
      }),
    );
    
    print('Response status: \${response.statusCode}');
    print('Response body: \${response.body}');
    
    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      print('Parsed status: \${decoded["status"]}');
      final recs = decoded['recommendations'] as List;
      print('Top Recommendation: \${recs[0]["crop"]} with score \${recs[0]["predicted_area_frequency"]}');
    }
  } catch (e) {
    print('Error: \$e');
  }
}

import '../core/api_client.dart';
import '../models/farm_digital_twin.dart';

class DigitalTwinService {
  /// Fetches a Farm Digital Twin by farm ID.
  Future<FarmDigitalTwin> getFarm(String farmId) async {
    final response = await ApiClient.get('/api/v1/digital-twin/$farmId');
    return FarmDigitalTwin.fromJson(response);
  }

  /// Optional: In a real app we might want to get a list, but current backend
  /// only supports fetching by specific ID via the dict.
  /// For the dashboard, we will fetch a specific farm.
}

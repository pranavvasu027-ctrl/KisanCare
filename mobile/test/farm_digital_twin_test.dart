import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/models/farm_digital_twin.dart';

void main() {
  group('FarmDigitalTwin Parsing', () {
    test('Parses complete JSON response successfully', () {
      final json = {
        "version": "1.0.0",
        "farm_id": "farm_001",
        "farmer_id": "farmer_001",
        "area_acres": 12.5,
        "location": {
          "state": "Maharashtra",
          "district": "Pune"
        },
        "soil": {
          "nitrogen": 45.0
        },
        "climate": {
          "temperature": 28.5
        },
        "crop": {
          "current_crop": "Tomato",
          "season": "Rabi"
        }
      };

      final twin = FarmDigitalTwin.fromJson(json);

      expect(twin.farmId, 'farm_001');
      expect(twin.areaAcres, 12.5);
      expect(twin.location.state, 'Maharashtra');
      expect(twin.soil.nitrogen, 45.0);
      expect(twin.crop.currentCrop, 'Tomato');
    });

    test('Parses empty or missing fields gracefully', () {
      final json = {
        "farm_id": "farm_missing",
        "farmer_id": "farmer_x"
      };

      final twin = FarmDigitalTwin.fromJson(json);

      expect(twin.farmId, 'farm_missing');
      expect(twin.areaAcres, null);
      expect(twin.location.state, null);
      expect(twin.soil.nitrogen, null);
    });
  });
}

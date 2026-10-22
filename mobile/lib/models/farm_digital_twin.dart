class FarmDigitalTwin {
  final String version;
  final String farmId;
  final String farmerId;
  final double? areaAcres;
  final FarmLocation location;
  final SoilState soil;
  final ClimateState climate;
  final CropState crop;
  final WaterState water;
  final FinancialState financial;
  final MarketState market;
  final Map<String, dynamic>? modelOutputs;

  FarmDigitalTwin({
    required this.version,
    required this.farmId,
    required this.farmerId,
    this.areaAcres,
    required this.location,
    required this.soil,
    required this.climate,
    required this.crop,
    required this.water,
    required this.financial,
    required this.market,
    this.modelOutputs,
  });

  factory FarmDigitalTwin.fromJson(Map<String, dynamic> json) {
    return FarmDigitalTwin(
      version: json['version'] ?? '1.0.0',
      farmId: json['farm_id'] ?? '',
      farmerId: json['farmer_id'] ?? '',
      areaAcres: (json['area_acres'] as num?)?.toDouble(),
      location: FarmLocation.fromJson(json['location'] ?? {}),
      soil: SoilState.fromJson(json['soil'] ?? {}),
      climate: ClimateState.fromJson(json['climate'] ?? {}),
      crop: CropState.fromJson(json['crop'] ?? {}),
      water: WaterState.fromJson(json['water'] ?? {}),
      financial: FinancialState.fromJson(json['financial'] ?? {}),
      market: MarketState.fromJson(json['market'] ?? {}),
      modelOutputs: json['model_outputs'] as Map<String, dynamic>?,
    );
  }
}

class FarmLocation {
  final String? state;
  final String? district;
  final double? latitude;
  final double? longitude;

  FarmLocation({this.state, this.district, this.latitude, this.longitude});

  factory FarmLocation.fromJson(Map<String, dynamic> json) {
    return FarmLocation(
      state: json['state'] as String?,
      district: json['district'] as String?,
      latitude: (json['latitude'] as num?)?.toDouble(),
      longitude: (json['longitude'] as num?)?.toDouble(),
    );
  }
}

class SoilState {
  final double? nitrogen;
  final double? phosphorus;
  final double? potassium;
  final double? ph;
  final double? organicCarbon;

  SoilState({this.nitrogen, this.phosphorus, this.potassium, this.ph, this.organicCarbon});

  factory SoilState.fromJson(Map<String, dynamic> json) {
    return SoilState(
      nitrogen: (json['nitrogen'] as num?)?.toDouble(),
      phosphorus: (json['phosphorus'] as num?)?.toDouble(),
      potassium: (json['potassium'] as num?)?.toDouble(),
      ph: (json['ph'] as num?)?.toDouble(),
      organicCarbon: (json['organic_carbon'] as num?)?.toDouble(),
    );
  }
}

class ClimateState {
  final double? temperature;
  final double? humidity;
  final double? rainfall;
  final String? weatherCondition;

  ClimateState({this.temperature, this.humidity, this.rainfall, this.weatherCondition});

  factory ClimateState.fromJson(Map<String, dynamic> json) {
    return ClimateState(
      temperature: (json['temperature'] as num?)?.toDouble(),
      humidity: (json['humidity'] as num?)?.toDouble(),
      rainfall: (json['rainfall'] as num?)?.toDouble(),
      weatherCondition: json['weather_condition'] as String?,
    );
  }
}

class CropState {
  final String? currentCrop;
  final String? season;
  final String? plantingDate;

  CropState({this.currentCrop, this.season, this.plantingDate});

  factory CropState.fromJson(Map<String, dynamic> json) {
    return CropState(
      currentCrop: json['current_crop'] as String?,
      season: json['season'] as String?,
      plantingDate: json['planting_date'] as String?,
    );
  }
}

class WaterState {
  final String? waterAvailability;
  final String? irrigationType;

  WaterState({this.waterAvailability, this.irrigationType});

  factory WaterState.fromJson(Map<String, dynamic> json) {
    return WaterState(
      waterAvailability: json['water_availability'] as String?,
      irrigationType: json['irrigation_type'] as String?,
    );
  }
}

class FinancialState {
  final double? budget;
  final double? expectedRevenue;

  FinancialState({this.budget, this.expectedRevenue});

  factory FinancialState.fromJson(Map<String, dynamic> json) {
    return FinancialState(
      budget: (json['budget'] as num?)?.toDouble(),
      expectedRevenue: (json['expected_revenue'] as num?)?.toDouble(),
    );
  }
}

class MarketState {
  final String? nearestMarket;
  final double? currentPrice;

  MarketState({this.nearestMarket, this.currentPrice});

  factory MarketState.fromJson(Map<String, dynamic> json) {
    return MarketState(
      nearestMarket: json['nearest_market'] as String?,
      currentPrice: (json['current_price'] as num?)?.toDouble(),
    );
  }
}

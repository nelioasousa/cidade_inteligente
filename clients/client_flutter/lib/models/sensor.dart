import 'reading.dart';

class Sensor {
  final int deviceId;
  final String deviceCategory;
  final bool isOnline;
  final Reading? lastReading;
  final Map<String, dynamic>? metadata;
  final List<Reading>? readings;

  Sensor({
    required this.deviceId,
    required this.deviceCategory,
    required this.isOnline,
    this.lastReading,
    this.metadata,
    this.readings,
  });

  factory Sensor.fromJson(Map<String, dynamic> json) {
    return Sensor(
      deviceId: json['deviceId'],
      deviceCategory: json['deviceCategory'],
      isOnline: json['isOnline'],
      lastReading: json['lastReading'] != null
          ? Reading.fromJson(json['lastReading'])
          : null,
      metadata: json['metadata'],
      readings: json['readings'] != null
          ? (json['readings'] as List)
                .map((reading) => Reading.fromJson(reading))
                .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deviceId': deviceId,
      'deviceCategory': deviceCategory,
      'isOnline': isOnline,
      'lastReading': lastReading?.toJson(),
      'metadata': metadata,
      'readings': readings?.map((reading) => reading.toJson()).toList(),
    };
  }
}

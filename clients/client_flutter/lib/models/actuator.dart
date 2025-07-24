class Actuator {
  final int deviceId;
  final String deviceCategory;
  final bool isOnline;
  final String lastUpdate;
  final Map<String, dynamic>? currentState;
  final Map<String, dynamic>? metadata;

  Actuator({
    required this.deviceId,
    required this.deviceCategory,
    required this.isOnline,
    required this.lastUpdate,
    this.currentState,
    this.metadata,
  });

  factory Actuator.fromJson(Map<String, dynamic> json) {
    return Actuator(
      deviceId: json['deviceId'],
      deviceCategory: json['deviceCategory'],
      isOnline: json['isOnline'],
      lastUpdate: json['lastUpdate'],
      currentState: json['currentState'],
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'deviceId': deviceId,
      'deviceCategory': deviceCategory,
      'isOnline': isOnline,
      'lastUpdate': lastUpdate,
      'currentState': currentState,
      'metadata': metadata,
    };
  }
}

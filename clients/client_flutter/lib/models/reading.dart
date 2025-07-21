class Reading {
  final String timestamp;
  final double value;

  Reading({required this.timestamp, required this.value});

  factory Reading.fromJson(Map<String, dynamic> json) {
    return Reading(
      timestamp: json['timestamp'],
      value: json['value'].toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {'timestamp': timestamp, 'value': value};
  }
}

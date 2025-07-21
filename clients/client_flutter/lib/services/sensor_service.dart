import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/sensor.dart';

class SensorService {
  static const String baseUrl = 'http://127.0.0.1:8080';

  Future<List<Sensor>> getAllSensors() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/sensors'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> jsonList = json.decode(response.body);
        return jsonList.map((json) => Sensor.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load sensors: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching sensors: $e');
    }
  }

  Future<Sensor> getSensorDetails(String category, int deviceId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/sensors/$category/$deviceId'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return Sensor.fromJson(jsonData);
      } else {
        throw Exception(
          'Failed to load sensor details: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Error fetching sensor details: $e');
    }
  }
}

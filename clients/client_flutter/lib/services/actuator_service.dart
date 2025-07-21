import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/actuator.dart';
import '../models/api_response.dart';

class ActuatorService {
  static const String baseUrl = 'http://127.0.0.1:8080';

  Future<List<Actuator>> getAllActuators() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/actuators'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> jsonList = json.decode(response.body);
        return jsonList.map((json) => Actuator.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load actuators: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching actuators: $e');
    }
  }

  Future<Actuator> getActuatorDetails(String category, int deviceId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/actuators/$category/$deviceId'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        return Actuator.fromJson(jsonData);
      } else {
        throw Exception(
          'Failed to load actuator details: ${response.statusCode}',
        );
      }
    } catch (e) {
      throw Exception('Error fetching actuator details: $e');
    }
  }

  Future<ApiResponse> updateActuator(
    String category,
    int deviceId,
    Map<String, dynamic> updateData,
  ) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl/actuators/$category/$deviceId'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(updateData),
      );

      final Map<String, dynamic> responseData = json.decode(response.body);
      return ApiResponse.fromJson(responseData, response.statusCode);
    } catch (e) {
      return ApiResponse(
        message: 'Error updating actuator: $e',
        success: false,
      );
    }
  }

  Future<ApiResponse> executeAction(
    String category,
    int deviceId,
    String action,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/actuators/$category/$deviceId'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'action': action}),
      );

      final Map<String, dynamic> responseData = json.decode(response.body);
      return ApiResponse.fromJson(responseData, response.statusCode);
    } catch (e) {
      return ApiResponse(message: 'Error executing action: $e', success: false);
    }
  }
}

import 'package:flutter/foundation.dart';
import '../models/sensor.dart';
import '../services/sensor_service.dart';

class SensorViewModel extends ChangeNotifier {
  final SensorService _sensorService = SensorService();

  List<Sensor> _sensors = [];
  Sensor? _selectedSensor;
  bool _isLoading = false;
  String? _errorMessage;

  List<Sensor> get sensors => _sensors;
  Sensor? get selectedSensor => _selectedSensor;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  Future<void> loadSensors() async {
    _setLoading(true);
    _clearError();

    try {
      _sensors = await _sensorService.getAllSensors();
      notifyListeners();
    } catch (e) {
      _setError('Erro ao carregar sensores: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadSensorDetails(String category, int deviceId) async {
    _setLoading(true);
    _clearError();

    try {
      _selectedSensor = await _sensorService.getSensorDetails(
        category,
        deviceId,
      );
      notifyListeners();
    } catch (e) {
      _setError('Erro ao carregar detalhes do sensor: $e');
    } finally {
      _setLoading(false);
    }
  }

  List<Sensor> getSensorsByCategory(String category) {
    return _sensors
        .where((sensor) => sensor.deviceCategory == category)
        .toList();
  }

  void clearSelectedSensor() {
    _selectedSensor = null;
    notifyListeners();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _errorMessage = error;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
  }
}

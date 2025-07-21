import 'package:flutter/foundation.dart';
import '../models/actuator.dart';
import '../services/actuator_service.dart';

class ActuatorViewModel extends ChangeNotifier {
  final ActuatorService _actuatorService = ActuatorService();

  List<Actuator> _actuators = [];
  Actuator? _selectedActuator;
  bool _isLoading = false;
  String? _errorMessage;
  String? _successMessage;

  List<Actuator> get actuators => _actuators;
  Actuator? get selectedActuator => _selectedActuator;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  String? get successMessage => _successMessage;

  Future<void> loadActuators() async {
    _setLoading(true);
    _clearMessages();

    try {
      _actuators = await _actuatorService.getAllActuators();
      notifyListeners();
    } catch (e) {
      _setError('Erro ao carregar atuadores: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<void> loadActuatorDetails(String category, int deviceId) async {
    _setLoading(true);
    _clearMessages();

    try {
      _selectedActuator = await _actuatorService.getActuatorDetails(
        category,
        deviceId,
      );
      notifyListeners();
    } catch (e) {
      _setError('Erro ao carregar detalhes do atuador: $e');
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> updateActuator(
    String category,
    int deviceId,
    Map<String, dynamic> updateData,
  ) async {
    _setLoading(true);
    _clearMessages();

    try {
      final response = await _actuatorService.updateActuator(
        category,
        deviceId,
        updateData,
      );

      if (response.success) {
        _setSuccess(response.message);
        await loadActuatorDetails(category, deviceId);
        return true;
      } else {
        _setError(response.message);
        return false;
      }
    } catch (e) {
      _setError('Erro ao atualizar atuador: $e');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> executeAction(
    String category,
    int deviceId,
    String action,
  ) async {
    _setLoading(true);
    _clearMessages();

    try {
      final response = await _actuatorService.executeAction(
        category,
        deviceId,
        action,
      );

      if (response.success) {
        _setSuccess(response.message);
        await loadActuatorDetails(category, deviceId);
        return true;
      } else {
        _setError(response.message);
        return false;
      }
    } catch (e) {
      _setError('Erro ao executar ação: $e');
      return false;
    } finally {
      _setLoading(false);
    }
  }

  List<Actuator> getActuatorsByCategory(String category) {
    return _actuators
        .where((actuator) => actuator.deviceCategory == category)
        .toList();
  }

  void clearSelectedActuator() {
    _selectedActuator = null;
    notifyListeners();
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _errorMessage = error;
    _successMessage = null;
    notifyListeners();
  }

  void _setSuccess(String message) {
    _successMessage = message;
    _errorMessage = null;
    notifyListeners();
  }

  void _clearMessages() {
    _errorMessage = null;
    _successMessage = null;
  }
}

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../viewmodels/sensor_viewmodel.dart';
import '../models/sensor.dart';
import 'sensor_detail_view.dart';

class SensorListView extends StatefulWidget {
  const SensorListView({super.key});

  @override
  State<SensorListView> createState() => _SensorListViewState();
}

class _SensorListViewState extends State<SensorListView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SensorViewModel>().loadSensors();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.background,
      appBar: AppBar(
        title: const Text(
          'Sensores',
          style: TextStyle(fontWeight: FontWeight.w600, color: Colors.white),
        ),
        backgroundColor: const Color(0xFF6B73FF),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 8),
            child: IconButton(
              onPressed: () {
                context.read<SensorViewModel>().loadSensors();
              },
              icon: const Icon(Icons.refresh_rounded),
              style: IconButton.styleFrom(
                backgroundColor: Colors.white.withOpacity(0.2),
                foregroundColor: Colors.white,
              ),
            ),
          ),
        ],
      ),
      body: Consumer<SensorViewModel>(
        builder: (context, viewModel, child) {
          if (viewModel.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (viewModel.errorMessage != null) {
            return Center(
              child: Container(
                margin: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Icon(
                        Icons.error_outline_rounded,
                        size: 64,
                        color: Colors.red.shade400,
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Oops! Algo deu errado',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF2C2C2C),
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      viewModel.errorMessage!,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Color(0xFF666666),
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () => viewModel.loadSensors(),
                      icon: const Icon(Icons.refresh_rounded),
                      label: const Text('Tentar Novamente'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF6B73FF),
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 24,
                          vertical: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            );
          }

          if (viewModel.sensors.isEmpty) {
            return Center(
              child: Container(
                margin: const EdgeInsets.all(32),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: Colors.grey.shade100,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Icon(
                        Icons.sensors_off_rounded,
                        size: 64,
                        color: Colors.grey.shade400,
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Nenhum sensor encontrado',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF2C2C2C),
                          ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Verifique a conexão e tente novamente',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey.shade600,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            color: const Color(0xFF6B73FF),
            onRefresh: () => viewModel.loadSensors(),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: viewModel.sensors.length,
              itemBuilder: (context, index) {
                final sensor = viewModel.sensors[index];
                return _buildSensorCard(context, sensor);
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildSensorCard(BuildContext context, Sensor sensor) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      child: Card(
        elevation: 3,
        shadowColor: Colors.black.withOpacity(0.1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => SensorDetailView(
                  category: sensor.deviceCategory,
                  deviceId: sensor.deviceId,
                ),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: sensor.isOnline
                          ? [const Color(0xFF4CAF50), const Color(0xFF66BB6A)]
                          : [const Color(0xFFFF7043), const Color(0xFFFF8A65)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: (sensor.isOnline ? Colors.green : Colors.orange)
                            .withOpacity(0.3),
                        blurRadius: 8,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Icon(
                    _getSensorIcon(sensor.deviceCategory),
                    color: Colors.white,
                    size: 28,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '${sensor.deviceCategory} #${sensor.deviceId}',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                          color: Color(0xFF2C2C2C),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          Container(
                            width: 8,
                            height: 8,
                            decoration: BoxDecoration(
                              color: sensor.isOnline
                                  ? const Color(0xFF4CAF50)
                                  : const Color(0xFFFF7043),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            sensor.isOnline ? 'Online' : 'Offline',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                              color: sensor.isOnline
                                  ? const Color(0xFF4CAF50)
                                  : const Color(0xFFFF7043),
                            ),
                          ),
                        ],
                      ),
                      if (sensor.lastReading != null) ...[
                        const SizedBox(height: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: const Color(0xFF6B73FF).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(
                            'Última leitura: ${_formatTimestamp(sensor.lastReading!.timestamp)}',
                            style: const TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF6B73FF),
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.arrow_forward_ios_rounded,
                    size: 16,
                    color: Color(0xFF666666),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  IconData _getSensorIcon(String category) {
    switch (category.toLowerCase()) {
      case 'temperature':
        return Icons.thermostat_rounded;
      case 'humidity':
        return Icons.water_drop_rounded;
      case 'pressure':
        return Icons.compress_rounded;
      case 'luminosity':
        return Icons.light_mode_rounded;
      case 'sound':
        return Icons.volume_up_rounded;
      default:
        return Icons.sensors_rounded;
    }
  }

  String _formatTimestamp(String timestamp) {
    try {
      final dateTime = DateTime.parse(timestamp);
      return '${dateTime.day.toString().padLeft(2, '0')}/${dateTime.month.toString().padLeft(2, '0')}/${dateTime.year} ${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}:${dateTime.second.toString().padLeft(2, '0')}';
    } catch (e) {
      return timestamp;
    }
  }
}

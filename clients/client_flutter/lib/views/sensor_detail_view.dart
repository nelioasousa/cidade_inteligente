import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../viewmodels/sensor_viewmodel.dart';
import '../models/reading.dart';

class SensorDetailView extends StatefulWidget {
  final String category;
  final int deviceId;

  const SensorDetailView({
    super.key,
    required this.category,
    required this.deviceId,
  });

  @override
  State<SensorDetailView> createState() => _SensorDetailViewState();
}

class _SensorDetailViewState extends State<SensorDetailView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SensorViewModel>().loadSensorDetails(
        widget.category,
        widget.deviceId,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.background,
      appBar: AppBar(
        title: Text(
          '${widget.category} #${widget.deviceId}',
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            color: Colors.white,
          ),
        ),
        backgroundColor: const Color(0xFF6B73FF),
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 8),
            child: IconButton(
              onPressed: () {
                context.read<SensorViewModel>().loadSensorDetails(
                  widget.category,
                  widget.deviceId,
                );
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
                      onPressed: () => viewModel.loadSensorDetails(
                        widget.category,
                        widget.deviceId,
                      ),
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

          final sensor = viewModel.selectedSensor;
          if (sensor == null) {
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
                      'Sensor não encontrado',
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(
                            fontWeight: FontWeight.w600,
                            color: const Color(0xFF2C2C2C),
                          ),
                    ),
                  ],
                ),
              ),
            );
          }

          return RefreshIndicator(
            color: const Color(0xFF6B73FF),
            onRefresh: () =>
                viewModel.loadSensorDetails(widget.category, widget.deviceId),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInfoCard(sensor),
                  const SizedBox(height: 16),
                  if (sensor.readings != null && sensor.readings!.isNotEmpty)
                    _buildReadingsCard(sensor.readings!),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInfoCard(sensor) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Informações do Sensor',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            _buildInfoRow('ID do Dispositivo', sensor.deviceId.toString()),
            _buildInfoRow('Categoria', sensor.deviceCategory),
            _buildInfoRow('Status', sensor.isOnline ? 'Online' : 'Offline'),
            if (sensor.lastReading != null) ...[
              const Divider(),
              Text(
                'Última Leitura',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              _buildInfoRow('Valor', sensor.lastReading!.value.toString()),
              _buildInfoRow(
                'Timestamp',
                _formatTimestamp(sensor.lastReading!.timestamp),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildReadingsCard(List<Reading> readings) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Histórico de Leituras',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 300,
              child: ListView.builder(
                itemCount: readings.length,
                itemBuilder: (context, index) {
                  final reading = readings[index];
                  return ListTile(
                    leading: CircleAvatar(child: Text('${index + 1}')),
                    title: Text('Valor: ${reading.value}'),
                    subtitle: Text(_formatTimestamp(reading.timestamp)),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
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

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../viewmodels/actuator_viewmodel.dart';

class ActuatorDetailView extends StatefulWidget {
  final String category;
  final int deviceId;

  const ActuatorDetailView({
    super.key,
    required this.category,
    required this.deviceId,
  });

  @override
  State<ActuatorDetailView> createState() => _ActuatorDetailViewState();
}

class _ActuatorDetailViewState extends State<ActuatorDetailView> {
  double _currentBrightness = 5.0;
  final TextEditingController _brightnessController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _brightnessController.text = _currentBrightness.round().toString();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ActuatorViewModel>().loadActuatorDetails(
        widget.category,
        widget.deviceId,
      );
    });
  }

  @override
  void dispose() {
    _brightnessController.dispose();
    super.dispose();
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
                context.read<ActuatorViewModel>().loadActuatorDetails(
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
      body: Consumer<ActuatorViewModel>(
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
                      onPressed: () => viewModel.loadActuatorDetails(
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

          final actuator = viewModel.selectedActuator;
          if (actuator == null) {
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
                        Icons.power_off_rounded,
                        size: 64,
                        color: Colors.grey.shade400,
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      'Atuador não encontrado',
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
                viewModel.loadActuatorDetails(widget.category, widget.deviceId),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildInfoCard(actuator),
                  const SizedBox(height: 16),
                  _buildActionsCard(context, viewModel, actuator),
                  if (viewModel.successMessage != null) ...[
                    const SizedBox(height: 16),
                    _buildSuccessMessage(viewModel.successMessage!),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildInfoCard(actuator) {
    return Card(
      elevation: 3,
      shadowColor: Colors.black.withOpacity(0.1),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF6B73FF).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(
                    Icons.info_outline_rounded,
                    color: const Color(0xFF6B73FF),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Text(
                  'Informações do Atuador',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: const Color(0xFF2C2C2C),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            _buildInfoRow('ID do Dispositivo', actuator.deviceId.toString()),
            _buildInfoRow('Categoria', actuator.deviceCategory),
            _buildInfoRow('Status', actuator.isOnline ? 'Online' : 'Offline'),
            _buildInfoRow(
              'Última Atualização',
              _formatTimestamp(actuator.lastUpdate),
            ),
            if (actuator.currentState != null) ...[
              const SizedBox(height: 16),
              Container(
                width: double.infinity,
                height: 1,
                color: Colors.grey.shade200,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Icon(
                    Icons.settings_rounded,
                    color: const Color(0xFF6B73FF),
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Estado Atual',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                      color: const Color(0xFF2C2C2C),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              ...actuator.currentState!.entries.map(
                (entry) => _buildInfoRow(entry.key, entry.value.toString()),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionsCard(
    BuildContext context,
    ActuatorViewModel viewModel,
    actuator,
  ) {
    return Card(
      elevation: 3,
      shadowColor: Colors.black.withOpacity(0.1),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF4CAF50).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.touch_app_rounded,
                    color: Color(0xFF4CAF50),
                    size: 24,
                  ),
                ),
                const SizedBox(width: 16),
                Text(
                  'Ações',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w600,
                    color: const Color(0xFF2C2C2C),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            if (widget.category.toLowerCase() == 'lamp') ...[
              _buildActionButton(
                context,
                viewModel,
                'Ligar',
                'turn_on',
                Icons.lightbulb_rounded,
                const Color(0xFF4CAF50),
              ),
              const SizedBox(height: 12),
              _buildActionButton(
                context,
                viewModel,
                'Desligar',
                'turn_off',
                Icons.lightbulb_outline_rounded,
                const Color(0xFF757575),
              ),
              const SizedBox(height: 24),
              _buildColorForm(context, viewModel),
              const SizedBox(height: 24),
              _buildBrightnessForm(context, viewModel),
            ],
            if (widget.category.toLowerCase() == 'semaphore') ...[
              _buildUpdateForm(context, viewModel),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton(
    BuildContext context,
    ActuatorViewModel viewModel,
    String label,
    String action,
    IconData icon,
    Color color,
  ) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: viewModel.isLoading
            ? null
            : () async {
                await viewModel.executeAction(
                  widget.category,
                  widget.deviceId,
                  action,
                );
              },
        icon: Icon(icon, size: 20),
        label: Text(
          label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
        ),
        style: ElevatedButton.styleFrom(
          foregroundColor: Colors.white,
          backgroundColor: color,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 2,
          shadowColor: color.withOpacity(0.3),
        ),
      ),
    );
  }

  Widget _buildUpdateForm(BuildContext context, ActuatorViewModel viewModel) {
    final redController = TextEditingController();
    final yellowController = TextEditingController();
    final greenController = TextEditingController();

    return Column(
      children: [
        TextField(
          controller: redController,
          decoration: const InputDecoration(
            labelText: 'Período Vermelho (segundos)',
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 8),
        TextField(
          controller: yellowController,
          decoration: const InputDecoration(
            labelText: 'Período Amarelo (segundos)',
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 8),
        TextField(
          controller: greenController,
          decoration: const InputDecoration(
            labelText: 'Período Verde (segundos)',
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton(
            onPressed: viewModel.isLoading
                ? null
                : () async {
                    final updateData = <String, dynamic>{};

                    if (redController.text.isNotEmpty) {
                      updateData['RedPeriod'] = double.tryParse(
                        redController.text,
                      );
                    }
                    if (yellowController.text.isNotEmpty) {
                      updateData['YellowPeriod'] = double.tryParse(
                        yellowController.text,
                      );
                    }
                    if (greenController.text.isNotEmpty) {
                      updateData['GreenPeriod'] = double.tryParse(
                        greenController.text,
                      );
                    }

                    if (updateData.isNotEmpty) {
                      await viewModel.updateActuator(
                        widget.category,
                        widget.deviceId,
                        updateData,
                      );
                    }
                  },
            child: const Text('Atualizar Configurações'),
          ),
        ),
      ],
    );
  }

  Widget _buildColorForm(BuildContext context, ActuatorViewModel viewModel) {
    final colorController = TextEditingController();

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 1,
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF6B73FF).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.palette,
                  color: Color(0xFF6B73FF),
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                'Mudar Cor',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF2C2C2C),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Cores disponíveis: white ou yellow',
            style: TextStyle(
              fontSize: 13,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: colorController,
                  decoration: const InputDecoration(
                    labelText: 'Cor',
                    hintText: 'Digite: white ou yellow',
                    prefixIcon: Icon(Icons.edit, color: Color(0xFF6B73FF)),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: viewModel.isLoading
                    ? null
                    : () async {
                        final color = colorController.text.trim().toLowerCase();
                        if (color == 'white' || color == 'yellow') {
                          await viewModel.updateActuator(
                            widget.category,
                            widget.deviceId,
                            {'Color': color},
                          );
                          colorController.clear();
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: const Text(
                                'Apenas as cores "white" e "yellow" são permitidas',
                              ),
                              backgroundColor: const Color(0xFFFF9800),
                              behavior: SnackBarBehavior.floating,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          );
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6B73FF),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
                child: const Text('Aplicar'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            children: [
              _buildColorChip(
                context,
                viewModel,
                'Branco',
                'white',
                Colors.white,
              ),
              _buildColorChip(
                context,
                viewModel,
                'Amarelo',
                'yellow',
                const Color(0xFFFFC107),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildColorChip(
    BuildContext context,
    ActuatorViewModel viewModel,
    String label,
    String colorValue,
    Color color,
  ) {
    return ActionChip(
      avatar: Container(
        width: 16,
        height: 16,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          border: Border.all(color: Colors.grey.shade300, width: 1),
        ),
      ),
      label: Text(
        label,
        style: const TextStyle(
          fontWeight: FontWeight.w500,
          color: Color(0xFF2C2C2C),
        ),
      ),
      backgroundColor: Colors.grey.shade50,
      side: BorderSide(color: Colors.grey.shade200),
      onPressed: viewModel.isLoading
          ? null
          : () async {
              await viewModel.updateActuator(widget.category, widget.deviceId, {
                'Color': colorValue,
              });
            },
    );
  }

  Widget _buildSuccessMessage(String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF4CAF50).withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: const Color(0xFF4CAF50).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: const Color(0xFF4CAF50).withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
            ),
            child: const Icon(
              Icons.check_circle_rounded,
              color: Color(0xFF4CAF50),
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              message,
              style: const TextStyle(
                color: Color(0xFF2C2C2C),
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Color(0xFF666666),
                fontSize: 14,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Color(0xFF2C2C2C),
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
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

  Widget _buildBrightnessForm(
    BuildContext context,
    ActuatorViewModel viewModel,
  ) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.1),
            spreadRadius: 1,
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFC107).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.brightness_6,
                  color: Color(0xFFFFC107),
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                'Controle de Brilho',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: const Color(0xFF2C2C2C),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            'Valores permitidos: 1 a 10',
            style: TextStyle(
              fontSize: 13,
              color: Colors.grey.shade600,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: const Color(0xFF6B73FF).withOpacity(0.05),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  Icons.brightness_low,
                  color: const Color(0xFF6B73FF).withOpacity(0.7),
                ),
                Expanded(
                  child: SliderTheme(
                    data: SliderTheme.of(context).copyWith(
                      activeTrackColor: const Color(0xFF6B73FF),
                      inactiveTrackColor: const Color(
                        0xFF6B73FF,
                      ).withOpacity(0.2),
                      thumbColor: const Color(0xFF6B73FF),
                      overlayColor: const Color(0xFF6B73FF).withOpacity(0.2),
                      valueIndicatorColor: const Color(0xFF6B73FF),
                      valueIndicatorTextStyle: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    child: Slider(
                      value: _currentBrightness,
                      min: 1.0,
                      max: 10.0,
                      divisions: 9,
                      label: _currentBrightness.round().toString(),
                      onChanged: (value) {
                        setState(() {
                          _currentBrightness = value;
                          _brightnessController.text = value.round().toString();
                        });
                      },
                    ),
                  ),
                ),
                Icon(
                  Icons.brightness_high,
                  color: const Color(0xFF6B73FF).withOpacity(0.7),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _brightnessController,
                  decoration: const InputDecoration(
                    labelText: 'Brilho',
                    hintText: 'Digite um valor entre 1 e 10',
                    prefixIcon: Icon(Icons.tune, color: Color(0xFF6B73FF)),
                  ),
                  keyboardType: TextInputType.number,
                  onChanged: (value) {
                    final brightness = int.tryParse(value);
                    if (brightness != null &&
                        brightness >= 1 &&
                        brightness <= 10) {
                      setState(() {
                        _currentBrightness = brightness.toDouble();
                      });
                    }
                  },
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton(
                onPressed: viewModel.isLoading
                    ? null
                    : () async {
                        final brightnessText = _brightnessController.text
                            .trim();
                        final brightness = int.tryParse(brightnessText);

                        if (brightness != null &&
                            brightness >= 1 &&
                            brightness <= 10) {
                          await viewModel.updateActuator(
                            widget.category,
                            widget.deviceId,
                            {'Brightness': brightness},
                          );
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                content: Text(
                                  'Brilho ajustado para $brightness',
                                ),
                                backgroundColor: const Color(0xFF4CAF50),
                                behavior: SnackBarBehavior.floating,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10),
                                ),
                              ),
                            );
                          }
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: const Text(
                                'O brilho deve estar entre 1 e 10',
                              ),
                              backgroundColor: const Color(0xFFFF9800),
                              behavior: SnackBarBehavior.floating,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                          );
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF6B73FF),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 12,
                  ),
                ),
                child: const Text('Aplicar'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            children: [
              _buildBrightnessChip(context, viewModel, 'Baixo', 1),
              _buildBrightnessChip(context, viewModel, 'Médio', 5),
              _buildBrightnessChip(context, viewModel, 'Alto', 10),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildBrightnessChip(
    BuildContext context,
    ActuatorViewModel viewModel,
    String label,
    int brightnessValue,
  ) {
    return ActionChip(
      avatar: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: const Color(0xFF6B73FF).withOpacity(0.2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(
          _getBrightnessIcon(brightnessValue),
          size: 14,
          color: const Color(0xFF6B73FF),
        ),
      ),
      label: Text(
        label,
        style: const TextStyle(
          fontWeight: FontWeight.w600,
          color: Color(0xFF2C2C2C),
          fontSize: 13,
        ),
      ),
      backgroundColor: Colors.grey.shade50,
      side: BorderSide(color: Colors.grey.shade200),
      onPressed: viewModel.isLoading
          ? null
          : () async {
              setState(() {
                _currentBrightness = brightnessValue.toDouble();
                _brightnessController.text = brightnessValue.toString();
              });
              await viewModel.updateActuator(widget.category, widget.deviceId, {
                'Brightness': brightnessValue,
              });
              if (mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Brilho ajustado para $brightnessValue'),
                    backgroundColor: const Color(0xFF4CAF50),
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                );
              }
            },
    );
  }

  IconData _getBrightnessIcon(int brightness) {
    if (brightness <= 3) {
      return Icons.brightness_low_rounded;
    } else if (brightness <= 7) {
      return Icons.brightness_medium_rounded;
    } else {
      return Icons.brightness_high_rounded;
    }
  }
}

import 'package:flutter/material.dart';
import '../../core/api_client.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/section_header.dart';
import '../../models/farm_digital_twin.dart';
import '../../services/digital_twin_service.dart';
import '../recommendation/crop_recommendation_screen.dart';
import '../cost_analysis/cost_analysis_screen.dart';
import '../decision_support/decision_support_screen.dart';
import '../simulator/what_if_simulator_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final DigitalTwinService _twinService = DigitalTwinService();
  FarmDigitalTwin? _farmData;
  bool _isLoading = false;
  String? _error;
  String _currentFarmId = '';

  @override
  void initState() {
    super.initState();
    // In-memory for now to avoid adding packages
  }

  void _saveFarmId(String id) {
    setState(() {
      _currentFarmId = id;
    });
    if (id.isNotEmpty) {
      _fetchFarmData();
    } else {
      setState(() {
        _farmData = null;
        _error = null;
      });
    }
  }

  Future<void> _fetchFarmData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await _twinService.getFarm(_currentFarmId);
      setState(() {
        _farmData = data;
        _isLoading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        if (e.statusCode == 404) {
          _error = 'Farm "$_currentFarmId" not found in the database.';
        } else {
          _error = e.message;
        }
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'An unexpected error occurred.';
        _isLoading = false;
      });
    }
  }

  void _showConnectFarmDialog() {
    final controller = TextEditingController(text: _currentFarmId);
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Connect Farm'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Farm ID',
            hintText: 'Enter your Farm ID to connect',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _saveFarmId(''); // Disconnect
            },
            child: const Text('Disconnect'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _saveFarmId(controller.text.trim());
            },
            child: const Text('Connect'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('KisanCare'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _currentFarmId.isNotEmpty ? _fetchFarmData : null,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _currentFarmId.isNotEmpty ? _fetchFarmData : () async {},
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildFarmHeader(context),
              const SizedBox(height: 16),

              if (_currentFarmId.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: EmptyStateWidget(
                    icon: Icons.link_off,
                    title: 'No Farm Connected',
                    message: 'Tap the switch icon in the header to connect your Farm ID and fetch real data.',
                  ),
                )
              else if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (_error != null)
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      EmptyStateWidget(
                        icon: Icons.error_outline,
                        title: 'Failed to Load Farm Data',
                        message: _error!,
                      ),
                      ElevatedButton(
                        onPressed: _fetchFarmData,
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                )
              else if (_farmData != null) ...[
                const SectionHeader(title: 'Farm Overview'),
                _buildFarmOverview(context, _farmData!),
                const SizedBox(height: 16),
                const SectionHeader(title: 'Farm Status'),
                _buildFarmStatus(context, _farmData!),
                const SizedBox(height: 16),
                const SectionHeader(title: 'Priority Actions'),
                _buildPriorityActions(context),
                const SizedBox(height: 16),
                const SectionHeader(title: 'Recent Activity'),
                _buildRecentActivity(context),
                const SizedBox(height: 24),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFarmHeader(BuildContext context) {
    return Container(
      color: Theme.of(context).primaryColor,
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      child: Row(
        children: [
          const CircleAvatar(
            backgroundColor: Colors.white,
            child: Icon(Icons.agriculture, color: Colors.green),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _farmData != null ? 'Farm: ${_farmData!.farmId}' : 'Not Connected',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  _farmData != null
                    ? '${_farmData!.location.district ?? 'Unknown District'}, ${_farmData!.location.state ?? 'Unknown State'}'
                    : 'Awaiting connection...',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                      ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.swap_horiz, color: Colors.white),
            onPressed: _showConnectFarmDialog,
          ),
        ],
      ),
    );
  }

  Widget _buildFarmOverview(BuildContext context, FarmDigitalTwin farm) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildOverviewItem(context, 'Area', farm.areaAcres != null ? '${farm.areaAcres} Acres' : 'N/A', Icons.landscape),
              _buildOverviewItem(context, 'Crop', farm.crop.currentCrop ?? 'None', Icons.grass),
              _buildOverviewItem(context, 'Season', farm.crop.season ?? 'N/A', Icons.calendar_month),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOverviewItem(BuildContext context, String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: Theme.of(context).primaryColor),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }

  Widget _buildFarmStatus(BuildContext context, FarmDigitalTwin farm) {
    final healthLabel = farm.soil.nitrogen != null ? 'Data Available' : 'No Soil Data';
    final weatherLabel = farm.climate.temperature != null ? '${farm.climate.temperature}°C, ${farm.climate.weatherCondition ?? 'Unknown'}' : 'No Climate Data';

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Row(
                children: [
                  Icon(Icons.health_and_safety, color: farm.soil.nitrogen != null ? Colors.green.shade700 : Colors.grey),
                  const SizedBox(width: 8),
                  Text('Field Health: $healthLabel', style: const TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              const Divider(),
              Row(
                children: [
                  Icon(Icons.cloud, color: farm.climate.temperature != null ? Colors.blue.shade700 : Colors.grey),
                  const SizedBox(width: 8),
                  Text('Weather: $weatherLabel'),
                ],
              ),
              const Divider(),
              Row(
                children: [
                  Icon(Icons.shield, color: Colors.blue.shade700),
                  const SizedBox(width: 8),
                  const Text('Model Outputs:'),
                  const Spacer(),
                  Text(farm.modelOutputs?.isNotEmpty == true ? '${farm.modelOutputs!.length} available' : 'None', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPriorityActions(BuildContext context) {
    return SizedBox(
      height: 130,
      child: ListView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12.0),
        children: [
          _buildActionCard(
            context,
            'Crop Rec',
            Icons.psychology,
            onTap: () => Navigator.push(
                context, MaterialPageRoute(builder: (_) => const CropRecommendationScreen())),
          ),
          _buildActionCard(
            context,
            'Cost Analysis',
            Icons.analytics,
            onTap: () => Navigator.push(
                context, MaterialPageRoute(builder: (_) => const CostAnalysisScreen())),
          ),
          _buildActionCard(
            context,
            'Decision Support',
            Icons.lightbulb,
            onTap: () => Navigator.push(
                context, MaterialPageRoute(builder: (_) => const DecisionSupportScreen())),
          ),
          _buildActionCard(
            context,
            'Simulator',
            Icons.science,
            onTap: () => Navigator.push(
                context, MaterialPageRoute(builder: (_) => const WhatIfSimulatorScreen())),
          ),
        ],
      ),
    );
  }

  Widget _buildActionCard(BuildContext context, String title, IconData icon, {required VoidCallback onTap}) {
    return Container(
      width: 100,
      margin: const EdgeInsets.symmetric(horizontal: 4.0),
      child: Card(
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 28, color: Theme.of(context).primaryColor),
                const SizedBox(height: 4),
                Expanded(
                  child: Center(
                    child: Text(
                      title,
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildRecentActivity(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 16.0),
      child: Card(
        child: EmptyStateWidget(
          icon: Icons.history,
          title: 'No Recent Activity',
          message: 'Farm activities will appear here once recorded by the backend.',
        ),
      ),
    );
  }
}

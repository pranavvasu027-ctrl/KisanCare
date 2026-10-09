import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

files = {}

files['lib/app/theme.dart'] = """
import 'package:flutter/material.dart';

class AppTheme {
  static const Color primaryColor = Color(0xFF2E7D32); // Deep green
  static const Color backgroundColor = Color(0xFFF5F5F5); // Light neutral
  static const Color cardColor = Colors.white;

  static ThemeData get lightTheme {
    return ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        primary: primaryColor,
        background: backgroundColor,
        surface: cardColor,
      ),
      scaffoldBackgroundColor: backgroundColor,
      useMaterial3: true,
      appBarTheme: const AppBarTheme(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardTheme(
        color: cardColor,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
    );
  }
}
"""

files['lib/main.dart'] = """
import 'package:flutter/material.dart';
import 'app/theme.dart';
import 'features/home/home_screen.dart';

void main() {
  runApp(const KisanCareApp());
}

class KisanCareApp extends StatelessWidget {
  const KisanCareApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'KisanCare',
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
"""

files['lib/core/widgets/empty_state.dart'] = """
import 'package:flutter/material.dart';

class EmptyStateWidget extends StatelessWidget {
  final IconData icon;
  final String title;
  final String message;

  const EmptyStateWidget({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 64, color: Colors.grey.shade400),
            const SizedBox(height: 16),
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: Colors.grey.shade700,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Colors.grey.shade600,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}
"""

files['lib/core/widgets/section_header.dart'] = """
import 'package:flutter/material.dart';

class SectionHeader extends StatelessWidget {
  final String title;
  final VoidCallback? onActionPressed;
  final String? actionLabel;

  const SectionHeader({
    super.key,
    required this.title,
    this.onActionPressed,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          if (onActionPressed != null && actionLabel != null)
            TextButton(
              onPressed: onActionPressed,
              child: Text(actionLabel!),
            ),
        ],
      ),
    );
  }
}
"""

files['lib/features/dashboard/dashboard_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/section_header.dart';
import '../../core/widgets/empty_state.dart';
import '../recommendation/crop_recommendation_screen.dart';
import '../cost_analysis/cost_analysis_screen.dart';
import '../decision_support/decision_support_screen.dart';
import '../simulator/what_if_simulator_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('KisanCare'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_none),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildFarmHeader(context),
            const SizedBox(height: 16),
            const SectionHeader(title: 'Farm Overview'),
            _buildFarmOverview(context),
            const SizedBox(height: 16),
            const SectionHeader(title: 'Farm Status'),
            _buildFarmStatus(context),
            const SizedBox(height: 16),
            const SectionHeader(title: 'Priority Actions'),
            _buildPriorityActions(context),
            const SizedBox(height: 16),
            const SectionHeader(title: 'Recent Activity'),
            _buildRecentActivity(context),
            const SizedBox(height: 24),
          ],
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
                  'Green Valley Farm',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                Text(
                  'Pune, Maharashtra',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.white70,
                      ),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.swap_horiz, color: Colors.white),
            onPressed: () {},
          ),
        ],
      ),
    );
  }

  Widget _buildFarmOverview(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildOverviewItem(context, 'Area', '12 Acres', Icons.landscape),
              _buildOverviewItem(context, 'Crop', 'Tomato', Icons.grass),
              _buildOverviewItem(context, 'Season', 'Rabi', Icons.calendar_month),
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

  Widget _buildFarmStatus(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Row(
                children: [
                  Icon(Icons.health_and_safety, color: Colors.green.shade700),
                  const SizedBox(width: 8),
                  const Text('Field Health: Good', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              const Divider(),
              Row(
                children: [
                  Icon(Icons.cloud_off, color: Colors.grey.shade500),
                  const SizedBox(width: 8),
                  const Text('Weather: Live integration unavailable'),
                ],
              ),
              const Divider(),
              Row(
                children: [
                  Icon(Icons.shield, color: Colors.blue.shade700),
                  const SizedBox(width: 8),
                  const Text('Risk Status: Low'),
                  const Spacer(),
                  const Text('Updated 2h ago', style: TextStyle(fontSize: 12, color: Colors.grey)),
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
      height: 120,
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
                Icon(icon, size: 32, color: Theme.of(context).primaryColor),
                const SizedBox(height: 8),
                Text(
                  title,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
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
          message: 'Farm activities will appear here once recorded.',
        ),
      ),
    );
  }
}
"""

files['lib/features/home/home_screen.dart'] = """
import 'package:flutter/material.dart';
import '../dashboard/dashboard_screen.dart';
import '../farm/my_farm_screen.dart';
import '../insights/insights_screen.dart';
import '../profile/profile_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const DashboardScreen(),
    const MyFarmScreen(),
    const InsightsScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: Theme.of(context).primaryColor,
        unselectedItemColor: Colors.grey,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.landscape), label: 'My Farm'),
          BottomNavigationBarItem(icon: Icon(Icons.insights), label: 'Insights'),
          BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
        ],
      ),
    );
  }
}
"""

files['lib/features/farm/my_farm_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class MyFarmScreen extends StatelessWidget {
  const MyFarmScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Farm')),
      body: const EmptyStateWidget(
        icon: Icons.landscape,
        title: 'Farm Details Unavailable',
        message: 'Detailed farm management will be implemented soon.',
      ),
    );
  }
}
"""

files['lib/features/insights/insights_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Insights')),
      body: const EmptyStateWidget(
        icon: Icons.insights,
        title: 'Insights Coming Soon',
        message: 'Market trends and crop analytics will appear here.',
      ),
    );
  }
}
"""

files['lib/features/profile/profile_screen.dart'] = """
import 'package:flutter/material.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        children: [
          const SizedBox(height: 24),
          const CircleAvatar(
            radius: 50,
            child: Icon(Icons.person, size: 50),
          ),
          const SizedBox(height: 16),
          const Center(
            child: Text(
              'Farmer Name',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(height: 32),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('Settings'),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.help),
            title: const Text('Help & Support'),
            onTap: () {},
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Logout'),
            onTap: () {},
          ),
        ],
      ),
    );
  }
}
"""

files['lib/features/recommendation/crop_recommendation_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class CropRecommendationScreen extends StatelessWidget {
  const CropRecommendationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Crop Recommendation')),
      body: const EmptyStateWidget(
        icon: Icons.psychology,
        title: 'Recommendation Model Not Connected',
        message: 'API integration for crop recommendations is pending.',
      ),
    );
  }
}
"""

files['lib/features/cost_analysis/cost_analysis_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class CostAnalysisScreen extends StatelessWidget {
  const CostAnalysisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Cost Analysis')),
      body: const EmptyStateWidget(
        icon: Icons.analytics,
        title: 'Cost Data Unavailable',
        message: 'API integration for cost analysis is pending.',
      ),
    );
  }
}
"""

files['lib/features/decision_support/decision_support_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class DecisionSupportScreen extends StatelessWidget {
  const DecisionSupportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Decision Support')),
      body: const EmptyStateWidget(
        icon: Icons.lightbulb,
        title: 'Decision Engine Not Connected',
        message: 'API integration for decision support is pending.',
      ),
    );
  }
}
"""

files['lib/features/simulator/what_if_simulator_screen.dart'] = """
import 'package:flutter/material.dart';
import '../../core/widgets/empty_state.dart';

class WhatIfSimulatorScreen extends StatelessWidget {
  const WhatIfSimulatorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('What-If Simulator')),
      body: const EmptyStateWidget(
        icon: Icons.science,
        title: 'Simulator Not Connected',
        message: 'API integration for the what-if simulator is pending.',
      ),
    );
  }
}
"""

files['test/widget_test.dart'] = """
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/main.dart';
import 'package:mobile/features/home/home_screen.dart';
import 'package:flutter/material.dart';

void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const KisanCareApp());
    expect(find.byType(HomeScreen), findsOneWidget);
  });
}
"""

for path, content in files.items():
    write_file(path, content)

print("Files generated successfully.")

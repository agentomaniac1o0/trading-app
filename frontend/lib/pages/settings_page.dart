import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';

final themeModeProvider = StateProvider<ThemeMode>((ref) => ThemeMode.dark);

class SettingsPage extends ConsumerWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    final isDark = themeMode == ThemeMode.dark;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Trading App',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Version 0.1.0',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'FastAPI Backend + Flutter Frontend',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Appearance',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      const Icon(Icons.wb_sunny_outlined,
                          color: AppColors.gold, size: 20),
                      const SizedBox(width: 8),
                      const Expanded(
                        child: Text('Dark Mode',
                            style: TextStyle(fontSize: 14)),
                      ),
                      Switch(
                        value: isDark,
                        activeColor: AppColors.positive,
                        onChanged: (v) {
                          ref.read(themeModeProvider.notifier).state =
                              v ? ThemeMode.dark : ThemeMode.light;
                        },
                      ),
                      const SizedBox(width: 4),
                      const Icon(Icons.nights_stay,
                          color: AppColors.blue, size: 20),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: const Icon(Icons.cloud_outlined),
              title: const Text('API Status'),
              subtitle: const Text('http://localhost:8000'),
              trailing: Icon(Icons.check_circle, color: AppColors.positive),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              leading: const Icon(Icons.storage_outlined),
              title: const Text('Database'),
              subtitle: const Text('SQLite (local)'),
            ),
          ),
        ],
      ),
    );
  }
}

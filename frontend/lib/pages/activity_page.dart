import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../providers/crypto_arb_provider.dart';

class ActivityPage extends ConsumerWidget {
  const ActivityPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final activityAsync = ref.watch(cryptoArbActivityProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Engine Aktivitaet'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: () => refreshCryptoArb(ref),
          ),
        ],
      ),
      body: SafeArea(
        child: activityAsync.when(
          data: (events) {
            if (events.isEmpty) {
              return Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.inbox_outlined, size: 48,
                        color: AppColors.secondaryColor(context).withOpacity(0.4)),
                    const SizedBox(height: 12),
                    Text('Noch keine Aktivitaet',
                        style: TextStyle(color: AppColors.secondaryColor(context))),
                    Text('Events erscheinen beim naechsten Arb-Cycle',
                        style: TextStyle(fontSize: 11, color: AppColors.secondaryColor(context).withOpacity(0.6))),
                  ],
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: events.length,
              itemBuilder: (context, index) {
                return _buildEventCard(context, events[index]);
              },
            );
          },
          loading: () => const Center(child: CircularProgressIndicator(strokeWidth: 2)),
          error: (_, __) => Center(
            child: Text('Fehler beim Laden',
                style: TextStyle(color: AppColors.textSecondary)),
          ),
        ),
      ),
    );
  }

  Widget _buildEventCard(BuildContext context, dynamic event) {
    final type = event['type'] ?? '?';
    final status = event['status'] ?? '?';
    final details = event['details'] ?? '';
    final coin = event['coin'];
    final amount = event['amount'];
    final apr = event['apr'];
    final reason = event['reason'] ?? '';
    final ts = event['timestamp']?.toString() ?? '';

    final (icon, color, label) = _eventMeta(type, status);

    final timeStr = ts.length >= 16 ? ts.substring(11, 16) : ts;

    return Card(
      margin: const EdgeInsets.only(bottom: 4),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                color: color.withOpacity(0.12),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Icon(icon, size: 16, color: color),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      if (coin != null) ...[
                        _badge(coin.toString(), color),
                        const SizedBox(width: 6),
                      ],
                      Text(label,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: AppColors.textColor(context),
                          )),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(details,
                      style: TextStyle(
                        fontSize: 11,
                        color: AppColors.secondaryColor(context),
                      )),
                  if (reason.isNotEmpty) ...[
                    const SizedBox(height: 1),
                    Text(reason,
                        style: TextStyle(
                          fontSize: 10,
                          color: AppColors.textSecondary,
                          fontStyle: FontStyle.italic,
                        )),
                  ],
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(timeStr,
                    style: TextStyle(
                      fontSize: 10,
                      color: AppColors.secondaryColor(context).withOpacity(0.6),
                    )),
                if (amount != null && amount != 0) ...[
                  const SizedBox(height: 2),
                  Text('\$${amount.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        color: amount >= 0 ? AppColors.positive : AppColors.negative,
                      )),
                ],
                if (apr != null) ...[
                  Text('${apr.toStringAsFixed(1)}% APR',
                      style: TextStyle(fontSize: 9, color: AppColors.gold)),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  (IconData, Color, String) _eventMeta(String type, String status) {
    switch (type) {
      case 'scan':
        return (Icons.search, AppColors.blue, 'Scan');
      case 'candidate':
        if (status == 'skipped') {
          return (Icons.block, AppColors.textSecondary, 'Uebersprungen');
        }
        return (Icons.lightbulb_outline, AppColors.gold, 'Kandidat');
      case 'open':
        return (Icons.add_circle_outline, AppColors.positive, 'Eroeffnet');
      case 'close':
        if (status == 'attempt') {
          return (Icons.warning_amber, AppColors.textSecondary, 'Schliessen versucht');
        }
        return (Icons.check_circle_outline, AppColors.negative, 'Geschlossen');
      case 'monitor':
        if (status == 'ok') {
          return (Icons.monitor_heart, AppColors.positive, 'Monitor OK');
        }
        return (Icons.warning, AppColors.textSecondary, 'Monitor');
      case 'health':
        if (status == 'ok') {
          return (Icons.healing, AppColors.positive, 'Health Check');
        }
        return (Icons.healing, AppColors.textSecondary, 'Health Check');
      case 'error':
        return (Icons.error_outline, AppColors.negative, 'Fehler');
      case 'dust':
        return (Icons.cleaning_services, AppColors.textSecondary, 'Dust');
      case 'arb':
        if (status == 'start') {
          return (Icons.play_circle_outline, AppColors.blue, 'Arb Cycle Start');
        }
        return (Icons.sync, AppColors.positive, 'Arb Cycle Done');
      case 'swap':
        return (Icons.swap_horiz, AppColors.gold, 'Swap');
      default:
        return (Icons.circle, AppColors.textSecondary, type);
    }
  }

  Widget _badge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(3),
      ),
      child: Text(text,
          style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

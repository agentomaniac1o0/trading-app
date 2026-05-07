import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../models/portfolio.dart';
import '../providers/portfolio_provider.dart';
import '../providers/trade_provider.dart';
import '../widgets/kpi_card.dart';

class PortfolioPage extends ConsumerWidget {
  const PortfolioPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final portfolioAsync = ref.watch(portfolioProvider);
    final tradesAsync = ref.watch(tradesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Portfolio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(portfolioProvider);
              ref.invalidate(tradesProvider);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(portfolioProvider);
          ref.invalidate(tradesProvider);
        },
        child: portfolioAsync.when(
          data: (portfolio) {
            if (portfolio == null) {
              return const Center(child: Text('No portfolio data'));
            }
            return _buildContent(context, portfolio, tradesAsync);
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e')),
        ),
      ),
    );
  }

  Widget _buildContent(
    BuildContext context,
    PortfolioSummary portfolio,
    AsyncValue tradesAsync,
  ) {
    final pnlColor =
        portfolio.totalPnl >= 0 ? AppColors.positive : AppColors.negative;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Portfolio Value',
                value:
                    '\$${portfolio.portfolioValue.toStringAsFixed(2)}',
                icon: Icons.account_balance_wallet,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Total P&L',
                value:
                    '${portfolio.totalPnl >= 0 ? "+" : ""}\$${portfolio.totalPnl.toStringAsFixed(2)}',
                subtitle:
                    '${portfolio.totalPnlPct >= 0 ? "+" : ""}${portfolio.totalPnlPct.toStringAsFixed(1)}%',
                icon: Icons.trending_up,
                valueColor: pnlColor,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Cash Available',
                value: '\$${portfolio.cash.toStringAsFixed(2)}',
                icon: Icons.payments,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Invested',
                value: '\$${portfolio.invested.toStringAsFixed(2)}',
                icon: Icons.show_chart,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Open Positions',
                value: '${portfolio.openPositions}',
                icon: Icons.open_in_new,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Win Rate',
                value: '${portfolio.winRate.toStringAsFixed(1)}%',
                subtitle: '${portfolio.closedTrades} trades',
                icon: Icons.emoji_events,
                valueColor: portfolio.winRate >= 50
                    ? AppColors.positive
                    : AppColors.negative,
              ),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Text(
          'Initial Capital: \$${portfolio.initialCapital.toStringAsFixed(2)}',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }
}
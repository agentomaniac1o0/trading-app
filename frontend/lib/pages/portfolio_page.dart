import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../models/live_portfolio.dart';
import '../models/portfolio.dart';
import '../models/trade.dart';
import '../providers/live_portfolio_provider.dart';
import '../providers/portfolio_review_provider.dart';
import '../providers/trade_provider.dart';
import '../providers/trader_provider.dart';
import '../widgets/kpi_card.dart';
import '../widgets/portfolio_review_card.dart';
import '../widgets/sparkline.dart';
import '../widgets/trader_avatar_row.dart';

class PortfolioPage extends ConsumerWidget {
  const PortfolioPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final liveAsync = ref.watch(livePortfolioProvider);
    final tradesAsync = ref.watch(tradesProvider);
    final tradersAsync = ref.watch(tradersProvider);
    final reviewAsync = ref.watch(portfolioReviewProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Portfolio'),
            const SizedBox(width: 8),
            tradersAsync.when(
              data: (traders) => TraderAvatarRow(traders: traders),
              loading: () => const SizedBox(width: 60, height: 28,
                  child: Center(child: SizedBox(
                      width: 12, height: 12,
                      child: CircularProgressIndicator(strokeWidth: 1.5)))),
              error: (_, __) => const SizedBox(),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.invalidate(livePortfolioProvider);
              ref.invalidate(tradesProvider);
              ref.invalidate(tradersProvider);
              ref.invalidate(portfolioReviewProvider);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(livePortfolioProvider);
          ref.invalidate(tradesProvider);
          ref.invalidate(tradersProvider);
          ref.invalidate(portfolioReviewProvider);
        },
        child: liveAsync.when(
          data: (live) => singleChildScrollView(context, live, tradesAsync, reviewAsync),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (e, _) => Center(child: Text('Error: $e', style: const TextStyle(color: AppColors.textSecondary))),
        ),
      ),
    );
  }

  Widget singleChildScrollView(
    BuildContext context,
    LivePortfolio? live,
    AsyncValue<List<Trade>> tradesAsync,
    AsyncValue<PortfolioReview?> reviewAsync,
  ) {
    if (live == null) {
      return const Center(child: Text('No portfolio data', style: TextStyle(color: AppColors.textSecondary)));
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildKpis(live),
        const SizedBox(height: 24),
        _buildPnlCurve(context, tradesAsync),
        const SizedBox(height: 16),
        _buildLivePositions(live),
        const SizedBox(height: 16),
        _buildPortfolioReview(reviewAsync),
      ],
    );
  }

  Widget _buildKpis(LivePortfolio p) {
    final pnlColor = p.totalPnl >= 0 ? AppColors.positive : AppColors.negative;
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Portfolio Value',
                value: '\$${p.portfolioValue.toStringAsFixed(2)}',
                icon: Icons.account_balance_wallet,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Total P&L',
                value: '${p.totalPnl >= 0 ? "+" : ""}\$${p.totalPnl.toStringAsFixed(2)}',
                subtitle: '${p.totalPnlPct >= 0 ? "+" : ""}${p.totalPnlPct.toStringAsFixed(1)}%',
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
                title: 'Cash',
                value: '\$${p.cash.toStringAsFixed(2)}',
                icon: Icons.payments,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Invested (Market)',
                value: '\$${p.investedMarket.toStringAsFixed(2)}',
                subtitle: 'Cost: \$${p.investedCost.toStringAsFixed(2)}',
                icon: Icons.show_chart,
                valueColor: p.investedMarket >= p.investedCost
                    ? AppColors.positive
                    : AppColors.negative,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: KpiCard(
                title: 'Unrealized P&L',
                value: '${p.unrealizedPnl >= 0 ? "+" : ""}\$${p.unrealizedPnl.toStringAsFixed(2)}',
                icon: Icons.wb_sunny_outlined,
                valueColor: p.unrealizedPnl >= 0 ? AppColors.positive : AppColors.negative,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Realized P&L',
                value: '${p.realizedPnl >= 0 ? "+" : ""}\$${p.realizedPnl.toStringAsFixed(2)}',
                icon: Icons.receipt_long,
                valueColor: p.realizedPnl >= 0 ? AppColors.positive : AppColors.negative,
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
                value: '${p.openPositions}',
                icon: Icons.open_in_new,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: KpiCard(
                title: 'Win Rate',
                value: '${p.winRate.toStringAsFixed(1)}%',
                subtitle: '${p.closedTrades} closed trades',
                icon: Icons.emoji_events,
                valueColor: p.winRate >= 50 ? AppColors.positive : AppColors.negative,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          'Initial Capital: \$${p.initialCapital.toStringAsFixed(2)}',
          style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
        ),
      ],
    );
  }

  Widget _buildPnlCurve(BuildContext context, AsyncValue<List<Trade>> tradesAsync) {
    return tradesAsync.when(
      data: (trades) {
        final closedTrades = trades.where((t) => t.status == 'closed' && t.pnl != null).toList();
        if (closedTrades.isEmpty) {
          return Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Text('P&L Curve', style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 12),
                  const Text('No closed trades yet',
                      style: TextStyle(color: AppColors.textSecondary)),
                ],
              ),
            ),
          );
        }

        closedTrades.sort((a, b) => a.dateClose!.compareTo(b.dateClose!));
        final spots = <FlSpot>[];
        double cumulative = 0;
        for (int i = 0; i < closedTrades.length; i++) {
          cumulative += closedTrades[i].pnl!;
          spots.add(FlSpot(i.toDouble(), cumulative));
        }

        final minY = spots.map((s) => s.y).reduce((a, b) => a < b ? a : b);
        final maxY = spots.map((s) => s.y).reduce((a, b) => a > b ? a : b);
        final yPadding = (maxY - minY) * 0.2;

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('P&L Curve', style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 12),
                SizedBox(
                  height: 200,
                  child: LineChart(
                    LineChartData(
                      minY: (minY - yPadding).floorToDouble(),
                      maxY: (maxY + yPadding).ceilToDouble(),
                      gridData: FlGridData(
                        show: true,
                        drawVerticalLine: false,
                        getDrawingHorizontalLine: (value) => FlLine(
                          color: value == 0
                              ? AppColors.textSecondary.withOpacity(0.5)
                              : AppColors.border.withOpacity(0.3),
                          strokeWidth: value == 0 ? 1.5 : 0.5,
                          dashArray: value == 0 ? [5, 3] : null,
                        ),
                      ),
                      titlesData: FlTitlesData(
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 55,
                            getTitlesWidget: (value, meta) => Text(
                              '\$${value.toStringAsFixed(0)}',
                              style: const TextStyle(color: AppColors.textSecondary, fontSize: 10),
                            ),
                          ),
                        ),
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 30,
                            interval: spots.length > 10 ? (spots.length / 5).ceilToDouble() : 1,
                            getTitlesWidget: (value, meta) {
                              final idx = value.toInt();
                              if (idx < 0 || idx >= closedTrades.length) return const SizedBox();
                              return Padding(
                                padding: const EdgeInsets.only(top: 6),
                                child: Text(closedTrades[idx].dateClose!.substring(5),
                                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 9)),
                              );
                            },
                          ),
                        ),
                        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      ),
                      borderData: FlBorderData(show: false),
                      lineBarsData: [
                        LineChartBarData(
                          spots: spots,
                          isCurved: true,
                          curveSmoothness: 0.3,
                          color: AppColors.positive,
                          barWidth: 2.5,
                          dotData: FlDotData(
                            show: spots.length <= 15,
                            getDotPainter: (spot, _, __, ___) => FlDotCirclePainter(
                              radius: 3,
                              color: spot.y >= 0 ? AppColors.positive : AppColors.negative,
                              strokeWidth: 0,
                            ),
                          ),
                          belowBarData: BarAreaData(
                            show: true,
                            color: AppColors.positive.withOpacity(0.08),
                          ),
                        ),
                      ],
                      lineTouchData: LineTouchData(
                        touchTooltipData: LineTouchTooltipData(
                          getTooltipItems: (spots) => spots
                              .map((s) => LineTooltipItem(
                                    '\$${s.y.toStringAsFixed(2)}',
                                    const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                                  ))
                              .toList(),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
      loading: () => const Card(
        child: Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator())),
      ),
      error: (_, __) => const SizedBox(),
    );
  }

  Widget _buildLivePositions(LivePortfolio p) {
    if (p.positions.isEmpty) return const SizedBox();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Open Positions', style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            )),
            const SizedBox(height: 12),
            ...p.positions.map((pos) => _LivePositionRow(position: pos)),
            const Divider(),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total cost', style: TextStyle(color: AppColors.textSecondary)),
                Text('\$${p.investedCost.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.bold)),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Total market value', style: TextStyle(color: AppColors.textSecondary)),
                Text('\$${p.investedMarket.toStringAsFixed(2)}',
                    style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: p.investedMarket >= p.investedCost
                            ? AppColors.positive : AppColors.negative)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPortfolioReview(AsyncValue<PortfolioReview?> reviewAsync) {
    return reviewAsync.when(
      data: (review) {
        if (review == null) return const SizedBox();
        return PortfolioReviewCard(review: review);
      },
      loading: () => const SizedBox(),
      error: (_, __) => const SizedBox(),
    );
  }
}

class _LivePositionRow extends StatelessWidget {
  final LivePosition position;
  const _LivePositionRow({required this.position});

  @override
  Widget build(BuildContext context) {
    final isLong = position.direction == 'LONG';
    final pnlColor = position.unrealizedPnl >= 0 ? AppColors.positive : AppColors.negative;
    final dirColor = isLong ? AppColors.positive : AppColors.negative;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 8, height: 8,
                decoration: BoxDecoration(
                  color: dirColor,
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: dirColor.withOpacity(0.4), blurRadius: 4, spreadRadius: 1)],
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text('${position.symbol} (${position.direction})',
                    style: const TextStyle(fontWeight: FontWeight.w600)),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('\$${position.priceCurrent.toStringAsFixed(2)}',
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                  Text('Entry: \$${position.priceOpen.toStringAsFixed(2)}',
                      style: const TextStyle(color: AppColors.textSecondary, fontSize: 11)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.only(left: 18),
            child: Row(
              children: [
                Text('×${position.quantity.toStringAsFixed(0)}',
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                const SizedBox(width: 8),
                Text('Cost: \$${position.cost.toStringAsFixed(2)}',
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
                const Spacer(),
                Text(
                  '${position.unrealizedPnl >= 0 ? "+" : ""}\$${position.unrealizedPnl.toStringAsFixed(2)} '
                  '(${position.unrealizedPnlPct >= 0 ? "+" : ""}${position.unrealizedPnlPct.toStringAsFixed(2)}%)',
                  style: TextStyle(
                    color: pnlColor,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

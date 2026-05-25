import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../models/live_portfolio.dart';
import '../models/portfolio.dart';
import '../models/portfolio_review.dart';
import '../models/trade.dart';
import '../models/trader_profile.dart';
import '../providers/live_portfolio_provider.dart';
import '../providers/portfolio_review_provider.dart';
import '../providers/trade_provider.dart';
import '../providers/trader_provider.dart';
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
        title: const Text('Portfolio'),
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
          data: (live) => singleChildScrollView(context, live, tradesAsync, tradersAsync, reviewAsync),
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
    AsyncValue<List<TraderProfile>> tradersAsync,
    AsyncValue<PortfolioReview?> reviewAsync,
  ) {
    if (live == null) {
      return const Center(child: Text('No portfolio data', style: TextStyle(color: AppColors.textSecondary)));
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildOverviewCard(tradersAsync, live),
        const SizedBox(height: 16),
        _buildPnlCurve(context, tradesAsync),
        const SizedBox(height: 16),
        _buildMarketReports(context),
        const SizedBox(height: 16),
        _buildLivePositions(live),
        const SizedBox(height: 16),
        _buildPortfolioReview(reviewAsync),
      ],
    );
  }

  Widget _buildOverviewCard(
    AsyncValue<List<TraderProfile>> tradersAsync,
    LivePortfolio live,
  ) {
    final pnlColor = live.totalPnl >= 0 ? AppColors.positive : AppColors.negative;
    final investedColor = live.investedMarket >= live.investedCost
        ? AppColors.positive
        : AppColors.negative;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Dashboard',
              style: TextStyle(
                color: AppColors.textPrimary,
                fontSize: 15,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  flex: 4,
                  child: tradersAsync.when(
                    data: (traders) => TraderAvatarRow(traders: traders),
                    loading: () => const SizedBox(
                      height: 60,
                      child: Center(child: SizedBox(width: 16, height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2))),
                    ),
                    error: (_, __) => const SizedBox.shrink(),
                  ),
                ),
                Container(width: 1, height: 80, color: AppColors.border.withOpacity(0.4)),
                const SizedBox(width: 12),
                Expanded(
                  flex: 5,
                  child: _compactKpiGrid(live, pnlColor, investedColor),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _compactKpiGrid(LivePortfolio p, Color pnlColor, Color investedColor) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          children: [
            Expanded(
              child: _miniKpi(
                label: 'Portfolio Value',
                value: '\$${p.portfolioValue.toStringAsFixed(2)}',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _miniKpi(
                label: 'Cash',
                value: '\$${p.cash.toStringAsFixed(2)}',
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _miniKpi(
                label: 'Total P&L',
                value: '${p.totalPnl >= 0 ? "+" : ""}\$${p.totalPnl.toStringAsFixed(2)}',
                valueColor: pnlColor,
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _miniKpi(
                label: 'Invested (Market)',
                value: '\$${p.investedMarket.toStringAsFixed(2)}',
                valueColor: investedColor,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _miniKpi({
    required String label,
    required String value,
    Color? valueColor,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 10,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            color: valueColor ?? AppColors.textPrimary,
            fontSize: 14,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }

  Widget _buildMarketReports(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.article_outlined, color: AppColors.gold, size: 18),
                const SizedBox(width: 8),
                const Text(
                  'Marktberichte',
                  style: TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const Spacer(),
                FilledButton.icon(
                  onPressed: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Marktbericht wird angefordert...'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  },
                  icon: const Icon(Icons.auto_awesome, size: 16),
                  label: const Text('Bericht anfordern', style: TextStyle(fontSize: 12)),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    backgroundColor: AppColors.gold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Tägliche KI-Analyse deines Portfolios mit Markteinschätzung, Risikobewertung und Handlungsempfehlungen.',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 11,
              ),
            ),
          ],
        ),
      ),
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

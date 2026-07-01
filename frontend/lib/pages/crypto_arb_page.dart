import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../providers/crypto_arb_provider.dart';

class CryptoArbPage extends ConsumerStatefulWidget {
  const CryptoArbPage({super.key});

  @override
  ConsumerState<CryptoArbPage> createState() => _CryptoArbPageState();
}

class _CryptoArbPageState extends ConsumerState<CryptoArbPage> {
  bool _showHistory = false;
  Timer? _refreshTimer;
  final _lastUpdated = ValueNotifier<DateTime?>(null);

  @override
  void initState() {
    super.initState();
    Future.microtask(() => refreshCryptoArb(ref));
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      refreshCryptoArb(ref);
      _lastUpdated.value = DateTime.now();
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    _lastUpdated.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final summaryAsync = ref.watch(cryptoArbSummaryProvider);
    final positionsAsync = ref.watch(cryptoArbPositionsProvider);
    final historyAsync = ref.watch(cryptoArbHistoryProvider);
    final portfolioAsync = ref.watch(cryptoArbPortfolioProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Crypto Arb Portfolio'),
        actions: [
          ValueListenableBuilder<DateTime?>(
            valueListenable: _lastUpdated,
            builder: (context, ts, _) {
              if (ts == null) return const SizedBox.shrink();
              return Center(
                child: Padding(
                  padding: const EdgeInsets.only(right: 4),
                  child: Text(
                    '${ts.hour.toString().padLeft(2, '0')}:${ts.minute.toString().padLeft(2, '0')}:${ts.second.toString().padLeft(2, '0')}',
                    style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context)),
                  ),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 20),
            onPressed: () {
              refreshCryptoArb(ref);
              _lastUpdated.value = DateTime.now();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async => refreshCryptoArb(ref),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildPortfolioKPIs(summaryAsync, portfolioAsync, positionsAsync),
              const SizedBox(height: 16),
              _buildCoinBreakdown(portfolioAsync),
              const SizedBox(height: 16),
              _buildSectionTitle('Aktive Arb-Positionen'),
              const SizedBox(height: 8),
              _buildPositions(positionsAsync),
              const SizedBox(height: 16),
              _buildSectionTitle('Trade History'),
              const SizedBox(height: 8),
              _buildHistoryToggle(),
              const SizedBox(height: 8),
              _buildHistory(historyAsync),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPortfolioKPIs(AsyncValue<Map<String, dynamic>?> summaryAsync,
      AsyncValue<Map<String, dynamic>?> portfolioAsync,
      AsyncValue<List<dynamic>> posAsync) {
    final portfolio = portfolioAsync.valueOrNull;
    final summary = summaryAsync.valueOrNull;

    final liveValue = (portfolio?['total_value'] ?? 0.0).toDouble();
    final spotValue = (portfolio?['spot_total'] ?? 0.0).toDouble();
    final futValue = (portfolio?['futures_total'] ?? 0.0).toDouble();
    final nCoins = portfolio?['coins']?.length ?? 0;
    final arbPositions = portfolio?['arb_positions'] ?? 0;

    final invested = (summary?['total_invested'] ?? 0.0).toDouble();
    final realizedPnl = (summary?['total_realized_pnl'] ?? 0.0).toDouble();
    final unrealizedPnl = (summary?['unrealized_pnl'] ?? 0.0).toDouble();
    final todayPnl = (summary?['today_pnl'] ?? 0.0).toDouble();
    final totalPnl = realizedPnl + unrealizedPnl;

    if (portfolioAsync.isLoading && summaryAsync.isLoading) {
      return const Center(child: Padding(
        padding: EdgeInsets.all(32),
        child: CircularProgressIndicator(strokeWidth: 2),
      ));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.account_balance, size: 18, color: AppColors.gold),
                const SizedBox(width: 6),
                Text('Portfolio',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textColor(context),
                    )),
                const Spacer(),
                _badge('LIVE · KuCoin', AppColors.positive),
              ],
            ),
            const SizedBox(height: 10),
            // Main value
            Center(
              child: Text('\$${liveValue.toStringAsFixed(2)}',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textColor(context),
                  )),
            ),
            const SizedBox(height: 4),
            Center(
              child: Text('$nCoins Coins · Spot \$${spotValue.toStringAsFixed(0)} · Futures \$${futValue.toStringAsFixed(0)}',
                  style: TextStyle(fontSize: 11, color: AppColors.secondaryColor(context))),
            ),
            const Divider(height: 20),
            Row(
              children: [
                _kpi('Arb Invested', '\$${invested.toStringAsFixed(0)}', AppColors.blue),
                _kpi('Arb Pos.', '$arbPositions', AppColors.gold),
                _kpi('Total P&L', '\$${totalPnl.toStringAsFixed(2)}',
                    totalPnl >= 0 ? AppColors.positive : AppColors.negative),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                _kpi('Funding/Tag', '\$${_computeDailyEarnings(positionsAsync).toStringAsFixed(4)}', AppColors.gold),
                _kpi('Funding/Monat', '\$${(_computeDailyEarnings(positionsAsync) * 30).toStringAsFixed(2)}', AppColors.positive),
              ],
            ),
            if (todayPnl != 0) ...[
              const SizedBox(height: 6),
              Row(
                children: [
                  Text('Today: ',
                      style: TextStyle(fontSize: 11, color: AppColors.secondaryColor(context))),
                  Text('\$${todayPnl.toStringAsFixed(2)}',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: todayPnl >= 0 ? AppColors.positive : AppColors.negative,
                      )),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildCoinBreakdown(AsyncValue<Map<String, dynamic>?> portfolioAsync) {
    final portfolio = portfolioAsync.valueOrNull;
    if (portfolio == null) return const SizedBox.shrink();

    final coins = (portfolio['coins'] as List<dynamic>?) ?? [];
    if (coins.isEmpty) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Bestände',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textColor(context),
                    )),
                const Spacer(),
                Text('${coins.length} Coins',
                    style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context))),
              ],
            ),
            const Divider(),
            ...coins.take(12).map<Widget>((c) {
              final coin = c['coin'] ?? '?';
              final usd = (c['usd_value'] ?? 0.0).toDouble();
              final amount = (c['amount'] ?? 0.0).toDouble();
              final pct = (portfolio['total_value'] ?? 1.0).toDouble() > 0
                  ? usd / (portfolio['total_value'] as num).toDouble() * 100
                  : 0.0;
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  children: [
                    _coinIcon(coin),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(coin,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: AppColors.textColor(context),
                          )),
                    ),
                    Text('\$${usd.toStringAsFixed(2)}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textColor(context),
                        )),
                    const SizedBox(width: 6),
                    SizedBox(
                      width: 38,
                      child: Text('${pct.toStringAsFixed(1)}%',
                          style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context))),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _buildPositions(AsyncValue<List<dynamic>> async) {
    return async.when(
      data: (positions) {
        if (positions.isEmpty) {
          return _cardPlaceholder('Keine aktiven Arb-Positionen', Icons.hourglass_empty);
        }
        return Column(
          children: positions.map<Widget>((p) {
            final coin = p['coin'] ?? '?';
            final cost = (p['cost'] ?? 0.0).toDouble();
            final apr = (p['funding_apr_open'] ?? p['funding_apr_current'] ?? 0.0).toDouble();
            final rate = (p['funding_rate_open'] ?? 0.0).toDouble();
            final spotQty = (p['spot_quantity'] ?? 0.0).toDouble();
            final perpQty = (p['perp_quantity'] ?? 0.0).toDouble();
            final entry = (p['entry_price'] ?? 0.0).toDouble();
            final upnl = (p['unrealized_pnl'] ?? p['pnl'] ?? 0.0).toDouble();
            final currentPrice = (p['current_price'] ?? entry).toDouble();
            final openedAt = p['opened_at']?.toString() ?? '?';
            final dailyEst = cost * rate * 3;  // 3 settlements/day
            final hedgePct = spotQty > 0 ? (perpQty / spotQty * 100) : 0;

            return Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        _coinIcon(coin),
                        const SizedBox(width: 8),
                        Text(coin,
                            style: TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w700,
                              color: AppColors.textColor(context),
                            )),
                        const Spacer(),
                        _pnlChip(upnl),
                      ],
                    ),
                    const SizedBox(height: 10),
                    _infoRow('Spot Long', '${spotQty.toStringAsFixed(4)} $coin · \$${cost.toStringAsFixed(0)}'),
                    _infoRow('Perp Short', '${perpQty.toStringAsFixed(1)} $coin · Hedge ${hedgePct.toStringAsFixed(0)}%'),
                     _infoRow('Einstandspreis', '\$${entry.toStringAsFixed(2)}'),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        _chip('APR ${apr.toStringAsFixed(1)}%', AppColors.positive),
                        const SizedBox(width: 6),
                        _chip('≈\$${dailyEst.toStringAsFixed(4)}/tag', AppColors.gold),
                        const SizedBox(width: 6),
                        _chip('Rate ${(rate * 100).toStringAsFixed(4)}%', AppColors.blue),
                      ],
                    ),
                    if (currentPrice != entry) ...[
                      const SizedBox(height: 6),
                      Text('Current: \$${currentPrice.toStringAsFixed(2)}  Δ ${((currentPrice - entry) / entry * 100).toStringAsFixed(2)}%',
                          style: TextStyle(
                            fontSize: 11,
                            color: currentPrice >= entry ? AppColors.positive : AppColors.negative,
                          )),
                    ],
                    const SizedBox(height: 4),
                    Text(openedAt.length > 16 ? 'Opened: ${openedAt.substring(0, 16).replaceAll('T', ' ')}' : openedAt,
                        style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context))),
                  ],
                ),
              ),
            );
          }).toList(),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator(strokeWidth: 2)),
      error: (_, __) => _cardPlaceholder('Fehler beim Laden', Icons.error_outline),
    );
  }

  Widget _buildHistoryToggle() {
    return InkWell(
      onTap: () => setState(() => _showHistory = !_showHistory),
      child: Row(
        children: [
          Icon(
            _showHistory ? Icons.expand_less : Icons.expand_more,
            size: 18,
            color: AppColors.blue,
          ),
          const SizedBox(width: 4),
          Text(
            _showHistory ? 'Einklappen' : 'Alle Trades anzeigen',
            style: TextStyle(fontSize: 12, color: AppColors.blue),
          ),
        ],
      ),
    );
  }

  Widget _buildHistory(AsyncValue<List<dynamic>> async) {
    if (!_showHistory) return const SizedBox.shrink();

    return async.when(
      data: (history) {
        if (history.isEmpty) {
          return _cardPlaceholder('Noch keine Trades', Icons.history);
        }
        return Column(
          children: history.map<Widget>((h) {
            final type = h['type'] ?? '?';
            final coin = h['coin'] ?? '?';
            final amount = (h['amount'] ?? 0.0).toDouble();
            final price = (h['price'] ?? h['entry_price'] ?? 0.0).toDouble();
            final pnl = (h['net_pnl'] ?? h['pnl'] ?? 0.0).toDouble();
            final ts = h['timestamp']?.toString() ?? '?';
            final simulated = h['_simulated'] == true;

            final isOpen = type == 'open';
            final icon = isOpen ? Icons.add_circle_outline : Icons.remove_circle_outline;
            final color = isOpen ? AppColors.positive : AppColors.negative;
            final label = isOpen ? 'OPEN' : 'CLOSE';
            final pnlText = pnl != 0 ? ' · P&L \$${pnl.toStringAsFixed(2)}' : '';

            return Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  child: Row(
                    children: [
                      Icon(icon, size: 16, color: color),
                      const SizedBox(width: 8),
                      Text(coin,
                          style: TextStyle(
                            fontWeight: FontWeight.w600,
                            color: AppColors.textColor(context),
                          )),
                      const SizedBox(width: 8),
                      _badge(label, color),
                      if (simulated) ...[
                        const SizedBox(width: 4),
                        _badge('SIM', AppColors.textSecondary),
                      ],
                      const Spacer(),
                      Text('\$${amount.toStringAsFixed(0)} @ \$${price.toStringAsFixed(2)}$pnlText',
                          style: TextStyle(fontSize: 11, color: AppColors.secondaryColor(context))),
                      const SizedBox(width: 8),
                      Text(
                        ts.length > 10 ? ts.substring(0, 10) : ts,
                        style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context)),
                      ),
                    ],
                  ),
                ),
              ),
            );
          }).toList(),
        );
      },
      loading: () => const Center(child: CircularProgressIndicator(strokeWidth: 2)),
      error: (_, __) => _cardPlaceholder('Fehler beim Laden', Icons.error_outline),
    );
  }

  // --- Helpers ---

  Widget _kpi(String label, String value, Color color) {
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label,
              style: TextStyle(fontSize: 10, color: AppColors.secondaryColor(context))),
          const SizedBox(height: 2),
          Text(value,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: color)),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        children: [
          SizedBox(
            width: 70,
            child: Text(label,
                style: TextStyle(fontSize: 11, color: AppColors.secondaryColor(context))),
          ),
          Expanded(
            child: Text(value,
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: AppColors.textColor(context))),
          ),
        ],
      ),
    );
  }

  Widget _chip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(text,
          style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: color)),
    );
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

  Widget _pnlChip(double pnl) {
    final color = pnl >= 0 ? AppColors.positive : AppColors.negative;
    final sign = pnl >= 0 ? '+' : '';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text('$sign\$${pnl.toStringAsFixed(2)}',
          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: color)),
    );
  }

  Widget _coinIcon(String coin) {
    final colors = <String, Color>{
      'BTC': const Color(0xFFf7931a),
      'ETH': const Color(0xFF627eea),
      'SOL': const Color(0xFF9945ff),
      'SUI': const Color(0xFF4da2ff),
      'APT': const Color(0xFF00d4aa),
      'XRP': const Color(0xFF23292f),
      'DOT': const Color(0xFFe6007a),
      'AVAX': const Color(0xFFe84142),
      'NEAR': const Color(0xFF00c08b),
      'OP': const Color(0xFFff0420),
      'ARB': const Color(0xFF28a0f0),
      'ATOM': const Color(0xFF2e3148),
    };
    return Container(
      width: 24,
      height: 24,
      decoration: BoxDecoration(
        color: (colors[coin] ?? AppColors.gold).withOpacity(0.2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(
        child: Text(coin[0],
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: colors[coin] ?? AppColors.gold,
            )),
      ),
    );
  }

  double _computeDailyEarnings(AsyncValue<List<dynamic>> posAsync) {
    double total = 0;
    if (posAsync.valueOrNull != null) {
      for (final p in posAsync.valueOrNull!) {
        final cost = (p['cost'] ?? 0.0).toDouble();
        final rate = (p['funding_rate_current'] ?? p['funding_rate_open'] ?? 0.0).toDouble();
        total += cost * rate * 3;  // 3 settlements per day
      }
    }
    return total;
  }

  Widget _buildSectionTitle(String title) {
    return Text(title,
        style: TextStyle(
          color: AppColors.textColor(context),
          fontSize: 15,
          fontWeight: FontWeight.w700,
        ));
  }

  Widget _emptyCard() {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Center(
          child: Column(
            children: [
              Icon(Icons.cloud_off, size: 36, color: AppColors.textSecondary),
              SizedBox(height: 8),
              Text('Keine Verbindung zum Backend',
                  style: TextStyle(color: AppColors.textSecondary)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _cardPlaceholder(String text, IconData icon) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Center(
          child: Column(
            children: [
              Icon(icon, size: 28, color: AppColors.textSecondary),
              const SizedBox(height: 6),
              Text(text, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}

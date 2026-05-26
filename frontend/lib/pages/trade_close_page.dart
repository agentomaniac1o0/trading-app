import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../models/trade.dart';
import '../providers/price_provider.dart';
import '../providers/trade_provider.dart';
import '../widgets/trade_card.dart';

class TradeClosePage extends ConsumerWidget {
  const TradeClosePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tradesAsync = ref.watch(tradesProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Trades')),
      body: tradesAsync.when(
        data: (trades) {
          final openTrades = trades.where((t) => t.status == 'open').toList();
          if (openTrades.isEmpty) {
            return const Padding(
              padding: EdgeInsets.all(32),
              child: Center(
                child: Text('No open trades',
                    style: TextStyle(color: AppColors.textSecondary)),
              ),
            );
          }
          final grouped = _groupBySymbol(openTrades);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: grouped.entries.map((e) {
              return _MergedTradeTile(
                symbol: e.key,
                trades: e.value,
              );
            }).toList(),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }

  Map<String, List<Trade>> _groupBySymbol(List<Trade> trades) {
    final map = <String, List<Trade>>{};
    for (final t in trades) {
      map.putIfAbsent(t.symbol, () => []).add(t);
    }
    return map;
  }
}

class _MergedTradeTile extends ConsumerStatefulWidget {
  final String symbol;
  final List<Trade> trades;
  const _MergedTradeTile({required this.symbol, required this.trades});

  @override
  ConsumerState<_MergedTradeTile> createState() => _MergedTradeTileState();
}

class _MergedTradeTileState extends ConsumerState<_MergedTradeTile> {
  double? _livePrice;
  bool _fetchingPrice = false;
  bool _showDetails = false;
  final _qtyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _fetchPrice());
  }

  @override
  void dispose() {
    _qtyController.dispose();
    super.dispose();
  }

  double get _totalQty => widget.trades.fold(0.0, (s, t) => s + t.quantity);
  double get _totalCost => widget.trades.fold(0.0, (s, t) => s + t.cost);
  String get _asset => widget.trades.first.asset;
  String get _direction => widget.trades.first.direction;
  double get _avgEntry =>
      _totalCost / _totalQty;

  Future<void> _fetchPrice() async {
    if (_fetchingPrice) return;
    setState(() => _fetchingPrice = true);
    try {
      final notifier = ref.read(priceMapProvider.notifier);
      final price = await notifier.fetchPrice(widget.symbol);
      if (price != null && mounted) {
        setState(() => _livePrice = price.price);
      }
    } finally {
      if (mounted) setState(() => _fetchingPrice = false);
    }
  }

  Future<void> _closeTrade(Trade trade, {double? quantity}) async {
    if (_livePrice == null) {
      await _fetchPrice();
      if (_livePrice == null) return;
    }
    try {
      await ref.read(tradesProvider.notifier).closeTrade(
            trade.id,
            _livePrice!,
            quantityClose: quantity,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(quantity != null
                ? 'Closed ${quantity.toStringAsFixed(4)} units'
                : 'Trade closed'),
            backgroundColor: AppColors.positive,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppColors.negative,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLong = _direction == 'LONG';
    final dirColor = isLong ? AppColors.positive : AppColors.negative;
    final estPnl = _livePrice != null
        ? isLong
            ? (_livePrice! - _avgEntry) * _totalQty
            : (_avgEntry - _livePrice!) * _totalQty
        : null;
    final estPnlPct = estPnl != null && _totalCost > 0
        ? (estPnl / _totalCost) * 100
        : null;

    final hasStopLoss =
        widget.trades.any((t) => t.stopLoss != null && t.stopLoss! > 0);
    final stopLossHit = _livePrice != null &&
        hasStopLoss &&
        (isLong
            ? _livePrice! <= widget.trades.first.stopLoss!
            : _livePrice! >= widget.trades.first.stopLoss!);

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 10,
                  height: 10,
                  decoration: BoxDecoration(
                    color: dirColor,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                          color: dirColor.withOpacity(0.4),
                          blurRadius: 4,
                          spreadRadius: 1),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '${widget.symbol}  ·  $_asset',
                    style: const TextStyle(
                        fontWeight: FontWeight.bold, fontSize: 15),
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: dirColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(_direction,
                      style: TextStyle(color: dirColor, fontSize: 11)),
                ),
                if (widget.trades.length > 1) ...[
                  const SizedBox(width: 6),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.gold.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text('${widget.trades.length} pos.',
                        style: const TextStyle(
                            color: AppColors.gold, fontSize: 10)),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text('Ø Entry: \$${_avgEntry.toStringAsFixed(2)}',
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 12)),
                const SizedBox(width: 12),
                Text('×${_totalQty.toStringAsFixed(0)}',
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 12)),
                const SizedBox(width: 12),
                Text('Cost: \$${_totalCost.toStringAsFixed(2)}',
                    style: const TextStyle(
                        color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                if (_livePrice != null)
                  Text(
                    'Live: \$${_livePrice!.toStringAsFixed(2)}',
                    style: const TextStyle(
                        color: AppColors.gold,
                        fontWeight: FontWeight.bold,
                        fontSize: 15),
                  )
                else if (_fetchingPrice)
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(
                        strokeWidth: 2, color: AppColors.gold),
                  ),
                if (estPnl != null) ...[
                  const SizedBox(width: 12),
                  Text(
                    '${estPnl >= 0 ? "+" : ""}\$${estPnl.toStringAsFixed(2)} '
                    '(${estPnlPct != null ? "${estPnlPct >= 0 ? "+" : ""}${estPnlPct.toStringAsFixed(1)}%" : ""})',
                    style: TextStyle(
                      color: estPnl >= 0 ? AppColors.positive : AppColors.negative,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ],
            ),
            if (hasStopLoss) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  Icon(Icons.shield, size: 14,
                      color: stopLossHit ? AppColors.negative : AppColors.gold),
                  const SizedBox(width: 4),
                  Text(
                    'Stop Loss: \$${widget.trades.first.stopLoss!.toStringAsFixed(2)}',
                    style: TextStyle(
                      color: stopLossHit
                          ? AppColors.negative
                          : AppColors.textSecondary,
                      fontSize: 11,
                      fontWeight:
                          stopLossHit ? FontWeight.w600 : FontWeight.normal,
                    ),
                  ),
                  if (stopLossHit) ...[
                    const SizedBox(width: 6),
                    const Icon(Icons.warning_amber, size: 14,
                        color: AppColors.negative),
                    const Text(' HIT!',
                        style: TextStyle(
                            color: AppColors.negative,
                            fontSize: 11,
                            fontWeight: FontWeight.w700)),
                  ],
                ],
              ),
            ],
            const SizedBox(height: 8),
            Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.refresh, size: 20),
                  onPressed: _fetchingPrice ? null : _fetchPrice,
                  tooltip: 'Refresh',
                ),
                const Spacer(),
                if (widget.trades.length == 1 &&
                    widget.trades.first.quantity > 1)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: SizedBox(
                      width: 80,
                      height: 40,
                      child: TextFormField(
                        controller: _qtyController,
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: const InputDecoration(
                          hintText: 'Qty',
                          contentPadding:
                              EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                          isDense: true,
                          border: OutlineInputBorder(),
                        ),
                        style: const TextStyle(fontSize: 13),
                      ),
                    ),
                  ),
                if (widget.trades.length == 1 &&
                    widget.trades.first.quantity > 1)
                  OutlinedButton(
                    onPressed: _livePrice == null
                        ? null
                        : () {
                            final qty = double.tryParse(
                                _qtyController.text.trim());
                            if (qty != null && qty > 0) {
                              _closeTrade(widget.trades.first, quantity: qty);
                            }
                          },
                    child: const Text('Close Qty', style: TextStyle(fontSize: 12)),
                  ),
                const SizedBox(width: 6),
                FilledButton(
                  onPressed: _livePrice == null ? null : () {
                    if (widget.trades.length == 1) {
                      _closeTrade(widget.trades.first);
                    } else {
                      for (final t in widget.trades) {
                        _closeTrade(t);
                      }
                    }
                  },
                  child: Text(
                      widget.trades.length > 1 ? 'Close All' : 'Close',
                      style: const TextStyle(fontSize: 12)),
                ),
              ],
            ),
            if (widget.trades.length > 1) ...[
              const SizedBox(height: 4),
              InkWell(
                onTap: () => setState(() => _showDetails = !_showDetails),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(_showDetails
                        ? Icons.expand_less
                        : Icons.expand_more,
                        size: 16, color: AppColors.textSecondary),
                    Text(
                        '${widget.trades.length} positions',
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 11)),
                  ],
                ),
              ),
              if (_showDetails)
                ...widget.trades.map((t) => Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Row(
                        children: [
                          Icon(Icons.circle, size: 6,
                              color: AppColors.textSecondary.withOpacity(0.5)),
                          const SizedBox(width: 6),
                          Text(
                            '#${t.id}  ·  \$${t.priceOpen.toStringAsFixed(2)} × ${t.quantity.toStringAsFixed(0)}',
                            style: const TextStyle(
                                color: AppColors.textSecondary, fontSize: 11),
                          ),
                          const Spacer(),
                          TextButton(
                            onPressed: _livePrice == null
                                ? null
                                : () => _closeTrade(t),
                            child: const Text('Close', style: TextStyle(fontSize: 11)),
                          ),
                        ],
                      ),
                    )),
            ],
          ],
        ),
      ),
    );
  }
}

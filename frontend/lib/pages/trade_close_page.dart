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
      appBar: AppBar(title: const Text('Close Trade')),
      body: tradesAsync.when(
        data: (trades) {
          final openTrades = trades.where((t) => t.status == 'open').toList();
          if (openTrades.isEmpty) {
            return const Center(child: Text('No open trades'));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: openTrades.length,
            itemBuilder: (context, index) {
              final trade = openTrades[index];
              return _OpenTradeTile(trade: trade);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _OpenTradeTile extends ConsumerStatefulWidget {
  final Trade trade;
  const _OpenTradeTile({required this.trade});

  @override
  ConsumerState<_OpenTradeTile> createState() => _OpenTradeTileState();
}

class _OpenTradeTileState extends ConsumerState<_OpenTradeTile> {
  double? _livePrice;
  bool _closing = false;
  bool _fetchingPrice = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _fetchPrice());
  }

  Future<void> _fetchPrice() async {
    if (_fetchingPrice) return;
    setState(() => _fetchingPrice = true);
    try {
      final notifier = ref.read(priceMapProvider.notifier);
      final price = await notifier.fetchPrice(widget.trade.symbol);
      if (price != null && mounted) {
        setState(() => _livePrice = price.price);
      }
    } finally {
      if (mounted) setState(() => _fetchingPrice = false);
    }
  }

  Future<void> _closeTrade() async {
    if (_livePrice == null) {
      await _fetchPrice();
      if (_livePrice == null) return;
    }
    setState(() => _closing = true);
    try {
      await ref.read(tradesProvider.notifier).closeTrade(
            widget.trade.id,
            _livePrice!,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Trade closed successfully'),
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
    } finally {
      if (mounted) setState(() => _closing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final trade = widget.trade;
    final isLong = trade.direction == 'LONG';
    final estPnl = _livePrice != null
        ? isLong
            ? (_livePrice! - trade.priceOpen) * trade.quantity
            : (trade.priceOpen - _livePrice!) * trade.quantity
        : null;

    return TradeCard(
      trade: trade,
      trailing: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (_livePrice != null)
            Text(
              '\$${_livePrice!.toStringAsFixed(2)}',
              style: const TextStyle(
                color: AppColors.gold,
                fontWeight: FontWeight.bold,
              ),
            )
          else if (_fetchingPrice)
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: AppColors.gold,
              ),
            ),
          if (estPnl != null)
            Text(
              '${estPnl >= 0 ? "+" : ""}\$${estPnl.toStringAsFixed(2)}',
              style: TextStyle(
                color: estPnl >= 0 ? AppColors.positive : AppColors.negative,
                fontSize: 12,
              ),
            ),
          const SizedBox(height: 4),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(
                icon: const Icon(Icons.refresh, size: 20),
                onPressed: _fetchingPrice ? null : _fetchPrice,
                tooltip: 'Refresh live price',
              ),
              FilledButton(
                onPressed: _closing || _fetchingPrice ? null : _closeTrade,
                child: _closing
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : _livePrice != null
                        ? const Text('Close')
                        : const Text('Close', style: TextStyle(color: Colors.white70)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../providers/price_provider.dart';
import '../providers/trade_provider.dart';

class TradeOpenPage extends ConsumerStatefulWidget {
  const TradeOpenPage({super.key});

  @override
  ConsumerState<TradeOpenPage> createState() => _TradeOpenPageState();
}

class _TradeOpenPageState extends ConsumerState<TradeOpenPage> {
  final _formKey = GlobalKey<FormState>();
  final _symbolController = TextEditingController();
  final _assetController = TextEditingController();
  final _quantityController = TextEditingController();
  final _costController = TextEditingController();
  String _direction = 'LONG';
  String _market = 'crypto';
  double? _livePrice;

  @override
  void dispose() {
    _symbolController.dispose();
    _assetController.dispose();
    _quantityController.dispose();
    _costController.dispose();
    super.dispose();
  }

  Future<void> _fetchLivePrice() async {
    final symbol = _symbolController.text.trim().toUpperCase();
    if (symbol.isEmpty) return;
    final notifier = ref.read(priceMapProvider.notifier);
    final price = await notifier.fetchPrice(symbol);
    if (price != null && mounted) {
      setState(() {
        _livePrice = price.price;
        _costController.text =
            (price.price * (double.tryParse(_quantityController.text) ?? 0))
                .toStringAsFixed(2);
      });
    }
  }

  Future<void> _submitTrade() async {
    if (!_formKey.currentState!.validate()) return;

    final data = {
      'asset': _assetController.text.trim(),
      'symbol': _symbolController.text.trim().toUpperCase(),
      'market': _market,
      'direction': _direction,
      'price_open': _livePrice ?? double.tryParse(_costController.text) ?? 0,
      'quantity': double.tryParse(_quantityController.text) ?? 0,
      'cost': double.tryParse(_costController.text) ?? 0,
    };

    try {
      await ref.read(tradesProvider.notifier).openTrade(data);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Trade opened successfully'),
            backgroundColor: AppColors.positive,
          ),
        );
        Navigator.of(context).pop();
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
    return Scaffold(
      appBar: AppBar(title: const Text('Open Trade')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'LONG', label: Text('LONG')),
                  ButtonSegment(value: 'SHORT', label: Text('SHORT')),
                ],
                selected: {_direction},
                onSelectionChanged: (v) => setState(() => _direction = v.first),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _market,
                decoration: const InputDecoration(
                  labelText: 'Market',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'crypto', child: Text('Crypto')),
                  DropdownMenuItem(value: 'technologie', child: Text('Technology')),
                  DropdownMenuItem(value: 'rohstoffe', child: Text('Commodities')),
                  DropdownMenuItem(value: 'forex', child: Text('Forex')),
                  DropdownMenuItem(value: 'etf', child: Text('ETF')),
                ],
                onChanged: (v) => setState(() => _market = v!),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _symbolController,
                      decoration: const InputDecoration(
                        labelText: 'Symbol',
                        border: OutlineInputBorder(),
                      ),
                      validator: (v) => v?.isEmpty == true ? 'Required' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _fetchLivePrice,
                    icon: const Icon(Icons.refresh),
                    tooltip: 'Get live price',
                  ),
                ],
              ),
              if (_livePrice != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    'Live price: \$${_livePrice!.toStringAsFixed(2)}',
                    style: TextStyle(color: AppColors.gold),
                  ),
                ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _assetController,
                decoration: const InputDecoration(
                  labelText: 'Asset name',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => v?.isEmpty == true ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _quantityController,
                decoration: const InputDecoration(
                  labelText: 'Quantity',
                  border: OutlineInputBorder(),
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) => v?.isEmpty == true ? 'Required' : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _costController,
                decoration: const InputDecoration(
                  labelText: 'Cost (\$)',
                  border: OutlineInputBorder(),
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) => v?.isEmpty == true ? 'Required' : null,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _submitTrade,
                child: Text(
                  'Open ${_direction} Trade',
                  style: const TextStyle(fontSize: 16),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
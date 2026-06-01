import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../providers/price_provider.dart';
import '../providers/trade_provider.dart';
import '../services/asset_search_service.dart';

class TradeOpenPage extends ConsumerStatefulWidget {
  const TradeOpenPage({super.key});

  @override
  ConsumerState<TradeOpenPage> createState() => _TradeOpenPageState();
}

class _TradeOpenPageState extends ConsumerState<TradeOpenPage> {
  final _formKey = GlobalKey<FormState>();
  final _searchController = TextEditingController();
  final _quantityController = TextEditingController();
  final _stopLossController = TextEditingController();
  String _direction = 'LONG';
  String _market = 'crypto';
  String? _selectedSymbol;
  String _assetName = '';
  double? _livePrice;
  bool _searching = false;
  List<AssetResult> _suggestions = [];
  bool _submitting = false;

  @override
  void dispose() {
    _searchController.dispose();
    _quantityController.dispose();
    _stopLossController.dispose();
    super.dispose();
  }

  Future<void> _onSearchChanged(String query) async {
    if (query.isEmpty) {
      setState(() => _suggestions = []);
      return;
    }
    setState(() => _searching = true);
    try {
      final service = ref.read(assetSearchServiceProvider);
      final results = await service.search(query);
      if (mounted) {
        setState(() {
          _suggestions = results;
          _searching = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _searching = false);
    }
  }

  void _onAssetSelected(AssetResult asset) {
    setState(() {
      _assetName = asset.name;
      _selectedSymbol = asset.symbol;
      _market = asset.market;
      _suggestions = [];
      _searchController.text = '${asset.name} (${asset.symbol})';
    });
    _fetchLivePrice();
  }

  Future<void> _fetchLivePrice() async {
    if (_selectedSymbol == null) return;
    final notifier = ref.read(priceMapProvider.notifier);
    final price = await notifier.fetchPrice(_selectedSymbol!);
    if (price != null && mounted) {
      setState(() {
        _livePrice = price.price;
        _quantityController.text = _quantityController.text.isEmpty
            ? '1'
            : _quantityController.text;
      });
    }
  }

  double get _cost =>
      (_livePrice ?? 0) *
      (double.tryParse(_quantityController.text) ?? 0);

  Future<void> _submitTrade() async {
    if (_selectedSymbol == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please search and select an asset first'),
          backgroundColor: AppColors.negative,
        ),
      );
      return;
    }

    setState(() => _submitting = true);

    final data = {
      'asset': _assetName,
      'symbol': _selectedSymbol!,
      'market': _market,
      'direction': _direction,
      'price_open': _livePrice ?? 0,
      'quantity': double.tryParse(_quantityController.text) ?? 0,
      'cost': _cost,
      'stop_loss': double.tryParse(_stopLossController.text) ?? 0,
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
        setState(() {
          _searchController.clear();
          _selectedSymbol = null;
          _assetName = '';
          _livePrice = null;
          _quantityController.clear();
          _stopLossController.clear();
          _market = 'crypto';
          _submitting = false;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: $e'),
            backgroundColor: AppColors.negative,
          ),
        );
        setState(() => _submitting = false);
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
              // Direction selector
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'LONG', label: Text('LONG')),
                  ButtonSegment(value: 'SHORT', label: Text('SHORT')),
                ],
                selected: {_direction},
                onSelectionChanged: (v) =>
                    setState(() => _direction = v.first),
              ),
              const SizedBox(height: 16),

              // Asset autocomplete search
              Autocomplete<AssetResult>(
                optionsBuilder: (TextEditingValue value) {
                  if (value.text.length < 2) return const Iterable.empty();
                  return _suggestions;
                },
                displayStringForOption: (AssetResult option) =>
                    '${option.name} (${option.symbol})',
                fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
                  return TextFormField(
                    controller: controller,
                    focusNode: focusNode,
                    decoration: InputDecoration(
                      labelText: 'Search asset...',
                      hintText: 'e.g. BTC, Gold, Apple...',
                      border: const OutlineInputBorder(),
                      suffixIcon: _selectedSymbol != null
                          ? IconButton(
                              icon: const Icon(Icons.clear),
                              onPressed: () {
                                setState(() {
                                  _searchController.clear();
                                  _selectedSymbol = null;
                                  _assetName = '';
                                  _livePrice = null;
                                  _suggestions = [];
                                });
                              },
                            )
                          : _searching
                              ? const Padding(
                                  padding: EdgeInsets.all(12),
                                  child: SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                    ),
                                  ),
                                )
                              : const Icon(Icons.search),
                    ),
                    onChanged: _onSearchChanged,
                    onFieldSubmitted: (_) => _fetchLivePrice(),
                  );
                },
                optionsViewBuilder: (context, onSelected, options) {
                  return Align(
                    alignment: Alignment.topLeft,
                    child: Material(
                      elevation: 4,
                      borderRadius: BorderRadius.circular(8),
                      color: AppColors.surface,
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxHeight: 280),
                        child: ListView.builder(
                          padding: EdgeInsets.zero,
                          shrinkWrap: true,
                          itemCount: options.length,
                          itemBuilder: (context, index) {
                            final asset = options.elementAt(index);
                            return ListTile(
                              dense: true,
                              title: Text(
                                asset.name,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                              subtitle: Text(
                                '${asset.symbol} · ${asset.market}',
                                style: const TextStyle(fontSize: 12),
                              ),
                              onTap: () => onSelected(asset),
                            );
                          },
                        ),
                      ),
                    ),
                  );
                },
                onSelected: _onAssetSelected,
              ),
              const SizedBox(height: 12),

              // Selected asset info
              if (_selectedSymbol != null)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _assetName,
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 18,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Symbol: $_selectedSymbol · Market: $_market',
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        if (_livePrice != null) ...[
                          const SizedBox(height: 8),
                          Text(
                            'Live price: \$${_livePrice!.toStringAsFixed(2)}',
                            style: const TextStyle(
                              color: AppColors.gold,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              const SizedBox(height: 16),

              // Quantity
              TextFormField(
                controller: _quantityController,
                decoration: const InputDecoration(
                  labelText: 'Quantity',
                  border: OutlineInputBorder(),
                ),
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 8),

              // Stop Loss
              TextFormField(
                controller: _stopLossController,
                decoration: const InputDecoration(
                  labelText: 'Stop Loss (optional)',
                  hintText: 'e.g. 95000',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.shield, size: 18),
                ),
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: 8),

              // Cost preview
              if (_livePrice != null && _quantityController.text.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    'Total cost: \$${_cost.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: _cost > 0 ? AppColors.positive : AppColors.textSecondary,
                        ),
                  ),
                ),
              const SizedBox(height: 8),

              // Refresh price button
              if (_selectedSymbol != null)
                OutlinedButton.icon(
                  onPressed: _fetchLivePrice,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Refresh live price'),
                ),
              const SizedBox(height: 16),

              // Submit
              ElevatedButton(
                onPressed: _submitting ? null : _submitTrade,
                child: _submitting
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : Text(
                        'Open $_direction Trade',
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

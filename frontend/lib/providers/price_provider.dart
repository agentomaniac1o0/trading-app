import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/price.dart';
import '../services/price_service.dart';

final priceMapProvider =
    AsyncNotifierProvider<PriceNotifier, Map<String, Price>>(
        PriceNotifier.new);

class PriceNotifier extends AsyncNotifier<Map<String, Price>> {
  @override
  Future<Map<String, Price>> build() async {
    return {};
  }

  Future<void> fetchPrices(List<String> symbols) async {
    final service = ref.watch(priceServiceProvider);
    final prices = await service.getPrices(symbols);
    state = AsyncData(prices);
  }

  Future<Price?> fetchPrice(String symbol) async {
    final service = ref.watch(priceServiceProvider);
    try {
      final price = await service.getPrice(symbol);
      final current = state.value ?? {};
      current[symbol] = price;
      state = AsyncData(Map.from(current));
      return price;
    } catch (e) {
      debugPrint('Price fetch failed: $e');
      return null;
    }
  }
}
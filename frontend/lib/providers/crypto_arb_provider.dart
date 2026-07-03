import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';

final _cryptoArbRefreshKey = StateProvider<int>((ref) => 0);

final cryptoArbSummaryProvider = FutureProvider<Map<String, dynamic>?>(
  (ref) async {
    ref.watch(_cryptoArbRefreshKey);
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/crypto-arb/summary');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Crypto-Arb summary fetch failed: $e');
      return null;
    }
  },
);

final cryptoArbPositionsProvider = FutureProvider<List<dynamic>>(
  (ref) async {
    ref.watch(_cryptoArbRefreshKey);
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/crypto-arb/positions/active');
      return response.data as List<dynamic>;
    } catch (e) {
      debugPrint('Crypto-Arb positions fetch failed: $e');
      return [];
    }
  },
);

final cryptoArbHistoryProvider = FutureProvider<List<dynamic>>(
  (ref) async {
    ref.watch(_cryptoArbRefreshKey);
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/crypto-arb/history');
      return (response.data as List<dynamic>).reversed.toList();
    } catch (e) {
      debugPrint('Crypto-Arb history fetch failed: $e');
      return [];
    }
  },
);

final cryptoArbPortfolioProvider = FutureProvider<Map<String, dynamic>?>(
  (ref) async {
    ref.watch(_cryptoArbRefreshKey);
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/crypto-arb/portfolio');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Crypto-Arb portfolio fetch failed: $e');
      return null;
    }
  },
);

final cryptoArbActivityProvider = FutureProvider<List<dynamic>>(
  (ref) async {
    ref.watch(_cryptoArbRefreshKey);
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/crypto-arb/activity?limit=100');
      return response.data as List<dynamic>;
    } catch (e) {
      debugPrint('Crypto-Arb activity fetch failed: $e');
      return [];
    }
  },
);

void refreshCryptoArb(WidgetRef ref) {
  ref.read(_cryptoArbRefreshKey.notifier).state++;
}

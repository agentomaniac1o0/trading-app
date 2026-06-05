import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../services/api_client.dart';

final _reportRefreshKey = StateProvider.family<int, String>((ref, category) => 0);

final marketReportProvider = FutureProvider.family<Map<String, dynamic>?, String>(
  (ref, category) async {
    ref.watch(_reportRefreshKey(category));
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get(
        '/api/reports/market/$category',
        options: Options(headers: {'Cache-Control': 'no-cache'}),
      );
      return response.data as Map<String, dynamic>;
    } catch (e) {
      debugPrint('Market report fetch failed: $e');
      return null;
    }
  },
);

void refreshMarketReport(WidgetRef ref, String category) {
  ref.read(_reportRefreshKey(category).notifier).state++;
}

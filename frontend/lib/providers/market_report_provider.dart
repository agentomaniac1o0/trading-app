import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_client.dart';

final marketReportProvider = FutureProvider.family<Map<String, dynamic>?, String>(
  (ref, category) async {
    final client = ref.watch(apiClientProvider);
    try {
      final response = await client.get('/api/reports/market/$category');
      return response.data as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  },
);

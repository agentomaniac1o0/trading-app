import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/portfolio.dart';
import '../services/api_client.dart';

final portfolioProvider =
    AsyncNotifierProvider<PortfolioNotifier, PortfolioSummary?>(
        PortfolioNotifier.new);

class PortfolioNotifier extends AsyncNotifier<PortfolioSummary?> {
  @override
  Future<PortfolioSummary?> build() async {
    final client = ref.watch(apiClientProvider);
    final response = await client.get('/api/portfolio');
    return PortfolioSummary.fromJson(response.data);
  }

  Future<void> refresh() async {
    ref.invalidateSelf();
  }
}
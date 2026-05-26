import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/trade.dart';
import '../services/api_client.dart';
import 'live_portfolio_provider.dart';
import 'portfolio_provider.dart';
import 'portfolio_review_provider.dart';

final tradesProvider =
    AsyncNotifierProvider<TradesNotifier, List<Trade>>(TradesNotifier.new);

class TradesNotifier extends AsyncNotifier<List<Trade>> {
  @override
  Future<List<Trade>> build() async {
    final client = ref.watch(apiClientProvider);
    final response = await client.get('/api/trades', queryParameters: {
      'limit': 200,
    });
    return (response.data as List)
        .map((e) => Trade.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Trade> openTrade(Map<String, dynamic> data) async {
    final client = ref.watch(apiClientProvider);
    final response = await client.post('/api/trades', data: data);
    final trade = Trade.fromJson(response.data);
    ref.invalidateSelf();
    ref.invalidate(portfolioProvider);
    ref.invalidate(livePortfolioProvider);
    return trade;
  }

  Future<Trade> closeTrade(String tradeId, double priceClose, {double? quantityClose}) async {
    final client = ref.watch(apiClientProvider);
    final data = <String, dynamic>{'price_close': priceClose};
    if (quantityClose != null && quantityClose > 0) {
      data['quantity_close'] = quantityClose;
    }
    final response = await client.patch('/api/trades/$tradeId/close', data: data);
    final remaining = response.data is Map<String, dynamic> ? Trade.fromJson(response.data) : null;
    ref.invalidateSelf();
    ref.invalidate(portfolioProvider);
    ref.invalidate(livePortfolioProvider);
    ref.invalidate(portfolioReviewProvider);
    return remaining ?? Trade.fromJson(response.data);
  }
}
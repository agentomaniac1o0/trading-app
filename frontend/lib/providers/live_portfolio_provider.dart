import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/live_portfolio.dart';
import '../services/api_client.dart';
import 'package:dio/dio.dart';
import 'portfolio_provider.dart';
import 'trade_provider.dart';

final livePortfolioProvider = FutureProvider<LivePortfolio?>((ref) async {
  final client = ref.watch(apiClientProvider);
  try {
    final response = await client.get('/api/portfolio/live');
    return LivePortfolio.fromJson(response.data as Map<String, dynamic>);
  } on DioException {
    return null;
  }
});

final refreshAllProviders = Provider<void Function()>((ref) {
  return () {
    ref.invalidate(livePortfolioProvider);
    ref.invalidate(portfolioProvider);
    ref.invalidate(tradesProvider);
  };
});

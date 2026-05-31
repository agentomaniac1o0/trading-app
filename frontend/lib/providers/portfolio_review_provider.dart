import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/portfolio_review.dart';
import '../services/api_client.dart';
import 'package:dio/dio.dart';

final portfolioReviewProvider = FutureProvider<PortfolioReview?>((ref) async {
  final client = ref.watch(apiClientProvider);
  try {
    final response = await client.get(
      '/api/portfolio/review',
      options: Options(headers: {'Cache-Control': 'no-cache'}),
    );
    if (response.data == null) return null;
    return PortfolioReview.fromJson(response.data as Map<String, dynamic>);
  } on DioException {
    return null;
  }
});

void refreshPortfolioReview(WidgetRef ref) {
  ref.invalidate(portfolioReviewProvider);
}

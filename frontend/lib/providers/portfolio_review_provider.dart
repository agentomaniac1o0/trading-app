import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/portfolio_review.dart';
import '../services/api_client.dart';
import 'package:dio/dio.dart';

final portfolioReviewProvider = FutureProvider<PortfolioReview?>((ref) async {
  final client = ref.watch(apiClientProvider);
  try {
    final response = await client.get('/api/reports/portfolio-review');
    if (response.data == null) return null;
    return PortfolioReview.fromJson(response.data as Map<String, dynamic>);
  } on DioException {
    return null;
  }
});

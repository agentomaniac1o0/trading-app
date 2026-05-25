import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/trader_profile.dart';
import '../services/api_client.dart';
import 'package:dio/dio.dart';

final tradersProvider = FutureProvider<List<TraderProfile>>((ref) async {
  final client = ref.watch(apiClientProvider);
  try {
    final response = await client.get('/api/traders');
    return (response.data as List)
        .map((e) => TraderProfile.fromJson(e as Map<String, dynamic>))
        .toList();
  } on DioException {
    return [];
  }
});

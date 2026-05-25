import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';
import '../models/price.dart';
import 'api_client.dart';

final priceServiceProvider = Provider<PriceService>((ref) {
  return PriceService(ref.watch(apiClientProvider));
});

class PriceService {
  final Dio _client;
  final Map<String, Price> _cache = {};

  PriceService(this._client);

  Future<Price> getPrice(String symbol) async {
    if (_cache.containsKey(symbol)) {
      final cached = _cache[symbol]!;
      final age = DateTime.now().difference(DateTime.parse(cached.timestamp));
      if (age.inSeconds < apiTimeout.inSeconds) {
        return cached;
      }
    }

    final response = await _client.get('/api/prices/${symbol.toUpperCase()}');
    final price = Price.fromJson(response.data);
    _cache[symbol] = price;
    return price;
  }

  Future<Map<String, Price>> getPrices(List<String> symbols) async {
    final results = <String, Price>{};
    for (final symbol in symbols) {
      try {
        results[symbol] = await getPrice(symbol);
      } catch (_) {}
    }
    return results;
  }

  Future<List<PricePoint>> getHistory(String symbol, {int days = 7}) async {
    final response = await _client.get(
      '/api/prices/${symbol.toUpperCase()}/history',
      queryParameters: {'days': days},
    );
    return (response.data as List)
        .map((e) => PricePoint.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}

class PricePoint {
  final String date;
  final double price;

  const PricePoint({required this.date, required this.price});

  factory PricePoint.fromJson(Map<String, dynamic> json) {
    return PricePoint(
      date: json['date'] as String,
      price: (json['price'] as num).toDouble(),
    );
  }
}
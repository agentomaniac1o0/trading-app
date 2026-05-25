import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api_client.dart';

class AssetResult {
  final String name;
  final String symbol;
  final String market;

  const AssetResult({
    required this.name,
    required this.symbol,
    required this.market,
  });

  factory AssetResult.fromJson(Map<String, dynamic> json) {
    return AssetResult(
      name: json['name'] as String,
      symbol: json['symbol'] as String,
      market: json['market'] as String,
    );
  }
}

final assetSearchServiceProvider = Provider<AssetSearchService>((ref) {
  return AssetSearchService(ref.watch(apiClientProvider));
});

class AssetSearchService {
  final Dio _client;

  AssetSearchService(this._client);

  Future<List<AssetResult>> search(String query) async {
    if (query.length < 2) return [];
    final response = await _client.get('/api/prices/search', queryParameters: {'q': query});
    return (response.data as List)
        .map((e) => AssetResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/api_config.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: apiBaseUrl,
    connectTimeout: apiTimeout,
    receiveTimeout: apiTimeout,
    headers: {'Content-Type': 'application/json'},
  ));
  return dio;
});

final apiClientProvider = Provider<Dio>((ref) => ref.watch(dioProvider));
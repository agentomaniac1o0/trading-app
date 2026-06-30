const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://100.112.199.58:8000',
);

const Duration apiTimeout = Duration(seconds: 10);
const Duration priceRefreshInterval = Duration(minutes: 1);
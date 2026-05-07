const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

const Duration apiTimeout = Duration(seconds: 10);
const Duration priceRefreshInterval = Duration(minutes: 1);
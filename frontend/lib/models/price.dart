class Price {
  final String symbol;
  final double price;
  final String currency;
  final String timestamp;
  final String source;

  const Price({
    required this.symbol,
    required this.price,
    required this.currency,
    required this.timestamp,
    required this.source,
  });

  factory Price.fromJson(Map<String, dynamic> json) {
    return Price(
      symbol: json['symbol'] as String,
      price: (json['price'] as num).toDouble(),
      currency: json['currency'] as String,
      timestamp: json['timestamp'] as String,
      source: json['source'] as String,
    );
  }
}
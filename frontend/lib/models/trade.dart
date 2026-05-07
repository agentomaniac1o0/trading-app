class Trade {
  final String id;
  final String dateOpen;
  final String asset;
  final String symbol;
  final String market;
  final String direction;
  final double priceOpen;
  final double quantity;
  final double cost;
  final String status;
  final String? dateClose;
  final double? priceClose;
  final double? pnl;
  final double? pnlPct;
  final String? signalSource;
  final String? notes;
  final String createdAt;
  final String updatedAt;

  const Trade({
    required this.id,
    required this.dateOpen,
    required this.asset,
    required this.symbol,
    required this.market,
    required this.direction,
    required this.priceOpen,
    required this.quantity,
    required this.cost,
    required this.status,
    this.dateClose,
    this.priceClose,
    this.pnl,
    this.pnlPct,
    this.signalSource,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Trade.fromJson(Map<String, dynamic> json) {
    return Trade(
      id: json['id'] as String,
      dateOpen: json['date_open'] as String,
      asset: json['asset'] as String,
      symbol: json['symbol'] as String,
      market: json['market'] as String,
      direction: json['direction'] as String,
      priceOpen: (json['price_open'] as num).toDouble(),
      quantity: (json['quantity'] as num).toDouble(),
      cost: (json['cost'] as num).toDouble(),
      status: json['status'] as String,
      dateClose: json['date_close'] as String?,
      priceClose: json['price_close'] != null
          ? (json['price_close'] as num).toDouble()
          : null,
      pnl: json['pnl'] != null ? (json['pnl'] as num).toDouble() : null,
      pnlPct:
          json['pnl_pct'] != null ? (json['pnl_pct'] as num).toDouble() : null,
      signalSource: json['signal_source'] as String?,
      notes: json['notes'] as String?,
      createdAt: json['created_at'] as String,
      updatedAt: json['updated_at'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
        'asset': asset,
        'symbol': symbol,
        'market': market,
        'direction': direction,
        'price_open': priceOpen,
        'quantity': quantity,
        'cost': cost,
        'signal_source': signalSource,
        'notes': notes,
      };
}
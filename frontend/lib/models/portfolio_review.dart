class TraderJudgment {
  final String trader;
  final String judgment;
  final String reason;

  const TraderJudgment({
    required this.trader,
    required this.judgment,
    required this.reason,
  });

  factory TraderJudgment.fromJson(Map<String, dynamic> json) {
    return TraderJudgment(
      trader: json['trader'] as String,
      judgment: json['judgment'] as String,
      reason: json['reason'] as String,
    );
  }
}

class PortfolioReviewAsset {
  final String name;
  final String symbol;
  final String direction;
  final int quantity;
  final double livePrice;
  final double pnlPct;
  final List<TraderJudgment> judgments;

  const PortfolioReviewAsset({
    required this.name,
    required this.symbol,
    required this.direction,
    required this.quantity,
    required this.livePrice,
    required this.pnlPct,
    required this.judgments,
  });

  factory PortfolioReviewAsset.fromJson(Map<String, dynamic> json) {
    return PortfolioReviewAsset(
      name: json['name'] as String,
      symbol: json['symbol'] as String,
      direction: json['direction'] as String,
      quantity: json['quantity'] as int,
      livePrice: (json['live_price'] as num).toDouble(),
      pnlPct: (json['pnl_pct'] as num).toDouble(),
      judgments: (json['judgments'] as List)
          .map((e) => TraderJudgment.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PortfolioReview {
  final String reportDate;
  final List<PortfolioReviewAsset> assets;

  const PortfolioReview({
    required this.reportDate,
    required this.assets,
  });

  factory PortfolioReview.fromJson(Map<String, dynamic> json) {
    return PortfolioReview(
      reportDate: json['report_date'] as String,
      assets: (json['assets'] as List)
          .map((e) => PortfolioReviewAsset.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

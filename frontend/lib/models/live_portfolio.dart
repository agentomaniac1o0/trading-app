class LivePosition {
  final String id;
  final String symbol;
  final String asset;
  final String direction;
  final double priceOpen;
  final double quantity;
  final double cost;
  final double priceCurrent;
  final double marketValue;
  final double unrealizedPnl;
  final double unrealizedPnlPct;

  const LivePosition({
    required this.id,
    required this.symbol,
    required this.asset,
    required this.direction,
    required this.priceOpen,
    required this.quantity,
    required this.cost,
    required this.priceCurrent,
    required this.marketValue,
    required this.unrealizedPnl,
    required this.unrealizedPnlPct,
  });

  factory LivePosition.fromJson(Map<String, dynamic> json) {
    return LivePosition(
      id: json['id'] as String,
      symbol: json['symbol'] as String,
      asset: json['asset'] as String,
      direction: json['direction'] as String,
      priceOpen: (json['price_open'] as num).toDouble(),
      quantity: (json['quantity'] as num).toDouble(),
      cost: (json['cost'] as num).toDouble(),
      priceCurrent: (json['price_current'] as num).toDouble(),
      marketValue: (json['market_value'] as num).toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] as num).toDouble(),
      unrealizedPnlPct: (json['unrealized_pnl_pct'] as num).toDouble(),
    );
  }
}

class LivePortfolio {
  final double initialCapital;
  final double cash;
  final double investedCost;
  final double investedMarket;
  final double portfolioValue;
  final double totalPnl;
  final double totalPnlPct;
  final double unrealizedPnl;
  final double realizedPnl;
  final int openPositions;
  final int closedTrades;
  final double winRate;
  final List<LivePosition> positions;

  const LivePortfolio({
    required this.initialCapital,
    required this.cash,
    required this.investedCost,
    required this.investedMarket,
    required this.portfolioValue,
    required this.totalPnl,
    required this.totalPnlPct,
    required this.unrealizedPnl,
    required this.realizedPnl,
    required this.openPositions,
    required this.closedTrades,
    required this.winRate,
    required this.positions,
  });

  factory LivePortfolio.fromJson(Map<String, dynamic> json) {
    return LivePortfolio(
      initialCapital: (json['initial_capital'] as num).toDouble(),
      cash: (json['cash'] as num).toDouble(),
      investedCost: (json['invested_cost'] as num).toDouble(),
      investedMarket: (json['invested_market'] as num).toDouble(),
      portfolioValue: (json['portfolio_value'] as num).toDouble(),
      totalPnl: (json['total_pnl'] as num).toDouble(),
      totalPnlPct: (json['total_pnl_pct'] as num).toDouble(),
      unrealizedPnl: (json['unrealized_pnl'] as num).toDouble(),
      realizedPnl: (json['realized_pnl'] as num).toDouble(),
      openPositions: json['open_positions'] as int,
      closedTrades: json['closed_trades'] as int,
      winRate: (json['win_rate'] as num).toDouble(),
      positions: (json['positions'] as List)
          .map((e) => LivePosition.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

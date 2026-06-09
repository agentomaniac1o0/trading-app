class PortfolioSummary {
  final double initialCapital;
  final double cash;
  final double shortExposure;
  final double netAvailable;
  final double invested;
  final double portfolioValue;
  final double totalPnl;
  final double totalPnlPct;
  final int openPositions;
  final int closedTrades;
  final double winRate;

  const PortfolioSummary({
    required this.initialCapital,
    required this.cash,
    required this.shortExposure,
    required this.netAvailable,
    required this.invested,
    required this.portfolioValue,
    required this.totalPnl,
    required this.totalPnlPct,
    required this.openPositions,
    required this.closedTrades,
    required this.winRate,
  });

  factory PortfolioSummary.fromJson(Map<String, dynamic> json) {
    return PortfolioSummary(
      initialCapital: (json['initial_capital'] as num).toDouble(),
      cash: (json['cash'] as num).toDouble(),
      shortExposure: (json['short_exposure'] as num).toDouble(),
      netAvailable: (json['net_available'] as num).toDouble(),
      invested: (json['invested'] as num).toDouble(),
      portfolioValue: (json['portfolio_value'] as num).toDouble(),
      totalPnl: (json['total_pnl'] as num).toDouble(),
      totalPnlPct: (json['total_pnl_pct'] as num).toDouble(),
      openPositions: json['open_positions'] as int,
      closedTrades: json['closed_trades'] as int,
      winRate: (json['win_rate'] as num).toDouble(),
    );
  }
}
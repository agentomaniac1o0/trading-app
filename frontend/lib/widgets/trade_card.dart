import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/trade.dart';
import 'ampel_indicator.dart';

class TradeCard extends StatelessWidget {
  final Trade trade;
  final Widget? trailing;

  const TradeCard({super.key, required this.trade, this.trailing});

  @override
  Widget build(BuildContext context) {
    final isLong = trade.direction == 'LONG';
    final directionColor = isLong ? AppColors.positive : AppColors.negative;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      AmpelIndicator(color: directionColor),
                      const SizedBox(width: 6),
                      Text(
                        trade.symbol,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: directionColor.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          trade.direction,
                          style: TextStyle(color: directionColor, fontSize: 11),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    trade.asset,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Open: \$${trade.priceOpen.toStringAsFixed(2)} × ${trade.quantity} = \$${trade.cost.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  if (trade.status == 'closed' && trade.pnl != null) ...[
                    const SizedBox(height: 2),
                    Text(
                      'P&L: ${trade.pnl! >= 0 ? "+" : ""}\$${trade.pnl!.toStringAsFixed(2)} (${trade.pnlPct?.toStringAsFixed(1)}%)',
                      style: TextStyle(
                        color: trade.pnl! >= 0
                            ? AppColors.positive
                            : AppColors.negative,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (trailing != null) trailing!,
          ],
        ),
      ),
    );
  }
}
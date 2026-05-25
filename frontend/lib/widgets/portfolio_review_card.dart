import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/portfolio_review.dart';

class PortfolioReviewCard extends StatelessWidget {
  final PortfolioReview review;

  const PortfolioReviewCard({super.key, required this.review});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  'Portfolio-Asset Review',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const Spacer(),
                Text(
                  review.reportDate,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ...review.assets.map((asset) => _AssetReviewTile(asset: asset)),
          ],
        ),
      ),
    );
  }
}

class _AssetReviewTile extends StatelessWidget {
  final PortfolioReviewAsset asset;
  const _AssetReviewTile({required this.asset});

  @override
  Widget build(BuildContext context) {
    final isLong = asset.direction == 'LONG';
    final pnlColor = asset.pnlPct >= 0 ? AppColors.positive : AppColors.negative;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  color: isLong ? AppColors.positive : AppColors.negative,
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: (isLong ? AppColors.positive : AppColors.negative)
                          .withOpacity(0.3),
                      blurRadius: 3,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Text(
                asset.name,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(width: 6),
              Text(
                '(${asset.symbol})',
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                ),
              ),
              const Spacer(),
              Text(
                '\$${asset.livePrice.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: pnlColor.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  '${asset.pnlPct >= 0 ? "+" : ""}${asset.pnlPct.toStringAsFixed(2)}%',
                  style: TextStyle(
                    color: pnlColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Padding(
            padding: const EdgeInsets.only(left: 16),
            child: Column(
              children: asset.judgments.map((j) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 72,
                        child: Text(
                          _traderLabel(j.trader),
                          style: TextStyle(
                            color: _traderColor(j.trader),
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 1),
                        decoration: BoxDecoration(
                          color: _judgmentColor(j.judgment).withOpacity(0.15),
                          borderRadius: BorderRadius.circular(3),
                        ),
                        child: Text(
                          j.judgment,
                          style: TextStyle(
                            color: _judgmentColor(j.judgment),
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          j.reason,
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 11,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            ),
          ),
          if (asset != review.assets.last)
            const Padding(
              padding: EdgeInsets.only(left: 16, top: 4),
              child: Divider(height: 1),
            ),
        ],
      ),
    );
  }

  static String _traderLabel(String key) {
    return switch (key) {
      'buffett' => 'Buffett',
      'lynch' => 'Lynch',
      'soros' => 'Soros',
      'wood' => 'Wood',
      'saylor' => 'Saylor',
      _ => key,
    };
  }

  static Color _traderColor(String key) {
    return switch (key) {
      'buffett' => AppColors.gold,
      'lynch' => AppColors.positive,
      'soros' => AppColors.violet,
      'wood' => AppColors.blue,
      'saylor' => const Color(0xFFf7931a),
      _ => AppColors.textSecondary,
    };
  }

  static Color _judgmentColor(String judgment) {
    return switch (judgment) {
      'AUFSTOCKEN' || 'KAUFEN' => AppColors.positive,
      'HALTEN' || 'BEOBACHTEN' => AppColors.gold,
      'VERKAUFEN' => AppColors.negative,
      _ => AppColors.textSecondary,
    };
  }
}

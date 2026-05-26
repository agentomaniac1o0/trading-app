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
            ...review.assets.asMap().entries.map((e) => _AssetReviewTile(
                asset: e.value,
                isLast: e.key == review.assets.length - 1)),
            if (review.assets.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Divider(),
              const SizedBox(height: 8),
              _Kommentator(assets: review.assets),
            ],
          ],
        ),
      ),
    );
  }
}

class _AssetReviewTile extends StatelessWidget {
  final PortfolioReviewAsset asset;
  final bool isLast;
  const _AssetReviewTile({required this.asset, required this.isLast});

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
              children: [
                ...asset.judgments.map((j) {
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
                            color:
                                _judgmentColor(j.judgment).withOpacity(0.15),
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
                }),
                if (_needsStopLoss(asset)) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const SizedBox(width: 72),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: AppColors.negative.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(4),
                          border: Border.all(
                              color: AppColors.negative.withOpacity(0.3)),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.warning_amber_rounded,
                                size: 14, color: AppColors.negative),
                            SizedBox(width: 4),
                            Text(
                              'Stop-Loss empfohlen',
                              style: TextStyle(
                                color: AppColors.negative,
                                fontSize: 10,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          if (!isLast)
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

  static bool _needsStopLoss(PortfolioReviewAsset asset) {
    int sellCount = 0;
    for (final j in asset.judgments) {
      final upper = j.judgment.toUpperCase();
      if (upper.contains('VERKAUFEN') ||
          upper.contains('VERKAUF') ||
          upper.contains('STOP')) {
        sellCount++;
      }
    }
    return sellCount >= 2 || asset.pnlPct < -5;
  }
}

class _Kommentator extends StatelessWidget {
  final List<PortfolioReviewAsset> assets;
  const _Kommentator({required this.assets});

  @override
  Widget build(BuildContext context) {
    final summary = _generateSummary(assets);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.violet.withOpacity(0.08),
            AppColors.blue.withOpacity(0.06),
          ],
        ),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.violet.withOpacity(0.25)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.psychology, size: 16, color: AppColors.violet),
              const SizedBox(width: 6),
              const Text(
                'AI-Kommentator',
                style: TextStyle(
                  color: AppColors.violet,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            summary,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontSize: 12,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  String _generateSummary(List<PortfolioReviewAsset> assets) {
    if (assets.isEmpty) return 'Keine Daten für eine Analyse verfügbar.';

    int bullishCount = 0;
    int bearishCount = 0;
    int haltCount = 0;
    final riskAssets = <String>[];
    final strongAssets = <String>[];

    for (final a in assets) {
      int aBuy = 0, aSell = 0;
      for (final j in a.judgments) {
        final ju = j.judgment.toUpperCase();
        if (ju.contains('AUFSTOCKEN') || ju.contains('KAUFEN')) {
          bullishCount++;
          aBuy++;
        } else if (ju.contains('VERKAUFEN')) {
          bearishCount++;
          aSell++;
        } else {
          haltCount++;
        }
      }
      if (aSell >= 3) {
        riskAssets.add(a.name);
      }
      if (aBuy >= 4) {
        strongAssets.add(a.name);
      }
    }

    final total = bullishCount + bearishCount + haltCount;
    final bullPct = total > 0 ? (bullishCount / total * 100).round() : 0;
    final bearPct = total > 0 ? (bearishCount / total * 100).round() : 0;

    final buf = StringBuffer();

    if (bullPct > bearPct + 20) {
      buf.write('Das Sentiment ist überwiegend bullisch ($bullPct% Kauf-Signale). ');
    } else if (bearPct > bullPct + 20) {
      buf.write('Das Sentiment ist überwiegend bearisch ($bearPct% Verkauf-Signale). ');
    } else {
      buf.write('Das Sentiment ist gemischt ($bullPct% bullisch, $bearPct% bearisch). ');
    }

    if (strongAssets.isNotEmpty) {
      buf.write(
          'Starke Kauf-Signale bei: ${strongAssets.join(', ')}. ');
    }
    if (riskAssets.isNotEmpty) {
      buf.write(
          'Kritisches Sentiment bei: ${riskAssets.join(', ')} — Stop-Loss prüfen! ');
    }
    if (riskAssets.isEmpty && strongAssets.isEmpty) {
      buf.write(
          'Keine Extrem-Signale — Positionen beobachten. ');
    }

    buf.write(
        'Gesamteinschätzung: ${bullPct >= 60 ? 'Optimistisch' : bearPct >= 50 ? 'Defensiv agieren' : 'Selektiv handeln'}.');

    return buf.toString();
  }
}

import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/trader_profile.dart';

class TraderAvatarRow extends StatelessWidget {
  final List<TraderProfile> traders;

  const TraderAvatarRow({super.key, required this.traders});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: traders.map((trader) {
        return Padding(
          padding: const EdgeInsets.only(left: 4),
          child: Tooltip(
            richMessage: WidgetSpan(
              alignment: PlaceholderAlignment.baseline,
              baseline: TextBaseline.alphabetic,
              child: _TraderTooltip(trader: trader),
            ),
            triggerMode: TooltipTriggerMode.tap,
            child: CircleAvatar(
              radius: 14,
              backgroundColor: _parseColor(trader.color).withOpacity(0.2),
              foregroundImage: trader.avatarBytes != null
                  ? MemoryImage(trader.avatarBytes!)
                  : null,
              child: trader.avatarBytes == null
                  ? Text(
                      trader.name[0],
                      style: TextStyle(
                        color: _parseColor(trader.color),
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    )
                  : null,
            ),
          ),
        );
      }).toList(),
    );
  }

  static Color _parseColor(String hex) {
    final stripped = hex.replaceFirst('#', '');
    return Color(int.parse('FF$stripped', radix: 16));
  }
}

class _TraderTooltip extends StatelessWidget {
  final TraderProfile trader;
  const _TraderTooltip({required this.trader});

  @override
  Widget build(BuildContext context) {
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 240),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Text(trader.emoji, style: const TextStyle(fontSize: 16)),
              const SizedBox(width: 6),
              Text(
                trader.name,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ],
          ),
          const SizedBox(height: 2),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: TraderAvatarRow._parseColor(trader.color).withOpacity(0.2),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              trader.title,
              style: TextStyle(
                color: TraderAvatarRow._parseColor(trader.color),
                fontSize: 10,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            trader.bio,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 11,
              height: 1.3,
            ),
          ),
        ],
      ),
    );
  }
}

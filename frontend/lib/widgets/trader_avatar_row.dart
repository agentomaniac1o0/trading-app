import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/trader_profile.dart';

class TraderAvatarRow extends StatelessWidget {
  final List<TraderProfile> traders;

  const TraderAvatarRow({super.key, required this.traders});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        for (final trader in traders) _TraderTile(trader: trader),
      ],
    );
  }
}

class _TraderTile extends StatelessWidget {
  final TraderProfile trader;
  const _TraderTile({required this.trader});

  Color get _color {
    final stripped = trader.color.replaceFirst('#', '');
    return Color(int.parse('FF$stripped', radix: 16));
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: (MediaQuery.of(context).size.width - 60) / 2,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 18,
            backgroundColor: _color.withOpacity(0.15),
            backgroundImage: trader.avatarBytes != null
                ? MemoryImage(trader.avatarBytes!)
                : null,
            child: trader.avatarBytes == null
                ? Text(trader.name[0],
                    style: TextStyle(
                        color: _color, fontSize: 16, fontWeight: FontWeight.w700))
                : null,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  trader.name,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  trader.title,
                  style: const TextStyle(
                    color: AppColors.textSecondary,
                    fontSize: 11,
                    fontWeight: FontWeight.w400,
                  ),
                ),
                const SizedBox(height: 3),
                Wrap(
                  spacing: 4,
                  runSpacing: 2,
                  children: trader.traits.map(
                    (t) => Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: _color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(3),
                      ),
                      child: Text(
                        t,
                        style: TextStyle(
                          color: _color,
                          fontSize: 9,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

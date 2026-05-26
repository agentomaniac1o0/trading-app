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
      runSpacing: 8,
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
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        CircleAvatar(
          radius: 13,
          backgroundColor: _color.withOpacity(0.15),
          backgroundImage: trader.avatarBytes != null
              ? MemoryImage(trader.avatarBytes!)
              : null,
          child: trader.avatarBytes == null
              ? Text(trader.name[0],
                  style: TextStyle(
                      color: _color, fontSize: 12, fontWeight: FontWeight.w700))
              : null,
        ),
        const SizedBox(width: 6),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              trader.name,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
            Text(
              trader.traits.join(' · '),
              style: TextStyle(
                color: _color,
                fontSize: 9,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

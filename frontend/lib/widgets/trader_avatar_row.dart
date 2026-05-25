import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../models/trader_profile.dart';

class TraderAvatarRow extends StatelessWidget {
  final List<TraderProfile> traders;

  const TraderAvatarRow({super.key, required this.traders});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (final trader in traders)
            _TraderTile(trader: trader),
        ],
      ),
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
    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: _color.withOpacity(0.15),
            backgroundImage: trader.avatarBytes != null
                ? MemoryImage(trader.avatarBytes!)
                : null,
            child: trader.avatarBytes == null
                ? Text(trader.name[0],
                    style: TextStyle(
                        color: _color, fontSize: 14, fontWeight: FontWeight.w700))
                : null,
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                trader.name,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              ...trader.traits.map(
                (t) => Text(
                  t,
                  style: TextStyle(
                    color: _color,
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

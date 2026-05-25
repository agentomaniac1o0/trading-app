import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../services/price_service.dart';

class Sparkline extends StatelessWidget {
  final List<PricePoint> data;
  final double height;

  const Sparkline({super.key, required this.data, this.height = 60});

  @override
  Widget build(BuildContext context) {
    if (data.length < 2) {
      return SizedBox(height: height, child: const Center(child: Text('-')));
    }

    final spots = <FlSpot>[];
    final minY = data.map((p) => p.price).reduce((a, b) => a < b ? a : b);
    final maxY = data.map((p) => p.price).reduce((a, b) => a > b ? a : b);
    final range = maxY - minY;
    final isUp = data.last.price >= data.first.price;
    final color = isUp ? AppColors.positive : AppColors.negative;

    for (int i = 0; i < data.length; i++) {
      spots.add(FlSpot(i.toDouble(), data[i].price));
    }

    return SizedBox(
      height: height,
      child: LineChart(
        LineChartData(
          minY: minY - range * 0.1,
          maxY: maxY + range * 0.1,
          gridData: const FlGridData(show: false),
          titlesData: const FlTitlesData(show: false),
          borderData: FlBorderData(show: false),
          lineBarsData: [
            LineChartBarData(
              spots: spots,
              isCurved: true,
              curveSmoothness: 0.3,
              color: color,
              barWidth: 2,
              dotData: const FlDotData(show: false),
              belowBarData: BarAreaData(
                show: true,
                color: color.withOpacity(0.08),
              ),
            ),
          ],
          lineTouchData: LineTouchData(
            enabled: true,
            touchTooltipData: LineTouchTooltipData(
              getTooltipItems: (spots) => spots
                  .map((s) => LineTooltipItem(
                        '\$${s.y.toStringAsFixed(2)}',
                        const TextStyle(
                          color: Colors.white,
                          fontSize: 11,
                        ),
                      ))
                  .toList(),
            ),
          ),
        ),
      ),
    );
  }
}

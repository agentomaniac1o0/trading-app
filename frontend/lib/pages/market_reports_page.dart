import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/theme.dart';
import '../providers/market_report_provider.dart';

const _categories = [
  _Category('crashprophet', 'Crash Prophet', Icons.warning_amber, AppColors.negative),
  _Category('diamondhands', 'Diamond Hands', Icons.diamond, AppColors.blue),
  _Category('cryptoanalysis', 'Crypto Analysis', Icons.currency_bitcoin, AppColors.violet),
  _Category('equities', 'Equities', Icons.show_chart, AppColors.positive),
  _Category('forex', 'Forex', Icons.swap_horiz, AppColors.gold),
  _Category('commodities', 'Commodities', Icons.water_drop, Color(0xFFcd853f)),
  _Category('real-estate', 'Real Estate', Icons.house, Color(0xFF2e8b57)),
  _Category('trader-perspectives', 'Trader Perspectives', Icons.psychology, AppColors.gold),
];

class _Category {
  final String key;
  final String label;
  final IconData icon;
  final Color color;
  const _Category(this.key, this.label, this.icon, this.color);
}

class MarketReportsPage extends ConsumerStatefulWidget {
  const MarketReportsPage({super.key});

  @override
  ConsumerState<MarketReportsPage> createState() => _MarketReportsPageState();
}

class _MarketReportsPageState extends ConsumerState<MarketReportsPage> {
  String _selected = _categories.first.key;

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.of(context).size.width > 700;

    return Scaffold(
      body: SafeArea(
        child: isWide ? _buildWideLayout() : _buildNarrowLayout(),
      ),
    );
  }

  Widget _buildWideLayout() {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 200,
          child: _buildCategoryList(),
        ),
        Container(width: 1, color: AppColors.border.withOpacity(0.4)),
        Expanded(
          child: _buildReportContent(),
        ),
      ],
    );
  }

  Widget _buildNarrowLayout() {
    return Column(
      children: [
        SizedBox(
          height: 50,
          child: _buildCategoryList(),
        ),
        const Divider(height: 1),
        Expanded(child: _buildReportContent()),
      ],
    );
  }

  Widget _buildCategoryList() {
    return ListView(
      padding: const EdgeInsets.symmetric(vertical: 8),
      children: _categories.map((cat) {
        final isSelected = _selected == cat.key;
        return Material(
          color: isSelected ? cat.color.withOpacity(0.15) : Colors.transparent,
          child: InkWell(
            onTap: () => setState(() => _selected = cat.key),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Icon(cat.icon, size: 18, color: isSelected ? cat.color : AppColors.textSecondary),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      cat.label,
                      style: TextStyle(
                        color: isSelected ? cat.color : AppColors.textSecondary,
                        fontSize: 13,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                      ),
                    ),
                  ),
                  if (isSelected)
                    Container(width: 3, height: 3,
                        decoration: BoxDecoration(color: cat.color, shape: BoxShape.circle)),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildReportContent() {
    final reportAsync = ref.watch(marketReportProvider(_selected));

    return reportAsync.when(
      data: (data) {
        if (data == null) {
          return _emptyState(_selected);
        }
        final reportDate = data['report_date'] ?? 'unknown';
        final content = data['content'] ?? '';

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Row(
                children: [
                  Text(
                    'Report: $reportDate',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 18),
                    onPressed: () => ref.invalidate(marketReportProvider(_selected)),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: Markdown(
                data: content,
                padding: const EdgeInsets.all(16),
                styleSheet: MarkdownStyleSheet(
                  h1: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 20, fontWeight: FontWeight.bold),
                  h2: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 17, fontWeight: FontWeight.w700),
                  h3: const TextStyle(
                      color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.w600),
                  p: const TextStyle(color: AppColors.textPrimary, fontSize: 14, height: 1.5),
                  code: TextStyle(
                      color: AppColors.gold, backgroundColor: AppColors.cardBg, fontSize: 12),
                  codeblockDecoration: BoxDecoration(
                    color: AppColors.cardBg,
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
              ),
            ),
          ],
        );
      },
      loading: () => const Center(
        child: SizedBox(width: 24, height: 24,
            child: CircularProgressIndicator(strokeWidth: 2)),
      ),
      error: (_, __) => _emptyState(_selected),
    );
  }

  Widget _emptyState(String category) {
    final cat = _categories.firstWhere((c) => c.key == category);
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(cat.icon, size: 48, color: AppColors.textSecondary.withOpacity(0.4)),
          const SizedBox(height: 12),
          Text(
            'Kein Report verfügbar',
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            'Die Trading Crew hat noch keinen ${cat.label}-Report generiert.',
            style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => ref.invalidate(marketReportProvider(category)),
            icon: const Icon(Icons.refresh, size: 16),
            label: const Text('Erneut versuchen'),
          ),
        ],
      ),
    );
  }
}

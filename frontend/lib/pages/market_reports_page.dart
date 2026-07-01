import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_html/flutter_html.dart';
import '../config/theme.dart';
import '../providers/market_report_provider.dart';

const _categories = [
  _Category('crashprophet', 'Crash Prophet', 'assets/report_icons/crashprophet_avatar.png', AppColors.negative),
  _Category('diamondhands', 'Diamond Hands', 'assets/report_icons/diamondhands_avatar.png', AppColors.blue),
  _Category('cryptoanalysis', 'Crypto Analysis', 'assets/report_icons/cryptonewsbot.png', AppColors.violet),
  _Category('equities', 'Equities', 'assets/report_icons/markets-lilly.png', AppColors.positive),
  _Category('forex', 'Forex', 'assets/report_icons/ForexHulk_avatar.png', AppColors.gold),
  _Category('commodities', 'Commodities', 'assets/report_icons/CommoLilly_avatar.png', Color(0xFFcd853f)),
  _Category('real-estate', 'Real Estate', 'assets/report_icons/CottageScout_avatar.png', Color(0xFF2e8b57)),
  _Category('trader-perspectives', 'Trader Perspectives', 'assets/report_icons/boersenguru_discord.png', AppColors.gold),
  _Category('crypto-arb-weekly', 'Crypto Arb Weekly', 'assets/report_icons/cryptonewsbot.png', AppColors.positive),
];

class _Category {
  final String key;
  final String label;
  final String imageAsset;
  final Color color;
  const _Category(this.key, this.label, this.imageAsset, this.color);
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
          width: 220,
          child: Column(
            children: [
              Expanded(child: _buildCategoryList()),
              Padding(
                padding: const EdgeInsets.all(10),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.asset(
                    'assets/report_icons/guterBote_discord_neon.png',
                    width: 200,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
            ],
          ),
        ),
        Container(width: 1, color: AppColors.borderColor(context).withOpacity(0.4)),
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
          height: 70,
          child: _buildCategoryList(scrollHorizontal: true),
        ),
        const Divider(height: 1),
        Expanded(child: _buildReportContent()),
      ],
    );
  }

  Widget _buildCategoryList({bool scrollHorizontal = false}) {
    return ListView.builder(
      scrollDirection: scrollHorizontal ? Axis.horizontal : Axis.vertical,
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: _categories.length,
      itemBuilder: (context, index) {
        final cat = _categories[index];
        final isSelected = _selected == cat.key;
        return Material(
          color: isSelected ? cat.color.withOpacity(0.15) : Colors.transparent,
          child: InkWell(
            onTap: () => setState(() => _selected = cat.key),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 16),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: Image.asset(
                      cat.imageAsset,
                      width: 22,
                      height: 22,
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    cat.label,
                    style: TextStyle(
                      color: isSelected ? cat.color : AppColors.secondaryColor(context),
                      fontSize: 13,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                    ),
                  ),
                  if (isSelected) ...[
                    const SizedBox(width: 6),
                    Container(width: 3, height: 3,
                        decoration: BoxDecoration(color: cat.color, shape: BoxShape.circle)),
                  ],
                ],
              ),
            ),
          ),
        );
      },
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
        final reportTime = data['report_time'];
        final content = data['content'] ?? '';
        final dateDisplay = reportTime != null
            ? '$reportDate at $reportTime'
            : reportDate;

        final prefix = content.substring(0, content.length.clamp(0, 200));
        final isHtml = RegExp(r'<(?:div|h[12]|p|!--)[\s>]').hasMatch(prefix);

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
child: Row(
                children: [
                  Text(
                    'Report: $dateDisplay',
                    style: TextStyle(
                      color: AppColors.secondaryColor(context),
                      fontSize: 12,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.refresh, size: 18),
                    onPressed: () => refreshMarketReport(ref, _selected),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: isHtml
                  ? SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Html(
                        data: _resolveAvatarPaths(content),
                        style: {
                          'body': Style(
                            margin: Margins.zero,
                            padding: HtmlPaddings.zero,
                            color: AppColors.textColor(context),
                            fontSize: FontSize(14),
                          ),
                          'h2': Style(
                            color: AppColors.textColor(context),
                            fontSize: FontSize(17),
                            fontWeight: FontWeight.w700,
                          ),
                          'h3': Style(
                            color: AppColors.textColor(context),
                            fontSize: FontSize(15),
                            fontWeight: FontWeight.w600,
                          ),
                          'p': Style(
                            color: AppColors.textColor(context),
                            fontSize: FontSize(14),
                            lineHeight: const LineHeight(1.5),
                          ),
                        },
                      ),
                    )
                  : Markdown(
                      data: content,
                      padding: const EdgeInsets.all(16),
                      styleSheet: MarkdownStyleSheet(
                        h1: TextStyle(
                            color: AppColors.textColor(context), fontSize: 20, fontWeight: FontWeight.bold),
                        h2: TextStyle(
                            color: AppColors.textColor(context), fontSize: 17, fontWeight: FontWeight.w700),
                        h3: TextStyle(
                            color: AppColors.textColor(context), fontSize: 14, fontWeight: FontWeight.w600),
                        p: TextStyle(color: AppColors.textColor(context), fontSize: 14, height: 1.5),
                        code: TextStyle(
                            color: AppColors.gold, backgroundColor: AppColors.cardColor(context), fontSize: 12),
                        codeblockDecoration: BoxDecoration(
                          color: AppColors.cardColor(context),
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
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.asset(
              cat.imageAsset,
              width: 64,
              height: 64,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Kein Report verfügbar',
            style: TextStyle(color: AppColors.secondaryColor(context), fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            'Die Trading Crew hat noch keinen ${cat.label}-Report generiert.',
            style: TextStyle(color: AppColors.secondaryColor(context), fontSize: 12),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => refreshMarketReport(ref, category),
            icon: const Icon(Icons.refresh, size: 16),
            label: const Text('Erneut versuchen'),
          ),
        ],
      ),
    );
  }
}

String _resolveAvatarPaths(String html) {
  return html.replaceAllMapped(
    RegExp(r'<img\s+src="avatars/([^"]+)"\s+style="([^"]*)"\s*/?>'),
    (m) {
      final name = m.group(1)!.replaceAll('.png', '');
      return '<span style="${m.group(2)}">&#x25CF;</span>';
    },
  );
}

import 'package:flutter/material.dart';

class AppColors {
  static const Color positive = Color(0xFF00b09b);
  static const Color negative = Color(0xFFe74c3c);
  static const Color gold = Color(0xFFf0a500);
  static const Color blue = Color(0xFF3498db);
  static const Color violet = Color(0xFF9b59b6);
  static const Color dark = Color(0xFF0d1117);
  static const Color surface = Color(0xFF161b22);
  static const Color cardBg = Color(0xFF21262d);
  static const Color textPrimary = Color(0xFFf0f6fc);
  static const Color textSecondary = Color(0xFF8b949e);
  static const Color border = Color(0xFF30363d);

  static const Color lightBg = Color(0xFFf6f8fa);
  static const Color lightSurface = Color(0xFFffffff);
  static const Color lightCardBg = Color(0xFFffffff);
  static const Color lightTextPrimary = Color(0xFF1a1a2e);
  static const Color lightTextSecondary = Color(0xFF57606a);
  static const Color lightBorder = Color(0xFFd0d7de);

  static Color textColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? textPrimary
        : lightTextPrimary;
  }

  static Color secondaryColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? textSecondary
        : lightTextSecondary;
  }

  static Color borderColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? border
        : lightBorder;
  }

  static Color surfaceColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? surface
        : lightSurface;
  }

  static Color cardColor(BuildContext context) {
    return Theme.of(context).brightness == Brightness.dark
        ? cardBg
        : lightCardBg;
  }
}

ThemeData buildDarkTheme() {
  return ThemeData(
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.dark,
    colorScheme: const ColorScheme.dark(
      primary: AppColors.positive,
      error: AppColors.negative,
      surface: AppColors.surface,
    ),
    cardTheme: CardThemeData(
      color: AppColors.cardBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.border),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.positive,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(
        color: AppColors.textPrimary, fontSize: 28, fontWeight: FontWeight.bold,
      ),
      headlineMedium: TextStyle(
        color: AppColors.textPrimary, fontSize: 22, fontWeight: FontWeight.bold,
      ),
      titleMedium: TextStyle(
        color: AppColors.textPrimary, fontSize: 16, fontWeight: FontWeight.w600,
      ),
      bodyLarge: TextStyle(color: AppColors.textPrimary, fontSize: 15),
      bodyMedium: TextStyle(color: AppColors.textSecondary, fontSize: 14),
      labelLarge: TextStyle(
        color: AppColors.textPrimary, fontSize: 14, fontWeight: FontWeight.w600,
      ),
    ),
  );
}

ThemeData buildLightTheme() {
  return ThemeData(
    brightness: Brightness.light,
    scaffoldBackgroundColor: AppColors.lightBg,
    colorScheme: const ColorScheme.light(
      primary: AppColors.positive,
      error: AppColors.negative,
      surface: AppColors.lightSurface,
    ),
    cardTheme: CardThemeData(
      color: AppColors.lightCardBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.lightBorder),
      ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.positive,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    textTheme: const TextTheme(
      headlineLarge: TextStyle(
        color: AppColors.lightTextPrimary, fontSize: 28, fontWeight: FontWeight.bold,
      ),
      headlineMedium: TextStyle(
        color: AppColors.lightTextPrimary, fontSize: 22, fontWeight: FontWeight.bold,
      ),
      titleMedium: TextStyle(
        color: AppColors.lightTextPrimary, fontSize: 16, fontWeight: FontWeight.w600,
      ),
      bodyLarge: TextStyle(color: AppColors.lightTextPrimary, fontSize: 15),
      bodyMedium: TextStyle(color: AppColors.lightTextSecondary, fontSize: 14),
      labelLarge: TextStyle(
        color: AppColors.lightTextPrimary, fontSize: 14, fontWeight: FontWeight.w600,
      ),
    ),
  );
}

ThemeData buildTheme() => buildDarkTheme();

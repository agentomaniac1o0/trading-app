import 'dart:convert';
import 'dart:typed_data';

class TraderProfile {
  final String key;
  final String name;
  final String emoji;
  final String title;
  final String bio;
  final String color;
  final String avatarUrl;
  final Uint8List? avatarBytes;

  const TraderProfile({
    required this.key,
    required this.name,
    required this.emoji,
    required this.title,
    required this.bio,
    required this.color,
    required this.avatarUrl,
    this.avatarBytes,
  });

  factory TraderProfile.fromJson(Map<String, dynamic> json) {
    Uint8List? bytes;
    final b64 = json['avatar_base64'] as String?;
    if (b64 != null && b64.isNotEmpty) {
      bytes = base64Decode(b64);
    }
    return TraderProfile(
      key: json['key'] as String,
      name: json['name'] as String,
      emoji: json['emoji'] as String,
      title: json['title'] as String,
      bio: json['bio'] as String,
      color: json['color'] as String,
      avatarUrl: json['avatar_url'] as String,
      avatarBytes: bytes,
    );
  }
}

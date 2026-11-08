import 'package:flutter/material.dart';

/// Um dos temas predefinidos do aplicativo.
class PodcastTheme {
  const PodcastTheme({
    required this.id,
    required this.name,
    required this.description,
    required this.query,
    required this.icon,
    required this.color,
  });

  final String id;
  final String name;
  final String description;

  /// Termo de busca enviado ao feed de notícias.
  final String query;
  final IconData icon;
  final Color color;
}

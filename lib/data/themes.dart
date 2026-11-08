import 'package:flutter/material.dart';

import '../models/podcast_theme.dart';

/// Janela máxima de idade das notícias aceitas no podcast.
const Duration kMaxArticleAge = Duration(hours: 72);

/// Duração alvo de cada episódio.
const Duration kTargetEpisodeDuration = Duration(minutes: 2);

/// Os 6 temas predefinidos do PodAI.
///
/// As cores são variações da paleta roxo/amarelo da marca, usadas apenas como
/// tingimento dos painéis de vidro de cada tema.
const List<PodcastTheme> kPodcastThemes = [
  PodcastTheme(
    id: 'tecnologia',
    name: 'Tecnologia',
    description: 'Inovação, inteligência artificial, gadgets e startups',
    query: 'tecnologia OR "inteligência artificial" OR startups',
    icon: Icons.memory_rounded,
    color: Color(0xFF8B5CF6), // violeta
  ),
  PodcastTheme(
    id: 'economia',
    name: 'Economia',
    description: 'Mercado financeiro, inflação, juros e negócios',
    query: 'economia OR "mercado financeiro" OR inflação OR juros',
    icon: Icons.trending_up_rounded,
    color: Color(0xFFFACC15), // amarelo
  ),
  PodcastTheme(
    id: 'esportes',
    name: 'Esportes',
    description: 'Futebol, olimpíadas e competições',
    query: 'esportes OR futebol OR campeonato',
    icon: Icons.sports_soccer_rounded,
    color: Color(0xFFA855F7), // púrpura
  ),
  PodcastTheme(
    id: 'ciencia',
    name: 'Ciência',
    description: 'Pesquisas, espaço e descobertas',
    query: 'ciência OR "pesquisa científica" OR espaço OR NASA',
    icon: Icons.science_rounded,
    color: Color(0xFFF59E0B), // âmbar
  ),
  PodcastTheme(
    id: 'saude',
    name: 'Saúde',
    description: 'Medicina, bem-estar e saúde pública',
    query: 'saúde OR medicina OR "saúde pública" OR vacina',
    icon: Icons.favorite_rounded,
    color: Color(0xFFD946EF), // fúcsia
  ),
  PodcastTheme(
    id: 'politica',
    name: 'Política',
    description: 'Governo, congresso e eleições',
    query: 'política OR governo OR congresso OR eleições',
    icon: Icons.account_balance_rounded,
    color: Color(0xFFFDE047), // amarelo-limão
  ),
];

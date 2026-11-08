// Identidade visual (README §8): roxo e amarelo sobre fundo escuro.
export const colors = {
  primaria: '#6D28D9',
  primariaEscura: '#2E1065',
  destaque: '#FACC15',
  fundo: '#0F0A1E',
  superficie: 'rgba(255,255,255,0.08)',
  superficieForte: 'rgba(255,255,255,0.14)',
  borda: 'rgba(255,255,255,0.16)',
  texto: '#F5F3FF',
  textoSecundario: '#C4B5FD',
  erro: '#FCA5A5',
} as const;

export const gradient = [colors.primariaEscura, colors.fundo, colors.fundo] as const;

export const radius = { sm: 10, md: 16, lg: 24 } as const;
export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 } as const;

// Tipos espelhando backend/app/schemas.py (README §5.2).

export type Voice = 'dora' | 'alex';

export interface Theme {
  id: string;
  nome: string;
  icone: string;
  cor: string;
  ultimo_episodio_em: string | null;
}

export interface Source {
  veiculo: string | null;
  titulo_original: string;
  url: string;
  publicada_em: string | null;
}

export interface Line {
  voz: Voice;
  texto: string;
  inicio_s: number;
}

export interface Episode {
  id: number;
  tema: string;
  titulo: string;
  gerado_em: string;
  duracao_s: number | null;
  audio_url: string | null;
  gerador: string;
  fonte: Source;
  falas: Line[];
  aviso: string;
}

export interface Generating {
  status: 'gerando';
  tema: string;
  tentar_novamente_em_s: number;
}

export interface ApiErrorBody {
  erro: string;
  mensagem: string;
}

export interface Health {
  status: 'ok';
  motor_voz: string;
  motor_voz_carregado: boolean;
  llm_configurado: boolean;
  gerando: string[];
  ultimo_ciclo: { inicio: string; fim: string; resultados: Record<string, string> } | null;
}

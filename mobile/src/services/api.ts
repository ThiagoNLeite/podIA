import type { ApiErrorBody, Episode, Generating, Health, Theme } from '@/types/api';

const TIMEOUT_MS = 10_000;

export type ApiErrorKind = 'offline' | 'not_found' | 'generation_failed' | 'server';

export class ApiError extends Error {
  constructor(
    public kind: ApiErrorKind,
    message: string,
    public status?: number,
  ) {
    super(message);
  }
}

async function request(baseUrl: string, path: string): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(`${baseUrl}${path}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });
  } catch {
    throw new ApiError('offline', 'Não foi possível falar com o servidor do podIA.');
  } finally {
    clearTimeout(timer);
  }
}

async function errorFrom(res: Response): Promise<ApiError> {
  let body: Partial<ApiErrorBody> = {};
  try {
    body = (await res.json()) as ApiErrorBody;
  } catch {
    // corpo não-JSON
  }
  const message = body.mensagem ?? `Erro ${res.status} no servidor.`;
  if (res.status === 404) return new ApiError('not_found', message, 404);
  if (res.status === 503) return new ApiError('generation_failed', message, 503);
  return new ApiError('server', message, res.status);
}

async function getJson<T>(baseUrl: string, path: string): Promise<T> {
  const res = await request(baseUrl, path);
  if (!res.ok) throw await errorFrom(res);
  return (await res.json()) as T;
}

export const api = {
  themes: (baseUrl: string) => getJson<Theme[]>(baseUrl, '/themes'),
  health: (baseUrl: string) => getJson<Health>(baseUrl, '/health'),

  /** 200 → episódio pronto · 202 → ainda gerando (o app consulta de novo). */
  latestEpisode: async (baseUrl: string, theme: string): Promise<Episode | Generating> => {
    const res = await request(baseUrl, `/episodes/latest?theme=${encodeURIComponent(theme)}`);
    if (res.status === 202) return (await res.json()) as Generating;
    if (!res.ok) throw await errorFrom(res);
    return (await res.json()) as Episode;
  },

  audioUrl: (baseUrl: string, path: string) => `${baseUrl}${path}`,
};

export function isGenerating(data: Episode | Generating | undefined): data is Generating {
  return !!data && 'status' in data && data.status === 'gerando';
}

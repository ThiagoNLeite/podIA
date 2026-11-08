import { useQuery } from '@tanstack/react-query';
import { useRef } from 'react';

import { api, ApiError, isGenerating } from '@/services/api';
import { useSettings } from '@/services/settings';

const MAX_WAIT_MS = 3 * 60 * 1000; // README §5.3: desiste depois de 3 minutos

export function useThemes() {
  const { apiUrl, loaded } = useSettings();
  return useQuery({
    queryKey: ['themes', apiUrl],
    queryFn: () => api.themes(apiUrl),
    enabled: loaded,
  });
}

/** Último episódio do tema; enquanto a API responder 202, consulta de novo a cada 5 s (máx. 3 min). */
export function useLatestEpisode(theme: string) {
  const { apiUrl, loaded } = useSettings();
  const startedAt = useRef<number | null>(null);

  return useQuery({
    queryKey: ['episode', apiUrl, theme],
    queryFn: async () => {
      startedAt.current ??= Date.now();
      const data = await api.latestEpisode(apiUrl, theme);
      if (isGenerating(data)) {
        if (Date.now() - startedAt.current > MAX_WAIT_MS) {
          startedAt.current = null;
          throw new ApiError('generation_failed', 'O episódio está demorando mais que o normal para ficar pronto.');
        }
      } else {
        startedAt.current = null;
      }
      return data;
    },
    enabled: loaded && !!theme,
    retry: (count, error) => error instanceof ApiError && error.kind === 'offline' && count < 1,
    refetchInterval: (query) =>
      isGenerating(query.state.data) ? query.state.data.tentar_novamente_em_s * 1000 : false,
  });
}

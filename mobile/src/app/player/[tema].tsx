import Ionicons from '@expo/vector-icons/Ionicons';
import { useQueryClient } from '@tanstack/react-query';
import {
  requestNotificationPermissionsAsync,
  useAudioPlayer,
  useAudioPlayerStatus,
  type AudioPlayer,
} from 'expo-audio';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { PlayerControls } from '@/components/player-controls';
import { SourceCard } from '@/components/source-card';
import { Transcript } from '@/components/transcript';
import { GlassCard, Screen, StateView } from '@/components/ui';
import { useLatestEpisode, useThemes } from '@/hooks/use-api';
import { api, ApiError, isGenerating } from '@/services/api';
import { currentLineIndex } from '@/services/format';
import { useSettings, type Speed } from '@/services/settings';
import { colors, spacing } from '@/theme/colors';
import type { Episode, Theme } from '@/types/api';

export default function PlayerScreen() {
  const { tema } = useLocalSearchParams<{ tema: string }>();
  const { data: themes } = useThemes();
  const theme = themes?.find((t) => t.id === tema);
  const query = useLatestEpisode(tema);
  const queryClient = useQueryClient();

  const header = (
    <View style={styles.header}>
      <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="Voltar" hitSlop={12}>
        <Ionicons name="chevron-back" size={28} color={colors.texto} />
      </Pressable>
      <Text style={styles.headerTitle} numberOfLines={1}>
        {theme ? `${theme.icone}  podIA ${theme.nome}` : 'podIA'}
      </Text>
      <View style={{ width: 28 }} />
    </View>
  );

  let body;
  if (query.isPending) {
    body = <StateView kind="loading" />;
  } else if (query.error) {
    const err = query.error;
    const offline = err instanceof ApiError && err.kind === 'offline';
    body = (
      <StateView
        kind="error"
        title={offline ? 'Servidor indisponível' : 'Não foi possível gerar o episódio'}
        message={err.message}
        onRetry={() => queryClient.resetQueries({ queryKey: ['episode'] })}
      />
    );
  } else if (isGenerating(query.data)) {
    body = (
      <StateView
        kind="generating"
        title="Preparando seu podIA…"
        message="Buscando a notícia mais recente e gravando a conversa da Dora e do Alex. Leva cerca de 1 minuto."
      />
    );
  } else {
    body = <EpisodeView episode={query.data} theme={theme} />;
  }

  return (
    <Screen>
      {header}
      {body}
    </Screen>
  );
}

function EpisodeView({ episode, theme }: { episode: Episode; theme?: Theme }) {
  const { apiUrl, speed: defaultSpeed } = useSettings();
  const source = useMemo(
    () => (episode.audio_url ? { uri: api.audioUrl(apiUrl, episode.audio_url) } : null),
    [apiUrl, episode.audio_url],
  );
  const player = useAudioPlayer(source, { updateInterval: 250 });
  const status = useAudioPlayerStatus(player);
  const [speed, setSpeed] = useState<Speed>(defaultSpeed);
  const autoplayed = useRef(false);

  // Começa a tocar assim que carregar e ativa os controles da tela de bloqueio
  // (no Android, sem eles o áudio em segundo plano para depois de ~3 min).
  useEffect(() => {
    if (!status.isLoaded || autoplayed.current) return;
    autoplayed.current = true;
    activateLockScreen(player, episode, theme);
    player.setPlaybackRate(speed);
    player.play();
  }, [status.isLoaded, player, episode, theme, speed]);

  const starts = useMemo(() => episode.falas.map((f) => f.inicio_s), [episode.falas]);
  const current = currentLineIndex(starts, status.currentTime);
  const duration = status.duration || episode.duracao_s || 0;
  const finished = status.didJustFinish || (duration > 0 && status.currentTime >= duration - 0.3);

  const seek = (seconds: number) => {
    player.seekTo(Math.max(0, Math.min(seconds, duration)));
    if (!status.playing) player.play();
  };

  const togglePlay = () => {
    if (status.playing) return player.pause();
    if (finished) player.seekTo(0);
    player.play();
  };

  const changeSpeed = (s: Speed) => {
    setSpeed(s);
    player.setPlaybackRate(s);
  };

  return (
    <ScrollView contentContainerStyle={styles.scroll}>
      <Text style={[styles.themeName, { color: theme?.cor ?? colors.destaque }]}>
        {theme?.nome.toUpperCase() ?? episode.tema.toUpperCase()}
      </Text>
      <Text style={styles.title} accessibilityRole="header">
        {episode.titulo}
      </Text>

      <GlassCard style={{ marginTop: spacing.md }}>
        {source ? (
          <PlayerControls
            playing={status.playing}
            buffering={status.isBuffering || !status.isLoaded}
            currentTime={status.currentTime}
            duration={duration}
            speed={speed}
            accent={theme?.cor ?? colors.destaque}
            onTogglePlay={togglePlay}
            onBack10={() => seek(status.currentTime - 10)}
            onSeek={seek}
            onSpeed={changeSpeed}
          />
        ) : (
          <Text style={styles.expired}>
            O áudio deste episódio expirou. A transcrição continua disponível abaixo.
          </Text>
        )}
      </GlassCard>

      <Text style={styles.section}>Transcrição</Text>
      <Transcript lines={episode.falas} current={current} onSeek={seek} />

      <View style={{ marginTop: spacing.lg }}>
        <SourceCard episode={episode} />
      </View>
    </ScrollView>
  );
}

async function activateLockScreen(player: AudioPlayer, episode: Episode, theme?: Theme) {
  try {
    if (Platform.OS === 'android') await requestNotificationPermissionsAsync();
    player.setActiveForLockScreen(
      true,
      { title: episode.titulo, artist: `podIA ${theme?.nome ?? ''}`.trim(), albumTitle: 'podIA' },
      { showSeekBackward: true, showSeekForward: true },
    );
  } catch {
    // Sem permissão de notificação: o áudio toca, só não aparece o controle na tela de bloqueio.
  }
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  headerTitle: { color: colors.texto, fontSize: 16, fontWeight: '700', flex: 1, textAlign: 'center' },
  scroll: { padding: spacing.md, paddingBottom: spacing.xl * 2 },
  themeName: { fontSize: 13, fontWeight: '800', letterSpacing: 2 },
  title: { color: colors.texto, fontSize: 24, fontWeight: '800', lineHeight: 30, marginTop: spacing.xs },
  section: {
    color: colors.texto,
    fontSize: 18,
    fontWeight: '700',
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  expired: { color: colors.textoSecundario, fontSize: 14, textAlign: 'center' },
});

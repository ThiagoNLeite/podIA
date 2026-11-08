import Ionicons from '@expo/vector-icons/Ionicons';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatClock } from '@/services/format';
import { SPEEDS, type Speed } from '@/services/settings';
import { colors, spacing } from '@/theme/colors';

interface Props {
  playing: boolean;
  buffering: boolean;
  currentTime: number;
  duration: number;
  speed: Speed;
  accent: string;
  onTogglePlay: () => void;
  onBack10: () => void;
  onSeek: (seconds: number) => void;
  onSpeed: (speed: Speed) => void;
}

export function PlayerControls(p: Props) {
  const [barWidth, setBarWidth] = useState(1);
  const progress = p.duration > 0 ? Math.min(1, p.currentTime / p.duration) : 0;

  return (
    <View style={styles.wrap}>
      <Pressable
        accessibilityRole="adjustable"
        accessibilityLabel={`Posição ${formatClock(p.currentTime)} de ${formatClock(p.duration)}. Toque na barra para avançar ou voltar.`}
        onLayout={(e) => setBarWidth(e.nativeEvent.layout.width || 1)}
        onPress={(e) => p.onSeek((e.nativeEvent.locationX / barWidth) * p.duration)}
        hitSlop={{ top: 14, bottom: 14 }}
        style={styles.barTouch}
      >
        <View style={styles.barTrack}>
          <View style={[styles.barFill, { width: `${progress * 100}%` }]} />
        </View>
        <View style={[styles.knob, { left: progress * barWidth - 7 }]} />
      </Pressable>
      <View style={styles.times}>
        <Text style={styles.time}>{formatClock(p.currentTime)}</Text>
        <Text style={styles.time}>{formatClock(p.duration)}</Text>
      </View>

      <View style={styles.row}>
        <Pressable
          onPress={p.onBack10}
          accessibilityRole="button"
          accessibilityLabel="Voltar 10 segundos"
          hitSlop={10}
          style={styles.side}
        >
          <Ionicons name="play-back" size={26} color={colors.texto} />
          <Text style={styles.sideLabel}>10s</Text>
        </Pressable>

        <Pressable
          onPress={p.onTogglePlay}
          accessibilityRole="button"
          accessibilityLabel={p.playing ? 'Pausar' : 'Tocar'}
          style={({ pressed }) => [styles.play, { backgroundColor: colors.primaria }, pressed && { opacity: 0.8 }]}
        >
          <Ionicons
            name={p.buffering && !p.playing ? 'hourglass-outline' : p.playing ? 'pause' : 'play'}
            size={38}
            color={colors.texto}
            style={!p.playing && !p.buffering ? { marginLeft: 4 } : undefined}
          />
        </Pressable>

        <View style={styles.speeds}>
          {SPEEDS.map((s) => (
            <Pressable
              key={s}
              onPress={() => p.onSpeed(s)}
              accessibilityRole="button"
              accessibilityState={{ selected: p.speed === s }}
              accessibilityLabel={`Velocidade ${s}x`}
              style={[styles.speed, p.speed === s && { backgroundColor: colors.destaque }]}
            >
              <Text style={[styles.speedText, p.speed === s && { color: colors.fundo }]}>{s}x</Text>
            </Pressable>
          ))}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  barTouch: { height: 24, justifyContent: 'center' },
  barTrack: { height: 6, borderRadius: 3, backgroundColor: colors.superficieForte, overflow: 'hidden' },
  barFill: { height: 6, backgroundColor: colors.destaque },
  knob: {
    position: 'absolute',
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.destaque,
  },
  times: { flexDirection: 'row', justifyContent: 'space-between' },
  time: { color: colors.textoSecundario, fontSize: 13, fontVariant: ['tabular-nums'] },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: spacing.sm },
  side: { alignItems: 'center', width: 72 },
  sideLabel: { color: colors.textoSecundario, fontSize: 12 },
  play: {
    width: 76,
    height: 76,
    borderRadius: 38,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 6,
  },
  speeds: { flexDirection: 'column', gap: 4, width: 72, alignItems: 'center' },
  speed: {
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 3,
    backgroundColor: colors.superficie,
    minWidth: 54,
    alignItems: 'center',
  },
  speedText: { color: colors.texto, fontSize: 13, fontWeight: '700' },
});

import { Pressable, StyleSheet, Text, View } from 'react-native';

import { colors, radius, spacing } from '@/theme/colors';
import type { Line } from '@/types/api';

const NAMES = { dora: 'Dora', alex: 'Alex' } as const;

/** Transcrição do diálogo; a fala atual fica destacada. Tocar numa fala pula para ela. */
export function Transcript({
  lines,
  current,
  onSeek,
}: {
  lines: Line[];
  current: number;
  onSeek: (seconds: number) => void;
}) {
  return (
    <View style={styles.wrap}>
      {lines.map((line, i) => {
        const active = i === current;
        return (
          <Pressable
            key={i}
            onPress={() => onSeek(line.inicio_s)}
            accessibilityRole="button"
            accessibilityLabel={`${NAMES[line.voz]}: ${line.texto}`}
            accessibilityHint="Toque para ouvir a partir desta fala"
            accessibilityState={{ selected: active }}
            style={[styles.line, active && styles.lineActive]}
          >
            <Text style={[styles.speaker, line.voz === 'alex' && styles.alex, active && styles.speakerActive]}>
              {NAMES[line.voz]}
            </Text>
            <Text style={[styles.text, active && styles.textActive]}>{line.texto}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.xs },
  line: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
    borderLeftWidth: 3,
    borderLeftColor: 'transparent',
  },
  lineActive: { backgroundColor: 'rgba(250,204,21,0.12)', borderLeftColor: colors.destaque },
  speaker: { color: colors.textoSecundario, fontWeight: '800', fontSize: 12, letterSpacing: 1, marginBottom: 2 },
  alex: { color: '#A5B4FC' },
  speakerActive: { color: colors.destaque },
  text: { color: 'rgba(245,243,255,0.75)', fontSize: 16, lineHeight: 23 },
  textActive: { color: colors.texto },
});

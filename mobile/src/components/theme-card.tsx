import { Pressable, StyleSheet, Text, View } from 'react-native';

import { formatUpdated } from '@/services/format';
import { colors, radius, spacing } from '@/theme/colors';
import type { Theme } from '@/types/api';

export function ThemeCard({ theme, onPress }: { theme: Theme; onPress: () => void }) {
  const updated = formatUpdated(theme.ultimo_episodio_em);
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`${theme.nome}, ${updated}. Tocar para ouvir.`}
      style={({ pressed }) => [styles.card, pressed && { transform: [{ scale: 0.97 }], opacity: 0.85 }]}
    >
      <View style={[styles.iconBubble, { backgroundColor: `${theme.cor}33`, borderColor: `${theme.cor}88` }]}>
        <Text style={styles.icon}>{theme.icone}</Text>
      </View>
      <Text style={styles.name}>{theme.nome}</Text>
      <Text style={styles.updated} numberOfLines={2}>
        {updated}
      </Text>
      <View style={[styles.accent, { backgroundColor: theme.cor }]} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 150,
    backgroundColor: colors.superficie,
    borderColor: colors.borda,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.md,
    overflow: 'hidden',
    gap: spacing.xs,
  },
  iconBubble: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  icon: { fontSize: 26 },
  name: { color: colors.texto, fontSize: 18, fontWeight: '700' },
  updated: { color: colors.textoSecundario, fontSize: 13 },
  accent: { position: 'absolute', left: 0, right: 0, bottom: 0, height: 4 },
});

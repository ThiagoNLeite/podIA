import Ionicons from '@expo/vector-icons/Ionicons';
import * as WebBrowser from 'expo-web-browser';
import { StyleSheet, Text, View } from 'react-native';

import { Button, GlassCard } from '@/components/ui';
import { formatAgo } from '@/services/format';
import { colors, spacing } from '@/theme/colors';
import type { Episode } from '@/types/api';

export function SourceCard({ episode }: { episode: Episode }) {
  const { fonte } = episode;
  const local = episode.gerador === 'local';
  return (
    <GlassCard style={styles.card}>
      <Text style={styles.label}>FONTE</Text>
      <Text style={styles.vehicle}>{fonte.veiculo ?? 'Fonte original'}</Text>
      <Text style={styles.original} numberOfLines={3}>
        {fonte.titulo_original}
      </Text>
      {fonte.publicada_em && <Text style={styles.ago}>{formatAgo(fonte.publicada_em)}</Text>}
      {!!fonte.url && (
        <View style={{ marginTop: spacing.sm }}>
          <Button
            label="Ler matéria completa"
            icon="open-outline"
            variant="ghost"
            onPress={() => WebBrowser.openBrowserAsync(fonte.url)}
          />
        </View>
      )}
      <View style={styles.badge}>
        <Ionicons name={local ? 'document-text-outline' : 'sparkles'} size={14} color={colors.destaque} />
        <Text style={styles.badgeText}>{local ? 'Resumo automático (sem IA)' : 'Gerado por IA'}</Text>
      </View>
      <Text style={styles.notice}>{episode.aviso}</Text>
    </GlassCard>
  );
}

const styles = StyleSheet.create({
  card: { gap: 4 },
  label: { color: colors.textoSecundario, fontSize: 11, fontWeight: '800', letterSpacing: 1.5 },
  vehicle: { color: colors.texto, fontSize: 18, fontWeight: '700' },
  original: { color: colors.texto, fontSize: 14, opacity: 0.85, lineHeight: 20 },
  ago: { color: colors.textoSecundario, fontSize: 13 },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    marginTop: spacing.md,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: 'rgba(250,204,21,0.12)',
  },
  badgeText: { color: colors.destaque, fontSize: 12, fontWeight: '700' },
  notice: { color: colors.textoSecundario, fontSize: 12, marginTop: spacing.xs },
});

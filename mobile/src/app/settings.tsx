import Ionicons from '@expo/vector-icons/Ionicons';
import { useQueryClient } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { Button, GlassCard, Screen } from '@/components/ui';
import { api } from '@/services/api';
import { DEFAULT_API_URL, normalizeUrl, SPEEDS, useSettings } from '@/services/settings';
import { colors, radius, spacing } from '@/theme/colors';

type TestResult = { ok: boolean; message: string } | null;

export default function SettingsScreen() {
  const settings = useSettings();
  const queryClient = useQueryClient();
  const [url, setUrl] = useState(settings.apiUrl);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult>(null);

  const save = () => {
    settings.update({ apiUrl: url });
    setUrl(normalizeUrl(url));
    queryClient.invalidateQueries();
  };

  const test = async () => {
    setTesting(true);
    setResult(null);
    try {
      const h = await api.health(normalizeUrl(url));
      setResult({
        ok: true,
        message: `Conectado! Voz: ${h.motor_voz}${h.motor_voz_carregado ? '' : ' (carregando)'} · IA: ${
          h.llm_configurado ? 'configurada' : 'sem chave (resumo automático)'
        }`,
      });
    } catch (e) {
      setResult({ ok: false, message: e instanceof Error ? e.message : 'Falha na conexão.' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <Screen>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="Voltar" hitSlop={12}>
          <Ionicons name="chevron-back" size={28} color={colors.texto} />
        </Pressable>
        <Text style={styles.headerTitle}>Configurações</Text>
        <View style={{ width: 28 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <GlassCard style={styles.card}>
          <Text style={styles.label}>Servidor do podIA</Text>
          <TextInput
            value={url}
            onChangeText={setUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            placeholder={DEFAULT_API_URL}
            placeholderTextColor="rgba(196,181,253,0.5)"
            style={styles.input}
            accessibilityLabel="Endereço do servidor"
            onSubmitEditing={save}
          />
          <Text style={styles.hint}>
            Emulador: http://10.0.2.2:8000 · Celular via USB: http://localhost:8000 · Wi-Fi: http://IP-do-PC:8000
          </Text>
          <View style={styles.row}>
            <Button label={testing ? 'Testando…' : 'Testar conexão'} icon="pulse" variant="ghost" onPress={test} disabled={testing} />
            <Button label="Salvar" icon="checkmark" onPress={save} />
          </View>
          {result && (
            <Text style={[styles.result, { color: result.ok ? '#86EFAC' : colors.erro }]}>{result.message}</Text>
          )}
        </GlassCard>

        <GlassCard style={styles.card}>
          <Text style={styles.label}>Velocidade padrão</Text>
          <View style={styles.row}>
            {SPEEDS.map((s) => (
              <Pressable
                key={s}
                onPress={() => settings.update({ speed: s })}
                accessibilityRole="button"
                accessibilityState={{ selected: settings.speed === s }}
                accessibilityLabel={`Velocidade padrão ${s}x`}
                style={[styles.chip, settings.speed === s && { backgroundColor: colors.destaque }]}
              >
                <Text style={[styles.chipText, settings.speed === s && { color: colors.fundo }]}>{s}x</Text>
              </Pressable>
            ))}
          </View>
        </GlassCard>

        <GlassCard style={styles.card}>
          <Text style={styles.label}>Sobre</Text>
          <Text style={styles.about}>podIA versão {Constants.expoConfig?.version ?? '1.0.0'}</Text>
          <Text style={styles.about}>
            Os episódios são gerados por IA a partir das fontes indicadas e podem conter imprecisões. Consulte sempre
            a matéria original.
          </Text>
          <Text style={styles.about}>
            Vozes: Kokoro-82M (Apache 2.0). Roteiros: Google Gemini. Notícias: Google Notícias e portais citados em
            cada episódio.
          </Text>
          <Text style={styles.about}>Projeto acadêmico — Thiago Nascimento Leite.</Text>
        </GlassCard>
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  headerTitle: { color: colors.texto, fontSize: 18, fontWeight: '700' },
  scroll: { padding: spacing.md, gap: spacing.md, paddingBottom: spacing.xl },
  card: { gap: spacing.sm },
  label: { color: colors.texto, fontSize: 16, fontWeight: '700' },
  input: {
    color: colors.texto,
    backgroundColor: 'rgba(0,0,0,0.25)',
    borderColor: colors.borda,
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    fontSize: 15,
  },
  hint: { color: colors.textoSecundario, fontSize: 12, lineHeight: 18 },
  row: { flexDirection: 'row', gap: spacing.sm, flexWrap: 'wrap' },
  result: { fontSize: 14, lineHeight: 20 },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 999,
    backgroundColor: colors.superficie,
    minWidth: 64,
    alignItems: 'center',
  },
  chipText: { color: colors.texto, fontWeight: '700' },
  about: { color: colors.textoSecundario, fontSize: 14, lineHeight: 20 },
});

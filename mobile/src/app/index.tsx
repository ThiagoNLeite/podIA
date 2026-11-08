import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { ThemeCard } from '@/components/theme-card';
import { Logo, Screen, StateView } from '@/components/ui';
import { useThemes } from '@/hooks/use-api';
import { colors, spacing } from '@/theme/colors';

export default function Home() {
  const { data, error, isPending, refetch, isRefetching } = useThemes();

  const header = (
    <View style={styles.header}>
      <Logo />
      <Pressable
        onPress={() => router.push('/settings')}
        accessibilityRole="button"
        accessibilityLabel="Configurações"
        hitSlop={12}
        style={styles.gear}
      >
        <Ionicons name="settings-outline" size={24} color={colors.texto} />
      </Pressable>
    </View>
  );

  if (isPending) {
    return (
      <Screen>
        {header}
        <StateView kind="loading" />
      </Screen>
    );
  }

  if (error || !data) {
    return (
      <Screen>
        {header}
        <StateView
          kind="error"
          title="Servidor indisponível"
          message={`${error?.message ?? 'Erro desconhecido.'}\nConfira a conexão ou o endereço do servidor nas Configurações.`}
          onRetry={() => refetch()}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <FlatList
        data={data}
        keyExtractor={(t) => t.id}
        numColumns={2}
        columnWrapperStyle={{ gap: spacing.md }}
        contentContainerStyle={styles.list}
        ListHeaderComponent={
          <View style={{ marginHorizontal: -spacing.md }}>
            {header}
            <Text style={styles.tagline}>Seu podcast de notícias, feito por IA, em 2 minutos.</Text>
          </View>
        }
        renderItem={({ item }) => (
          <ThemeCard
            theme={item}
            onPress={() => router.push({ pathname: '/player/[tema]', params: { tema: item.id } })}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={() => void refetch()}
            tintColor={colors.destaque}
            colors={[colors.primaria]}
          />
        }
      />
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  gear: { padding: spacing.sm },
  tagline: {
    color: colors.textoSecundario,
    fontSize: 15,
    paddingHorizontal: spacing.md,
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  list: { paddingHorizontal: spacing.md, paddingBottom: spacing.xl, gap: spacing.md },
});

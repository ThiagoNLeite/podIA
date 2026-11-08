import Ionicons from '@expo/vector-icons/Ionicons';
import { LinearGradient } from 'expo-linear-gradient';
import { useEffect, useState, type ReactNode } from 'react';
import {
  ActivityIndicator,
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, gradient, radius, spacing } from '@/theme/colors';

/** Fundo em gradiente roxo → escuro, comum a todas as telas. */
export function Screen({ children }: { children: ReactNode }) {
  return (
    <LinearGradient colors={gradient} locations={[0, 0.45, 1]} style={styles.flex}>
      <SafeAreaView style={styles.flex} edges={['top', 'left', 'right']}>
        {children}
      </SafeAreaView>
    </LinearGradient>
  );
}

/** Card "glass": fundo translúcido + borda clara (README §8). */
export function GlassCard({
  children,
  style,
}: {
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
}) {
  return <View style={[styles.glass, style]}>{children}</View>;
}

/** Wordmark "podIA" com o "IA" em amarelo e o fone de ouvido. */
export function Logo({ size = 30 }: { size?: number }) {
  return (
    <View style={styles.logo} accessibilityRole="header" accessibilityLabel="podIA">
      <Ionicons name="headset" size={size} color={colors.destaque} />
      <Text style={[styles.logoText, { fontSize: size }]}>
        pod<Text style={{ color: colors.destaque }}>IA</Text>
      </Text>
    </View>
  );
}

export function Button({
  label,
  onPress,
  icon,
  variant = 'primary',
  disabled,
}: {
  label: string;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
  variant?: 'primary' | 'ghost';
  disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => [
        styles.button,
        variant === 'primary' ? styles.buttonPrimary : styles.buttonGhost,
        (pressed || disabled) && { opacity: 0.6 },
      ]}
    >
      {icon && <Ionicons name={icon} size={18} color={colors.texto} />}
      <Text style={styles.buttonText}>{label}</Text>
    </Pressable>
  );
}

/** Ondas pulsando: "Preparando seu podIA…" */
function PulsingWaves() {
  const [anims] = useState(() => [0, 1, 2, 3, 4].map(() => new Animated.Value(0.3)));
  useEffect(() => {
    const loops = anims.map((a, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(i * 120),
          Animated.timing(a, { toValue: 1, duration: 420, useNativeDriver: true }),
          Animated.timing(a, { toValue: 0.3, duration: 420, useNativeDriver: true }),
        ]),
      ),
    );
    loops.forEach((l) => l.start());
    return () => loops.forEach((l) => l.stop());
  }, [anims]);
  return (
    <View style={styles.waves}>
      {anims.map((a, i) => (
        <Animated.View key={i} style={[styles.wave, { transform: [{ scaleY: a }] }]} />
      ))}
    </View>
  );
}

export function StateView({
  kind,
  title,
  message,
  onRetry,
}: {
  kind: 'loading' | 'generating' | 'error';
  title?: string;
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <View style={styles.state} accessibilityLiveRegion="polite">
      {kind === 'loading' && <ActivityIndicator size="large" color={colors.destaque} />}
      {kind === 'generating' && <PulsingWaves />}
      {kind === 'error' && <Ionicons name="cloud-offline-outline" size={48} color={colors.textoSecundario} />}
      {title && <Text style={styles.stateTitle}>{title}</Text>}
      {message && <Text style={styles.stateMessage}>{message}</Text>}
      {onRetry && (
        <View style={{ marginTop: spacing.md }}>
          <Button label="Tentar de novo" icon="refresh" onPress={onRetry} />
        </View>
      )}
    </View>
  );
}

export const styles = StyleSheet.create({
  flex: { flex: 1 },
  glass: {
    backgroundColor: colors.superficie,
    borderColor: colors.borda,
    borderWidth: StyleSheet.hairlineWidth * 2,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  logo: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  logoText: { color: colors.texto, fontWeight: '800', letterSpacing: -0.5 },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: 12,
    paddingHorizontal: spacing.lg,
    borderRadius: 999,
    minHeight: 48,
  },
  buttonPrimary: { backgroundColor: colors.primaria },
  buttonGhost: { backgroundColor: colors.superficie, borderWidth: 1, borderColor: colors.borda },
  buttonText: { color: colors.texto, fontWeight: '700', fontSize: 15 },
  state: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.sm },
  stateTitle: { color: colors.texto, fontSize: 20, fontWeight: '700', textAlign: 'center', marginTop: spacing.md },
  stateMessage: { color: colors.textoSecundario, fontSize: 15, textAlign: 'center', lineHeight: 22 },
  waves: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 56 },
  wave: { width: 8, height: 56, borderRadius: 4, backgroundColor: colors.destaque },
});

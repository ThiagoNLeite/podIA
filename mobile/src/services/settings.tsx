import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export const SPEEDS = [1, 1.25, 1.5] as const;
export type Speed = (typeof SPEEDS)[number];

// Emulador do Android enxerga o PC em 10.0.2.2. Celular via USB: use `adb reverse tcp:8000 tcp:8000`
// e a URL http://localhost:8000. Pela rede Wi-Fi: http://<IP-do-PC>:8000.
export const DEFAULT_API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://10.0.2.2:8000';

const KEY = 'podia:settings';

export interface Settings {
  apiUrl: string;
  speed: Speed;
}

interface SettingsContextValue extends Settings {
  loaded: boolean;
  update: (patch: Partial<Settings>) => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function normalizeUrl(url: string): string {
  const trimmed = url.trim().replace(/\/+$/, '');
  return /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>({ apiUrl: DEFAULT_API_URL, speed: 1 });
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(KEY)
      .then((raw) => {
        if (raw) setSettings((s) => ({ ...s, ...(JSON.parse(raw) as Partial<Settings>) }));
      })
      .catch(() => undefined)
      .finally(() => setLoaded(true));
  }, []);

  const update = (patch: Partial<Settings>) => {
    setSettings((prev) => {
      const next = { ...prev, ...patch };
      if (patch.apiUrl !== undefined) next.apiUrl = normalizeUrl(patch.apiUrl);
      AsyncStorage.setItem(KEY, JSON.stringify(next)).catch(() => undefined);
      return next;
    });
  };

  return (
    <SettingsContext.Provider value={{ ...settings, loaded, update }}>{children}</SettingsContext.Provider>
  );
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings precisa estar dentro de <SettingsProvider>');
  return ctx;
}

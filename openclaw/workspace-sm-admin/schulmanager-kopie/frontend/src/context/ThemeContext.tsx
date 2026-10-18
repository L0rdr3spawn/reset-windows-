import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

export type ThemeMode = 'system' | 'light' | 'dark';

interface ThemeValue {
  mode: ThemeMode;
  setMode: (m: ThemeMode) => void;
  nextMode: () => void;
}

const KEY = 'sm-theme';
const Ctx = createContext<ThemeValue | null>(null);

function readStored(): ThemeMode {
  try {
    const v = window.localStorage.getItem(KEY);
    return v === 'light' || v === 'dark' ? v : 'system';
  } catch {
    return 'system';
  }
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(readStored);

  useEffect(() => {
    const root = document.documentElement;
    if (mode === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', mode);
  }, [mode]);

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    try {
      if (m === 'system') window.localStorage.removeItem(KEY);
      else window.localStorage.setItem(KEY, m);
    } catch {
      /* ignorieren */
    }
  }, []);

  const nextMode = useCallback(() => {
    setMode(mode === 'system' ? 'light' : mode === 'light' ? 'dark' : 'system');
  }, [mode, setMode]);

  const value = useMemo(() => ({ mode, setMode, nextMode }), [mode, setMode, nextMode]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useTheme(): ThemeValue {
  const v = useContext(Ctx);
  if (!v) throw new Error('useTheme außerhalb von ThemeProvider');
  return v;
}

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as SecureStore from 'expo-secure-store';
import { api } from './api';

const AuthContext = createContext(null);

const LANG_CACHE_PREFIX = 'memora_lang_';

async function readCachedLang(patientId) {
  if (!patientId) return '';
  try {
    return (await SecureStore.getItemAsync(`${LANG_CACHE_PREFIX}${patientId}`)) || '';
  } catch {
    return '';
  }
}

async function writeCachedLang(patientId, code) {
  if (!patientId) return;
  try {
    await SecureStore.setItemAsync(`${LANG_CACHE_PREFIX}${patientId}`, code);
  } catch {
    /* ignore storage errors */
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [currentPatient, setCurrentPatient] = useState(null);
  const [pinVerified, setPinVerified] = useState(false);

  const loadPatients = useCallback(async () => {
    try {
      const list = await api.getPatients();
      // Local cache wins so a choice made offline still applies immediately.
      const hydrated = await Promise.all(
        (list || []).map(async (p) => {
          const cached = await readCachedLang(p.id);
          return cached ? { ...p, primary_language: cached } : p;
        }),
      );
      setPatients(hydrated);
      setCurrentPatient((prev) => {
        if (prev && hydrated.some((p) => p.id === prev.id)) {
          return hydrated.find((p) => p.id === prev.id) || prev;
        }
        return hydrated[0] || null;
      });
    } catch {}
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        await loadPatients();
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [loadPatients]);

  const login = useCallback(async (email, password) => {
    const res = await api.login({ email, password });
    setUser(res.user);
    await loadPatients();
    return res.user;
  }, [loadPatients]);

  const signup = useCallback(async (payload) => {
    const res = await api.signup(payload);
    setUser(res.user);
    await loadPatients();
    return res.user;
  }, [loadPatients]);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
    setPatients([]);
    setCurrentPatient(null);
    setPinVerified(false);
  }, []);

  const selectPatient = useCallback((id) => {
    setPatients((list) => {
      const found = list.find((p) => p.id === id);
      if (found) setCurrentPatient(found);
      return list;
    });
    setPinVerified(false);
  }, []);

  const setLanguage = useCallback(async (code) => {
    const pid = currentPatient?.id;
    if (!pid) return;
    setCurrentPatient((prev) => (prev ? { ...prev, primary_language: code } : prev));
    setPatients((list) => list.map((p) => (p.id === pid ? { ...p, primary_language: code } : p)));
    await writeCachedLang(pid, code);
    try {
      await api.updatePatientLanguage(pid, code);
    } catch {
      /* keep the local value; the backend write is best-effort */
    }
  }, [currentPatient?.id]);

  const value = useMemo(
    () => ({ user, loading, patients, currentPatient, pinVerified, setPinVerified, selectPatient, setLanguage, loadPatients, login, signup, logout }),
    [user, loading, patients, currentPatient, pinVerified, selectPatient, setLanguage, loadPatients, login, signup, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

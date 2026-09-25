import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [currentPatient, setCurrentPatient] = useState(null);
  const [pinVerified, setPinVerified] = useState(false);

  const loadPatients = useCallback(async () => {
    try {
      const list = await api.getPatients();
      setPatients(list || []);
      setCurrentPatient((prev) => {
        if (prev && list.some((p) => p.id === prev.id)) return prev;
        return list[0] || null;
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

  const value = useMemo(
    () => ({ user, loading, patients, currentPatient, pinVerified, setPinVerified, selectPatient, loadPatients, login, signup, logout }),
    [user, loading, patients, currentPatient, pinVerified, selectPatient, loadPatients, login, signup, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

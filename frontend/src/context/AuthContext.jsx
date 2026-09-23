import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, setAuthToken } from '../services/api';
import { isSupabaseAuthEnabled, supabase } from '../services/supabase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    try {
      const me = await api.me();
      setUser(me);
      return me;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    (async () => {
      // If Supabase client auth is used directly, mirror its token into the API client.
      if (isSupabaseAuthEnabled && supabase) {
        const { data } = await supabase.auth.getSession();
        if (data?.session?.access_token) setAuthToken(data.session.access_token);
        supabase.auth.onAuthStateChange((_event, session) => {
          setAuthToken(session?.access_token || '');
        });
      }
      await refresh();
      setLoading(false);
    })();
  }, [refresh]);

  const login = useCallback(async (email, password) => {
    setError('');
    // Prefer backend login (works in demo mode AND Supabase mode).
    const res = await api.login({ email, password });
    setUser(res.user);
    return res.user;
  }, []);

  const signup = useCallback(async (payload) => {
    setError('');
    const res = await api.signup(payload);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(async () => {
    try {
      if (isSupabaseAuthEnabled && supabase) await supabase.auth.signOut();
    } catch {
      /* ignore */
    }
    api.logout();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, error, setError, login, signup, logout, refresh }),
    [user, loading, error, login, signup, logout, refresh],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

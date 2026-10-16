import React, { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '../services/supabase';
import { IS_DEMO_MODE } from '../config/demo';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  role: string | null;
  loading: boolean;
  isDemoMode: boolean;
  isAuthenticated: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  role: null,
  loading: true,
  isDemoMode: false,
  isAuthenticated: false,
  signOut: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [role, setRole] = useState<string | null>(IS_DEMO_MODE ? 'Not authenticated' : null);
  const [loading, setLoading] = useState<boolean>(!IS_DEMO_MODE);

  useEffect(() => {
    // Attempt to read session from Supabase client (if credentials configured)
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchProfile(session.user.id);
      } else {
        setLoading(false);
      }
    }).catch(() => {
      setLoading(false);
    });

    // Listen for auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchProfile(session.user.id);
      } else {
        setRole(IS_DEMO_MODE ? 'Not authenticated' : null);
        setLoading(false);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchProfile = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('name, preferred_language')
        .eq('user_id', userId)
        .maybeSingle();

      if (data && !error) {
        setRole('farmer');
      } else {
        setRole('farmer');
      }
    } catch (e) {
      console.error("Error fetching profile", e);
      setRole('farmer');
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    if (error) {
      throw error;
    }
    setSession(null);
    setUser(null);
    setRole(IS_DEMO_MODE ? 'Not authenticated' : null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      session,
      role,
      loading,
      isDemoMode: IS_DEMO_MODE && !session,
      isAuthenticated: !!session,
      signOut
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

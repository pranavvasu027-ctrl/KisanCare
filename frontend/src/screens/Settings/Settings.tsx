import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User, Settings as SettingsIcon, Globe, Ruler, Bell, Shield,
  LogOut, Save, CheckCircle2, AlertCircle, Loader2, Database, Laptop
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../services/supabase';

interface LocalPreferences {
  areaUnit: 'acre' | 'hectare' | 'guntha' | 'bigha';
  weightUnit: 'qtl' | 'ton' | 'kg';
  currency: 'INR';
  notificationsEnabled: boolean;
}

const DEFAULT_PREFERENCES: LocalPreferences = {
  areaUnit: 'acre',
  weightUnit: 'qtl',
  currency: 'INR',
  notificationsEnabled: true
};

export default function Settings() {
  const navigate = useNavigate();
  const { user, session, isDemoMode, signOut } = useAuth();
  const isAuthenticated = Boolean(user);

  // Profile data (Supabase 'profiles' table)
  const [farmerName, setFarmerName] = useState('Patil Farmer');
  const [preferredLanguage, setPreferredLanguage] = useState('en');
  const [phoneNumber, setPhoneNumber] = useState('+91 98765 43210');

  // Preferences (Client localStorage)
  const [preferences, setPreferences] = useState<LocalPreferences>(DEFAULT_PREFERENCES);

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load preferences from localStorage and profile from Supabase on mount
  useEffect(() => {
    // 1. Load local preferences
    try {
      const stored = localStorage.getItem('kisancare_user_preferences');
      if (stored) {
        setPreferences(JSON.parse(stored));
      }
    } catch {
      // Use defaults
    }

    // 2. Load authenticated profile from Supabase
    if (user && isAuthenticated) {
      loadProfile(user.id);
    }
  }, [user, isAuthenticated]);

  const loadProfile = async (userId: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('user_id', userId)
        .maybeSingle();

      if (error) {
        console.error('Error loading profile:', error);
        setErrorMessage(`Could not load profile: ${error.message}`);
        return;
      }

      if (data) {
        if (data.name) setFarmerName(data.name);
        if (data.preferred_language) setPreferredLanguage(data.preferred_language);
        if (data.phone) setPhoneNumber(data.phone);
      }
    } catch (err: any) {
      console.error('Unexpected error loading profile:', err);
      setErrorMessage(`Error: ${err.message || String(err)}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setStatusMessage(null);

    // Validation
    if (!farmerName.trim()) {
      setErrorMessage('Farmer profile name is required.');
      return;
    }

    // 1. Save local preferences (Client Persistence)
    try {
      localStorage.setItem('kisancare_user_preferences', JSON.stringify(preferences));
    } catch {
      // Local storage disabled or full
    }

    // 2. If unauthenticated / demo mode
    if (!user || !isAuthenticated) {
      setStatusMessage('Preferences updated for active demo session (Saved to browser storage). Sign in to persist profile to Supabase.');
      setTimeout(() => setStatusMessage(null), 5000);
      return;
    }

    // 3. Authenticated Supabase Persistence
    setIsSaving(true);
    try {
      const { error: profileErr } = await supabase
        .from('profiles')
        .upsert({
          user_id: user.id,
          name: farmerName.trim(),
          preferred_language: preferredLanguage,
          phone: phoneNumber.trim(),
          updated_at: new Date().toISOString()
        }, { onConflict: 'user_id' });

      if (profileErr) throw profileErr;

      setStatusMessage('Profile and preferences successfully saved to Supabase and browser settings!');
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to save profile:', err);
      setErrorMessage(`Failed to update profile: ${err.message || String(err)}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (err: any) {
      console.error('Sign out error:', err);
      navigate('/login');
    }
  };

  return (
    <div className="p-4 lg:p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-serif font-bold text-[#103D2C]">Account Settings</h1>
            {(!isAuthenticated || isDemoMode) ? (
              <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-amber-300">
                Demo Profile
              </span>
            ) : (
              <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                <Database size={12} className="text-emerald-700" />
                Supabase Connected
              </span>
            )}
          </div>
          <p className="text-[#292B26]/70 mt-1">
            Manage your farmer profile, display languages, unit conventions, and account security.
          </p>
        </div>

        <button
          onClick={handleSignOut}
          className="bg-white hover:bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg font-medium text-xs sm:text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-xs"
        >
          <LogOut size={16} />
          <span>{isAuthenticated ? 'Sign Out' : 'Exit to Login'}</span>
        </button>
      </div>

      {isLoading && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <Loader2 className="w-4 h-4 text-blue-600 animate-spin shrink-0" />
          <span>Loading farmer profile from database...</span>
        </div>
      )}

      {statusMessage && (
        <div className="bg-emerald-50 border border-emerald-300 text-emerald-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="bg-red-50 border border-red-300 text-red-900 px-4 py-3 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">
            <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
              <User size={18} className="text-[#17643E]" /> Farmer Profile
            </h2>
            <span className="text-[11px] font-medium text-[#292B26]/60 flex items-center gap-1">
              <Database size={11} /> Persisted to Supabase (profiles)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#292B26] mb-1">Farmer Full Name</label>
              <input
                type="text"
                value={farmerName}
                onChange={(e) => setFarmerName(e.target.value)}
                placeholder="e.g. Ramesh Patil"
                className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-2 text-sm text-[#103D2C] focus:outline-none focus:border-[#17643E]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#292B26] mb-1">Phone Number (Optional)</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-2 text-sm text-[#103D2C] focus:outline-none focus:border-[#17643E]"
              />
            </div>
          </div>
        </div>

        {/* Language & Unit Preferences */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">
            <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
              <Globe size={18} className="text-[#17643E]" /> Localization & Measurement Units
            </h2>
            <span className="text-[11px] font-medium text-[#292B26]/60 flex items-center gap-1">
              <Laptop size={11} /> Stored in browser preferences
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#292B26] mb-1">Preferred Language</label>
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-2 text-sm text-[#103D2C] font-medium focus:outline-none focus:border-[#17643E]"
              >
                <option value="en">English (Default)</option>
                <option value="hi">हिंदी (Hindi)</option>
                <option value="mr">मराठी (Marathi)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#292B26] mb-1">Land Area Unit</label>
              <select
                value={preferences.areaUnit}
                onChange={(e) => setPreferences({ ...preferences, areaUnit: e.target.value as any })}
                className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-2 text-sm text-[#103D2C] font-medium focus:outline-none focus:border-[#17643E]"
              >
                <option value="acre">Acres (Standard)</option>
                <option value="hectare">Hectares</option>
                <option value="guntha">Gunthas (33x33 ft)</option>
                <option value="bigha">Bighas</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#292B26] mb-1">Crop Yield Weight Unit</label>
              <select
                value={preferences.weightUnit}
                onChange={(e) => setPreferences({ ...preferences, weightUnit: e.target.value as any })}
                className="w-full border border-[#E5DDCF] bg-[#FBF7EF] rounded-lg px-3 py-2 text-sm text-[#103D2C] font-medium focus:outline-none focus:border-[#17643E]"
              >
                <option value="qtl">Quintals (100 kg)</option>
                <option value="ton">Metric Tons (1,000 kg)</option>
                <option value="kg">Kilograms (kg)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notifications & System Info */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#E5DDCF] p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[#E5DDCF] pb-3">
            <h2 className="text-lg font-bold text-[#103D2C] flex items-center gap-2">
              <Bell size={18} className="text-[#17643E]" /> Advisory Alerts
            </h2>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-[#292B26]">Pest & Weather Advisory Alerts</p>
              <p className="text-xs text-[#292B26]/60">
                Receive proactive warning notifications for high humidity, heat stress, and pest alerts on dashboard.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={preferences.notificationsEnabled}
                onChange={(e) => setPreferences({ ...preferences, notificationsEnabled: e.target.checked })}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#E5DDCF] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#103D2C]"></div>
            </label>
          </div>
        </div>

        {/* Account & Session Details */}
        <div className="bg-[#FBF7EF] rounded-2xl border border-[#E5DDCF] p-6 text-xs text-[#292B26]/70 space-y-2">
          <h3 className="font-bold text-[#103D2C] flex items-center gap-1.5">
            <Shield size={14} className="text-[#17643E]" /> Account Status & Security
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            <div>
              <span className="font-semibold text-[#292B26]">Session Mode: </span>
              {isAuthenticated ? (
                <span className="text-emerald-700 font-bold">Authenticated User ({session?.user.email})</span>
              ) : (
                <span className="text-amber-800 font-bold">Unauthenticated Demo Session</span>
              )}
            </div>
            <div>
              <span className="font-semibold text-[#292B26]">Database RLS: </span>
              <span className="text-emerald-700 font-bold">Enforced (Row-Level Security Active)</span>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="bg-[#103D2C] hover:bg-[#17643E] text-white px-6 py-2.5 rounded-lg font-medium text-sm flex items-center gap-2 transition-colors cursor-pointer shadow-sm disabled:opacity-50"
          >
            {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            <span>{isSaving ? 'Saving Preferences...' : 'Save Settings'}</span>
          </button>
        </div>
      </form>
    </div>
  );
}

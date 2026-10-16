import { createClient } from '@supabase/supabase-js';
import { IS_DEMO_MODE } from '../config/demo';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

const isMissingCredentials =
  !supabaseUrl ||
  supabaseUrl === 'https://placeholder.supabase.co' ||
  !supabaseAnonKey ||
  supabaseAnonKey === 'placeholder_key';

// In standard mode, enforce Supabase credentials
if (!IS_DEMO_MODE && isMissingCredentials) {
  throw new Error(
    'Supabase credentials missing or invalid. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in frontend/.env, or set VITE_DEMO_MODE=true.'
  );
}

// In demo mode with missing credentials, initialize with dummy endpoints so module imports succeed safely
export const supabase = createClient(
  supabaseUrl || 'https://placeholder.supabase.co',
  supabaseAnonKey || 'placeholder_key'
);

function getEnv(name: keyof ImportMetaEnv, fallback: string): string {
  const value = import.meta.env[name]
  if (typeof value === 'string' && value.trim() !== '') {
    return value.trim()
  }
  return fallback
}

export const env = {
  apiBaseUrl: getEnv('VITE_API_BASE_URL', 'https://papercraft.onrender.com').replace(/\/$/, ''),
  supabaseUrl: getEnv('VITE_SUPABASE_URL', 'https://placeholder.supabase.co'),
  supabaseAnonKey: getEnv('VITE_SUPABASE_ANON_KEY', 'placeholder-anon-key'),
} as const

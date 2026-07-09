-- Permitir que hash_password sea nulo en public.users para soportar autenticación por Supabase (Magic Links, OTP, Gotrue)
ALTER TABLE users ALTER COLUMN hash_password DROP NOT NULL;

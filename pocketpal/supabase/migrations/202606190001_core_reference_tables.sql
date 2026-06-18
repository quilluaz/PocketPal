CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS public.currencies (
  code CHAR(3) PRIMARY KEY,
  exponent SMALLINT NOT NULL CHECK (exponent BETWEEN 0 AND 6),
  name TEXT NOT NULL,
  symbol TEXT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS public.user_preferences (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  timezone TEXT NOT NULL DEFAULT 'Asia/Manila',
  base_currency CHAR(3) NOT NULL DEFAULT 'PHP' REFERENCES public.currencies(code),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TRIGGER set_user_preferences_updated_at
BEFORE UPDATE ON public.user_preferences
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE IF NOT EXISTS public.exchange_rates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  base_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  quote_currency CHAR(3) NOT NULL REFERENCES public.currencies(code),
  rate NUMERIC(20, 10) NOT NULL CHECK (rate > 0),
  rate_date DATE NOT NULL,
  source TEXT NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (base_currency, quote_currency, rate_date, source)
);

INSERT INTO public.currencies (code, exponent, name, symbol)
VALUES
  ('PHP', 2, 'Philippine Peso', 'PHP'),
  ('USD', 2, 'United States Dollar', '$'),
  ('JPY', 0, 'Japanese Yen', 'JPY'),
  ('KWD', 3, 'Kuwaiti Dinar', 'KD')
ON CONFLICT (code) DO NOTHING;


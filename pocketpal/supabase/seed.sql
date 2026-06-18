INSERT INTO public.currencies (code, exponent, name, symbol)
VALUES
  ('PHP', 2, 'Philippine Peso', 'PHP'),
  ('USD', 2, 'United States Dollar', '$'),
  ('JPY', 0, 'Japanese Yen', 'JPY'),
  ('KWD', 3, 'Kuwaiti Dinar', 'KD')
ON CONFLICT (code) DO NOTHING;

INSERT INTO public.exchange_rates
(base_currency, quote_currency, rate, rate_date, source)
VALUES
('PHP', 'USD', 56.8500000000, CURRENT_DATE, 'seed'),
('PHP', 'JPY', 0.3900000000, CURRENT_DATE, 'seed'),
('PHP', 'KWD', 185.0000000000, CURRENT_DATE, 'seed'),
('PHP', 'PHP', 1.0000000000, CURRENT_DATE, 'seed')
ON CONFLICT DO NOTHING;


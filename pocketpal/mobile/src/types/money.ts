export type CurrencyCode = "PHP" | "USD" | "JPY" | "KWD" | string;

export type CurrencyMeta = {
  code: CurrencyCode;
  exponent: number;
  name: string;
  symbol?: string | null;
};

export type ExchangeRate = {
  base_currency: CurrencyCode;
  quote_currency: CurrencyCode;
  rate: string;
  rate_date: string;
  source: string;
  fetched_at: string;
};

export type RatesResponse = {
  base_currency: CurrencyCode;
  currencies: CurrencyMeta[];
  rates: ExchangeRate[];
};


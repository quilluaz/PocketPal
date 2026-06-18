import { CurrencyMeta } from "../types/money";

export const fallbackCurrencies: CurrencyMeta[] = [
  { code: "PHP", exponent: 2, name: "Philippine Peso", symbol: "PHP" },
  { code: "USD", exponent: 2, name: "United States Dollar", symbol: "$" },
  { code: "JPY", exponent: 0, name: "Japanese Yen", symbol: "JPY" },
  { code: "KWD", exponent: 3, name: "Kuwaiti Dinar", symbol: "KD" }
];

export function currencyExponent(currency: string, currencies: CurrencyMeta[] = fallbackCurrencies): number {
  return currencies.find((item) => item.code === currency)?.exponent ?? 2;
}

export function majorToMinor(amountMajor: string, exponent: number): number {
  const normalized = amountMajor.replace(/,/g, "").trim();
  if (!normalized) {
    return 0;
  }
  const [wholeRaw, fractionRaw = ""] = normalized.split(".");
  const sign = wholeRaw.startsWith("-") ? -1 : 1;
  const whole = Math.abs(Number.parseInt(wholeRaw || "0", 10));
  const fraction = fractionRaw.padEnd(exponent, "0").slice(0, exponent);
  const fractionValue = exponent === 0 ? 0 : Number.parseInt(fraction || "0", 10);
  return sign * (whole * 10 ** exponent + fractionValue);
}

export function formatMoney(
  amountMinor: number,
  currency: string,
  currencies: CurrencyMeta[] = fallbackCurrencies
): string {
  const exponent = currencyExponent(currency, currencies);
  const amountMajor = amountMinor / 10 ** exponent;
  return new Intl.NumberFormat(undefined, {
    style: "currency",
    currency,
    minimumFractionDigits: exponent,
    maximumFractionDigits: exponent
  }).format(amountMajor);
}


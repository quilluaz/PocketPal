import type { CurrencyMeta } from "../types/money";

export const fallbackCurrencies: CurrencyMeta[] = [
  { code: "PHP", exponent: 2, name: "Philippine Peso", symbol: "PHP" },
  { code: "USD", exponent: 2, name: "United States Dollar", symbol: "$" },
  { code: "JPY", exponent: 0, name: "Japanese Yen", symbol: "JPY" },
  { code: "KWD", exponent: 3, name: "Kuwaiti Dinar", symbol: "KD" }
];

export function currencyMeta(
  currency: string,
  currencies: CurrencyMeta[] = fallbackCurrencies
): CurrencyMeta {
  const normalized = currency.toUpperCase();
  return (
    currencies.find((item) => item.code === normalized) ?? {
      code: normalized,
      exponent: 2,
      name: normalized,
      symbol: normalized
    }
  );
}

export function currencyExponent(
  currency: string,
  currencies: CurrencyMeta[] = fallbackCurrencies
): number {
  return currencyMeta(currency, currencies).exponent;
}

function minorScale(exponent: number): bigint {
  return 10n ** BigInt(exponent);
}

function localizedInteger(value: bigint): string {
  return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function displaySymbol(currency: string, symbol?: string | null): string {
  if (currency === "PHP") {
    return "\u20b1";
  }
  if (currency === "JPY") {
    return "\u00a5";
  }
  return symbol || currency;
}

export function majorToMinor(amountMajor: string, exponent: number): number {
  const normalized = amountMajor.replace(/,/g, "").trim();
  if (!normalized) {
    return 0;
  }
  const sign = normalized.startsWith("-") ? -1n : 1n;
  const unsigned = normalized.replace(/^[+-]/, "");
  const [wholeRaw = "0", fractionRaw = ""] = unsigned.split(".");
  const wholeDigits = wholeRaw.replace(/\D/g, "") || "0";
  const fractionDigits = fractionRaw.replace(/\D/g, "").padEnd(exponent, "0").slice(0, exponent);
  const wholeMinor = BigInt(wholeDigits) * minorScale(exponent);
  const fractionMinor = exponent === 0 ? 0n : BigInt(fractionDigits || "0");
  return Number(sign * (wholeMinor + fractionMinor));
}

export function formatMoney(
  amountMinor: number,
  currency: string,
  currencies: CurrencyMeta[] = fallbackCurrencies
): string {
  const meta = currencyMeta(currency, currencies);
  const exponent = meta.exponent;
  const scale = minorScale(exponent);
  const minor = BigInt(amountMinor);
  const sign = minor < 0n ? "-" : "";
  const absoluteMinor = minor < 0n ? -minor : minor;
  const whole = absoluteMinor / scale;
  const fraction = absoluteMinor % scale;
  const fractionText =
    exponent === 0 ? "" : `.${fraction.toString().padStart(exponent, "0")}`;
  const symbol = displaySymbol(meta.code, meta.symbol);
  const spacer = symbol.length > 1 ? " " : "";

  return `${sign}${symbol}${spacer}${localizedInteger(whole)}${fractionText}`;
}

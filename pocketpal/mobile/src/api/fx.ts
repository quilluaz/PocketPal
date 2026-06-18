import { RatesResponse } from "../types/money";
import { apiFetch } from "./client";

export function fetchRates(): Promise<RatesResponse> {
  return apiFetch<RatesResponse>("/fx/rates");
}


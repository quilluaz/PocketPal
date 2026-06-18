import { Dashboard } from "../types/dashboard";
import { apiFetch } from "./client";

export function fetchDashboard(): Promise<Dashboard> {
  return apiFetch<Dashboard>("/dashboard");
}


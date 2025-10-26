import { apiFetch } from "./client";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function loginRequest(email: string, password: string) {
  // FastAPI erwartet JSON im Body
  return apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

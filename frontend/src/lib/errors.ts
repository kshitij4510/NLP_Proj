import axios from "axios";
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data?.detail === "string") return data.detail;
    if (typeof data?.message === "string") return data.message;
    if (!error.response) return "Cannot reach the backend. Check that the server is running.";
    return `Request failed (${error.response.status}). Please retry.`;
  }
  return error instanceof Error ? error.message : "The request failed. Please retry.";
}

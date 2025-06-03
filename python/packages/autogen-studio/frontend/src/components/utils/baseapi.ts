import { getServerUrl } from "./utils";

type ContentType = "application/json" | "multipart/form-data" | "application/x-www-form-urlencoded";

// baseApi.ts
export abstract class BaseAPI {
  protected getBaseUrl(): string {
    return getServerUrl();
  }

  protected getHeaders(content_type?: ContentType) {
    // Get auth token from localStorage
    const token = localStorage.getItem("auth_token");

    const headers: HeadersInit = {
      "Content-Type": content_type ?? "application/json", // use json by default
    };

    // Add authorization header if token exists
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  // Other common methods
}

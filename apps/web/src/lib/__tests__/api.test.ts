import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiClientError, api } from "@/lib/api";

describe("ApiClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("handles successful JSON response", async () => {
    const mockHealth = {
      status: "healthy",
      service: "pokerlab-api",
      timestamp: "2026-10-08T15:00:00Z",
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockHealth,
      headers: new Headers({ "X-Request-ID": "test-req-123" }),
    } as unknown as Response);

    const result = await api.getHealth();
    expect(result.status).toBe("healthy");
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/health"),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "X-Request-ID": expect.any(String),
        }),
      }),
    );
  });

  it("parses standard error response on 4xx/5xx failure", async () => {
    const mockErrorPayload = {
      error: {
        code: "PROFILE_NOT_FOUND",
        message: "Profile not found",
        details: { id: "123" },
        request_id: "req-err-456",
      },
    };

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: async () => mockErrorPayload,
      headers: new Headers({ "X-Request-ID": "req-err-456" }),
    } as unknown as Response);

    await expect(api.getProfile("123")).rejects.toThrow(ApiClientError);
    try {
      await api.getProfile("123");
    } catch (err) {
      const apiErr = err as ApiClientError;
      expect(apiErr.code).toBe("PROFILE_NOT_FOUND");
      expect(apiErr.status).toBe(404);
      expect(apiErr.requestId).toBe("req-err-456");
    }
  });
});

import type { InternshipDetail, MatchResponse, StudentProfile } from "../types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";
const REQUEST_TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type MatchPayload = {
  profile: StudentProfile;
  internships: InternshipDetail[];
};

export type ResumeExtractResponse = {
  text: string;
  filename?: string;
  structured_profile?: StudentProfile;
};

export type ResumeTextParseResponse = {
  structured_profile?: StudentProfile;
};

export type InternshipExtractResponse = {
  internship?: InternshipDetail;
};

type RequestOptions = {
  method?: "GET" | "POST";
  body?: BodyInit;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

async function readBody(response: Response): Promise<unknown> {
  const raw = await response.text();
  if (!raw.trim()) return null;
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return raw;
  }
}

function detailMessage(detail: unknown): string | null {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          const msg = (item as { msg?: unknown }).msg;
          return typeof msg === "string" ? msg : null;
        }
        return null;
      })
      .filter((item): item is string => Boolean(item && item.trim()));
    if (parts.length > 0) return parts.join("; ");
  }
  return null;
}

function errorMessageFromBody(body: unknown, status: number): string {
  if (typeof body === "string" && body.trim()) return body.trim().slice(0, 300);

  if (body && typeof body === "object") {
    const record = body as Record<string, unknown>;
    const detail = detailMessage(record.detail);
    if (detail) return detail;
    if (typeof record.message === "string" && record.message.trim()) {
      return record.message;
    }
    if (typeof record.error === "string" && record.error.trim()) {
      return record.error;
    }
  }

  return `Request failed with status ${status}.`;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const { signal } = options;
  let timedOut = false;

  const timeout = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);

  const forwardAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", forwardAbort, { once: true });
  }

  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      method: options.method ?? "POST",
      body: options.body,
      headers: options.headers,
      signal: controller.signal,
    });

    const body = await readBody(response);

    if (!response.ok) {
      throw new ApiError(response.status, errorMessageFromBody(body, response.status));
    }

    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (isAbortError(error)) {
      if (signal?.aborted) throw error;
      if (timedOut) {
        throw new ApiError(0, "The analysis service took too long to respond. Try again.");
      }
      throw error;
    }
    throw new ApiError(
      0,
      "Could not reach the analysis service. Check that the backend is running and try again.",
    );
  } finally {
    window.clearTimeout(timeout);
    signal?.removeEventListener("abort", forwardAbort);
  }
}

export function extractResume(file: File, signal?: AbortSignal): Promise<ResumeExtractResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<ResumeExtractResponse>("/api/resume/extract", {
    method: "POST",
    body: formData,
    signal,
  });
}

export function parseResumeText(
  text: string,
  signal?: AbortSignal,
): Promise<ResumeTextParseResponse> {
  return request<ResumeTextParseResponse>("/api/resume/parse-text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal,
  });
}

export function extractInternship(
  input: { title: string; company: string; description: string },
  signal?: AbortSignal,
): Promise<InternshipExtractResponse> {
  return request<InternshipExtractResponse>("/api/internship/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
    signal,
  });
}

export function match(payload: MatchPayload, signal?: AbortSignal): Promise<MatchResponse> {
  return request<MatchResponse>("/api/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}

export function reanalyze(payload: MatchPayload, signal?: AbortSignal): Promise<MatchResponse> {
  return request<MatchResponse>("/api/reanalyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return "Something went wrong. Try again.";
}

export { isAbortError };

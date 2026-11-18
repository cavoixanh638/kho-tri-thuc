export const SESSION_EXPIRED_EVENT = 'session-expired';

export type Session = { authenticated: boolean; username: string | null; csrf_token: string };
export type Receipt = { capture_id: string; item_id: string; received_at: string; state: string };
export type Capture = Receipt & {
  raw_kind: 'link' | 'text';
  raw_text: string;
  original_url: string;
  source_channel: string;
};
export type Asset = { asset_id: string; filename: string; status: string; mime: string };
export type Item = {
  item_id: string;
  kind: 'link' | 'text' | 'file';
  title: string;
  note: string;
  description: string;
  saved_at: string;
  published_at: string | null;
  updated_at: string;
  favorite: boolean;
  deleted: boolean;
  classification_status: string;
  original_url: string;
  source_fetch?: string;
  asset_storage?: string;
  content_extract?: string;
  assets: Asset[];
};
export type Page<T> = { results: T[]; next_offset: number | null };
export type DriveStatus = { state: string; display_name: string };

export class ApiError extends Error {
  constructor(readonly status: number) {
    super(`HTTP ${status}`);
    this.name = 'ApiError';
  }
}

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: object;
  csrf?: string;
  idempotencyKey?: string;
  signal?: AbortSignal;
};

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers({ Accept: 'application/json' });
  if (options.body) headers.set('Content-Type', 'application/json');
  if (options.csrf) headers.set('X-CSRFToken', options.csrf);
  if (options.idempotencyKey) headers.set('Idempotency-Key', options.idempotencyKey);

  const controller = new AbortController();
  const cancel = () => controller.abort();
  const external = options.signal;
  if (external?.aborted) cancel();
  external?.addEventListener('abort', cancel, { once: true });
  const timer = window.setTimeout(cancel, 15_000);
  try {
    const response = await fetch(`/api/v1${path}`, {
      method: options.method,
      headers,
      body: options.body && JSON.stringify(options.body),
      credentials: 'same-origin',
      cache: 'no-store',
      signal: controller.signal,
    });
    if (!response.ok) {
      if (response.status === 401 && path !== '/session') {
        window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
      }
      throw new ApiError(response.status);
    }
    return await response.json() as T;
  } finally {
    window.clearTimeout(timer);
    external?.removeEventListener('abort', cancel);
  }
}

export function externalHttpUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    if ((url.protocol === 'https:' || url.protocol === 'http:') && !url.username && !url.password) {
      return url.href;
    }
  } catch {
    return undefined;
  }
}

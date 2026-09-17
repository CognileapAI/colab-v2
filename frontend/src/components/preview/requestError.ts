/** Authentication expiry is handled by the API client; preserve hidden-object boundaries. */
export function requestMessage(status: number, body: unknown, fallback: string): string {
  if (status === 401) return '로그인이 만료됐어요. 다시 로그인해 주세요.';
  if (status === 403) return '이 작업을 할 권한이 없어요.';
  if (status === 404) return '대상이 없거나 접근 권한이 없어요.';
  const message = (body as { message?: unknown } | undefined)?.message;
  return typeof message === 'string' && message ? message : fallback;
}

/** A definitive authorization rejection never created a render job. */
export class PreviewRequestRejected extends Error {}

// 다운로드 티켓 → 바이트. **`<a href>` 로는 Bearer 를 싣지 못하고 `fetch` 로는 302 를 따라갈 때
// 자격을 잃는다** — 그래서 응답이 티켓이고, 바이트는 티켓 URL 로 내비게이션한다 (`PLAN-SoT §9 〈278〉-(다)`).
//
// 티켓 URL 은 둘 중 하나다 — 저장 모드 local 과 묶음(zip)은 이 seam 의 상대 경로(`/downloads/{ticket}`),
// s3 모드의 단일 파일은 프리사인드 GET 절대 URL. **가리지 않고 그대로 쓴다**: 상대 경로는 지금 열려
// 있는 창의 오리진에 붙고, 절대 URL 은 손대지 않는다 (`api/client.ts` 의 `resolvedBaseUrl` 과 같은 태도).
import { createContext, useContext } from 'react';
import type { DownloadTicket } from './types';

const ABSOLUTE = /^[a-z][a-z0-9+.-]*:/i;

/** 상대 경로면 현재 오리진에 붙이고, 절대 URL 이면 그대로. */
export function resolveTicketUrl(url: string): string {
  if (ABSOLUTE.test(url)) return url;
  const origin = typeof window === 'undefined' ? '' : (window.location?.origin ?? '');
  return origin ? new URL(url, origin).toString() : url;
}

/**
 * 티켓으로 저장을 시작한다 — `<a download>` 를 만들어 누르고 바로 걷는다.
 * 저장 이름은 티켓의 `fileName` 이다 (같은 오리진에서만 브라우저가 이 힌트를 쓴다 —
 * 프리사인드 절대 URL 은 서버 쪽 `Content-Disposition` 이 이름을 정한다).
 */
export function startDownload(ticket: DownloadTicket): void {
  const a = document.createElement('a');
  a.href = resolveTicketUrl(ticket.url);
  a.download = ticket.fileName;
  a.rel = 'noopener';
  a.hidden = true;
  document.body.appendChild(a);
  try {
    a.click();
  } finally {
    a.remove();
  }
}

/**
 * 시험이 갈아 끼우는 자리 — 기본값은 실제 내비게이션(`startDownload`)이다.
 * 화면은 티켓을 받아 이 함수에 넘길 뿐, 그 뒤는 모른다.
 */
export const DownloadContext = createContext<(ticket: DownloadTicket) => void>(startDownload);

export function useStartDownload(): (ticket: DownloadTicket) => void {
  return useContext(DownloadContext);
}

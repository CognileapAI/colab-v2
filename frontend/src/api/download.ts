// 원본 내려받기 한 자리 (`ST-1`).
//
// **왜 링크를 그냥 두지 않는가.** `<a href>` 가 만드는 요청에는 브라우저가 우리 헤더를
// 붙여 주지 않는다 — 세션 토큰은 `localStorage` 에 있고 첨부는 `client.ts` 미들웨어가
// 한다(`〈90〉-㉮`). 그래서 링크를 그대로 두면 **누른 순간 401** 이다. 눌러서 안 열리는
// 버튼을 화면에 두지 않는다.
//
// **여기서 인증을 다시 붙이지 않는다.** 생성된 클라이언트(`api`)를 그대로 부르므로
// 토큰을 아는 자리는 여전히 `client.ts` 한 곳이다.
//
// ⭑ **⟨개정 병합 창 8-a · `〈339〉`-(다) · Ted 판정 `〈334〉`-㉳-⑥⟩ 응답이 302 가 아니라 티켓이다.**
//   ／ 종전 ~~「서버는 302 로 「바이트가 있는 자리」를 알려 주고 `fetch` 가 그 한 바퀴를 따라간다」~~ —
//   그 판은 `main` 줄기의 것이고 **집행된 적이 없다**(계약은 이 op 을 줄곧 501 로 들고 있었다).
//   병합된 계약 `fe-core.yaml` 의 `downloadDataset` 은 **200 ＋ `DownloadTicket`** 이다:
//   `fetch` 는 302 를 따라갈 때 자격을 잃고 `<a href>` 는 Bearer 를 못 싣는다 — 그래서 티켓이다.
//   **이력은 티켓 발급 시점에 쌓인다**(바이트 시점이 아니다 · 계약 산문).
//
// ⚠ **바이트 한 바퀴는 여기서도 `fetch` 다** — 티켓 URL 을 받아 바이트를 읽고 blob 으로 저장한다.
//   `detail/download.ts` 의 `startDownload` 는 같은 일을 **내비게이션**으로 하고, 이 자리는
//   **blob 저장**으로 한다. 둘 다 티켓을 입력으로 받으므로 계약은 하나다.
//   저장 이름은 서버가 정한다 — 티켓의 `fileName`, 없으면 바이트 응답의 `Content-Disposition`.
//   **없으면 지어내지 않고** 데이터셋 ID 로 떨어진다.
import { api } from './client';
import { resolveTicketUrl } from '../components/detail/download';

/** `Content-Disposition` 이 말하는 이름. 서버가 안 주면 데이터셋 ID 로 떨어진다. */
export function fileNameFrom(disposition: string | null, fallback: string): string {
  if (!disposition) return fallback;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (star) {
    try {
      return decodeURIComponent((star[1] ?? '').trim()) || fallback;
    } catch {
      /* 못 읽으면 지어내지 않고 아래로 떨어진다 */
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(disposition);
  return plain && plain[1] ? plain[1].trim() : fallback;
}

export async function downloadDataset(datasetId: string): Promise<void> {
  // ⑴ 티켓 — 인증된 클라이언트로. 이 응답 시점에 다운로드 이력이 쌓인다.
  const { data, response } = await api.GET('/datasets/{datasetId}/download', {
    params: { path: { datasetId } },
  });
  if (!response.ok || !data) {
    throw new Error(`다운로드가 열리지 않았어요 (${response.status})`);
  }
  const ticket = data as { url: string; fileName?: string };

  // ⑵ 바이트 — 티켓이 곧 자격이라(`getDownloadBytes` 는 `security: []`) 헤더를 더 붙이지 않는다.
  const bytes = await fetch(resolveTicketUrl(ticket.url));
  if (!bytes.ok) {
    throw new Error(`다운로드가 열리지 않았어요 (${bytes.status})`);
  }
  const blob = await bytes.blob();
  const name = fileNameFrom(
    bytes.headers.get('content-disposition'),
    ticket.fileName || datasetId,
  );
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = name;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    URL.revokeObjectURL(url);
  }
}

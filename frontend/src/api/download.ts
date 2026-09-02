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
// 서버는 302 로 「바이트가 있는 자리」를 알려 주고 `fetch` 가 그 한 바퀴를 따라간다.
// 저장처가 볼륨이든 객체 저장소든 **화면은 그 차이를 모른다**(`kernel/file_store.py`).
import { api } from './client';

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
  const { data, response } = await api.GET('/datasets/{datasetId}/download', {
    params: { path: { datasetId } },
    parseAs: 'blob',
  });
  if (!response.ok || !data) {
    throw new Error(`다운로드가 열리지 않았어요 (${response.status})`);
  }
  const name = fileNameFrom(response.headers.get('content-disposition'), datasetId);
  const url = URL.createObjectURL(data as Blob);
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

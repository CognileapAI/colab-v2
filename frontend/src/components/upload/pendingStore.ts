// **등록을 안 끝낸 업로드**(상태 2)를 브라우저가 기억한다.
//
// 왜 필요한가 — 업로드는 두 걸음이다: ㉠ 바이트 올리기 ㉡ 설정 입력 후 「연구실에 등록하기」.
// ㉠ 이 끊긴 것(전송 원장)은 서버가 목록으로 돌려주지만, **㉡ 이 안 끝난 것은 목록 창구가
// 계약에 없다.** 그래서 새로고침하면 그 업로드에 **다시 도달할 방법이 아예 없었다** —
// 바이트는 S3 에 있고 원장도 살아 있는데 사람만 길을 잃었다.
//
// 어떻게 — 접수(`create`)가 성공한 순간의 `uploadId` 를 여기 적어 두고, 되찾을 때는
// **기존 `getUploadStatus` 한 건 조회**로 살아 있는지 묻는다. **새 op 을 만들지 않으므로
// 계약 동결을 건드리지 않는다.**
//
// ⚠ **한계는 하나 남았다.**
//  ⑴ **브라우저별이다.** 다른 기기·시크릿창에서는 못 되찾는다. 없애려면 목록 op 신설 = 계약 개정.
//  ⑵ ~~등록 여부를 알 수 없다~~ — **닫혔다**(2026-09-02). `getUploadStatus` 가 `registered` 를
//     내리므로, 등록 성공 시 이쪽에서 지우는 것에만 기대지 않는다. 그 사이 탭이 죽어도
//     다음 방문에서 서버가 말해 준다. 이 저장소는 이제 **되찾을 id 의 목록**이지 진실원이 아니다.
//
// 저장 위치는 `auth/store.ts` 와 같은 태도다 — 접근 자체가 던지는 환경(시크릿창 등)에서는
// **없는 것으로 본다**(fail-closed). 조용히 통과시키지 않는다.

const KEY = 'colab.upload.pending';

/** 연구실이 바뀌면 남의 연구실 것을 보여주지 않는다 — 키에 연구실을 넣는다. */
function keyOf(labId: string): string {
  return `${KEY}.${labId}`;
}

function read(labId: string): string[] {
  try {
    const raw = window.localStorage.getItem(keyOf(labId));
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((v): v is string => typeof v === 'string') : [];
  } catch {
    return [];
  }
}

function write(labId: string, ids: string[]): void {
  try {
    window.localStorage.setItem(keyOf(labId), JSON.stringify(ids));
  } catch {
    /* 저장이 안 되면 이 탭 안에서만 산다. 그 사실을 거짓말로 덮지 않는다. */
  }
}

/** 접수된 업로드를 기억한다. 이미 있으면 늘리지 않는다. */
export function rememberPending(labId: string, uploadId: string): void {
  const ids = read(labId);
  if (ids.includes(uploadId)) return;
  write(labId, [...ids, uploadId]);
}

/** 등록됐거나 버려졌거나 만료됐다 — 잊는다. */
export function forgetPending(labId: string, uploadId: string): void {
  const ids = read(labId);
  if (!ids.includes(uploadId)) return;
  write(labId, ids.filter((v) => v !== uploadId));
}

export function listPending(labId: string): string[] {
  return read(labId);
}

// 업로드 모달을 **바깥에서 여는** 자리.
//
// 모달의 주인은 GNB 의 `UploadEntry` 다(전역 내비라 모든 화면에 떠 있다). 메인 화면의
// 「올리다 만 것」 카드는 그 모달을 열어야 하는데, 모달을 하나 더 만들면 상태가 둘이 된다.
// 그래서 **함수 하나만 건넨다** — `components/detail/download.ts` 의 `DownloadContext` 와 같은 모양이다:
// 기본값이 동작하는 함수이고, 시험이 갈아 끼우며, 화면은 그 뒤를 모른다.
import { createContext, useContext } from 'react';

export interface OpenUploadRequest {
  /** 이 전송을 이어서 올린다. 없으면 빈 모달을 연다. */
  resumeUploadId?: string;
}

/**
 * 기본값은 **아무 일도 하지 않는다** — provider 밖에서 불릴 수 있고(시험·자리표시자),
 * 그때 조용히 아무 일도 안 하는 것이 모달을 하나 더 세우는 것보다 낫다.
 */
export const OpenUploadContext = createContext<(req?: OpenUploadRequest) => void>(() => {});

export function useOpenUpload(): (req?: OpenUploadRequest) => void {
  return useContext(OpenUploadContext);
}

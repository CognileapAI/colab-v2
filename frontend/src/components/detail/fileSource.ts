// 파일 관리 5 op 의 실서버 구현 (`PLAN-SoT §9 〈278〉`). 타입은 전부 생성물에서 온다.
//
// **픽스처 폴백을 두지 않는다.** 상세(`detailSource.ts`)는 읽기라 픽스처로 그려도 화면이
// 거짓말을 하지 않지만, 추가·교체·삭제는 **되돌릴 수 없는 것을 만드는 경로**고 다운로드 티켓은
// 발급 시점에 이력이 쌓인다. 실패는 실패로 보여야 한다 (`uploadSource.ts` 머리말과 같은 이유).
//
// 다운로드는 `<a href>` 가 아니다 — Bearer 는 fetch 미들웨어 한 자리(`api/client.ts`)에만 붙고
// 링크에는 실리지 않는다. 그래서 여기서 **티켓**을 받고, 바이트는 `download.ts` 가 티켓 URL 로 간다.
import { api } from '../../api/client';
import {
  FileGone,
  LastBodyFile,
  NotImplemented,
  type DatasetFile,
  type DownloadTicket,
  type FileSource,
} from './types';

/** 오류 봉투(`ErrorEnvelope.message`)의 문장. 없으면 `undefined` — 지어내지 않는다. */
function serverMessage(error: unknown): string | undefined {
  const m = (error as { message?: unknown } | undefined)?.message;
  return typeof m === 'string' && m.length > 0 ? m : undefined;
}

/** form-data 바디를 그대로 내보낸다 — 계약이 `multipart/form-data` 로 못 박았다 (`uploadSource.ts` 와 같은 모양). */
const asForm = (b: unknown) => b as FormData;

export function apiFileSource(): FileSource {
  return {
    async list(datasetId): Promise<DatasetFile[]> {
      const r = await api.GET('/datasets/{datasetId}/files', {
        params: { path: { datasetId } },
      });
      if (r.response.status === 404) throw new FileGone();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) {
        // 403 = 잠김 + 허용 목록 밖 (P-34). 서버 문장이 있으면 그대로 보여 준다.
        throw new Error(serverMessage(r.error) ?? '파일 목록을 불러오지 못했어요.'); // [정본 무근거 · 〈278〉]
      }
      return r.data.items ?? [];
    },

    async downloadTicket(datasetId, fileId): Promise<DownloadTicket> {
      const r = fileId
        ? await api.GET('/datasets/{datasetId}/files/{fileId}/download', {
            params: { path: { datasetId, fileId } },
          })
        : await api.GET('/datasets/{datasetId}/download', {
            params: { path: { datasetId } },
          });
      // 404 = 없거나 경계 밖 — 존재를 알리지 않는다 (P-9·P-10). 잠김(403)은 아래 일반 오류로
      if (r.response.status === 404) throw new FileGone();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error(serverMessage(r.error) ?? '다운로드를 시작하지 못했어요.'); // [정본 무근거 · 〈278〉]
      return r.data;
    },

    async add(datasetId, file, kind, relativePath): Promise<DatasetFile> {
      const form = new FormData();
      form.append('file', file, file.name);
      form.append('kind', kind);
      // 경로는 저장 키가 아니라 원장 메타다 — 있을 때만 싣는다 (`createUpload.relativePaths` 와 같은 정규화·상한)
      if (relativePath) form.append('relativePath', relativePath);
      const r = await api.POST('/datasets/{datasetId}/files', {
        params: { path: { datasetId } },
        body: form as unknown as never,
        bodySerializer: asForm,
      });
      if (r.response.status === 404) throw new FileGone();
      if (r.response.status === 501) throw new NotImplemented();
      // 400 = `kind` 가 격자다(→ `attachUploadGridFiles`) 또는 경로 정규화 실패 — 서버 문장 그대로
      if (!r.data) throw new Error(serverMessage(r.error) ?? '파일을 더하지 못했어요.'); // [정본 무근거 · 〈278〉]
      return r.data;
    },

    async replace(datasetId, fileId, file): Promise<DatasetFile> {
      const form = new FormData();
      form.append('file', file, file.name);
      const r = await api.PUT('/datasets/{datasetId}/files/{fileId}', {
        params: { path: { datasetId, fileId } },
        body: form as unknown as never,
        bodySerializer: asForm,
      });
      if (r.response.status === 404) throw new FileGone();
      if (r.response.status === 501) throw new NotImplemented();
      // 409 는 `flipAxes` 쪽 충돌뿐이다 — 파일 교체에는 없다. 그래도 오면 서버 문장을 그대로
      if (!r.data) throw new Error(serverMessage(r.error) ?? '파일을 교체하지 못했어요.'); // [정본 무근거 · 〈278〉]
      return r.data;
    },

    async remove(datasetId, fileId): Promise<void> {
      const r = await api.DELETE('/datasets/{datasetId}/files/{fileId}', {
        params: { path: { datasetId, fileId } },
      });
      if (r.response.status === 404) throw new FileGone();
      // 409 = 마지막 본체 파일 (본체 ≥ 1). **서버 문장을 그대로** 실어 보낸다
      if (r.response.status === 409) {
        throw new LastBodyFile(serverMessage(r.error) ?? '마지막 본체 파일은 지울 수 없어요.'); // [정본 무근거 · 〈278〉] 서버 문장이 없을 때만
      }
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.response.ok) throw new Error(serverMessage(r.error) ?? '파일을 지우지 못했어요.'); // [정본 무근거 · 〈278〉]
    },
  };
}

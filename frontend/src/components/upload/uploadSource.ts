// 업로드 수명주기 3 op 의 실서버 구현. 타입은 전부 생성물에서 온다.
//
// **픽스처 폴백을 두지 않는다.** 상세(`detailSource.ts`)는 읽기라 픽스처로 그려도 화면이
// 거짓말을 하지 않지만, 업로드는 **되돌릴 수 없는 것을 만드는 경로**다. 접수되지 않은 파일을
// 접수된 것처럼 그리면 사람이 등록을 누른다 — 실패는 실패로 보여야 한다 (`P2.md` 머리말).
import { api } from '../../api/client';
import { presignedCreate } from './transferSource';
import {
  GridAxisTaken,
  NoResolvedGrid,
  NotImplemented,
  UploadGone,
  type DatasetCreate,
  type PickedFile,
  type UploadCreateOptions,
  type UploadSource,
} from './types';

/** 서버가 한 번 501 을 냈으면(저장 모드 local) 매번 다시 두드리지 않는다. */
let transferUnavailable = false;

export function apiUploadSource(): UploadSource {
  return {
    async create(files: PickedFile[], opts?: UploadCreateOptions) {
      // ① 프리사인드 직행(〈338〉)을 먼저 — 브라우저가 S3 에 직접 놓고 재개가 성립한다.
      if (!transferUnavailable) {
        try {
          return await presignedCreate(files, opts ?? {});
        } catch (e) {
          if (!(e instanceof NotImplemented)) throw e;
          transferUnavailable = true;  // ② 501 = 로컬 저장 모드 — form-data 로 폴백
        }
      }
      // 계약이 `multipart/form-data` 로 못 박았고 `fileKinds`·`relativePaths` 는 `files` 와 **같은 순서**다.
      const form = new FormData();
      for (const f of files) form.append('files', f.file, f.file.name);
      for (const f of files) form.append('fileKinds', f.kind);
      // 폴더째 업로드의 경로(〈339〉-(나)) — 하나라도 있으면 **전부** 싣는다(같은 개수). 빈 문자열 =
      // 그 파일은 경로 없음(multipart 배열은 null 을 싣지 못한다). 아무 파일에도 없으면 생략 = 전부 낱개.
      if (files.some((f) => f.relativePath)) {
        for (const f of files) form.append('relativePaths', f.relativePath ?? '');
      }
      const r = await api.POST('/uploads', {
        body: form as unknown as never,
        bodySerializer: (b: unknown) => b as FormData,
      });
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('파일을 올리지 못했어요.');
      return r.data;
    },

    async incomplete() {
      if (transferUnavailable) return [];
      const r = await api.GET('/uploads/transfers/incomplete');
      if (r.response.status === 501) { transferUnavailable = true; return []; }
      return r.data?.items ?? [];
    },

    async abortTransfer(uploadId: string) {
      await api.DELETE('/uploads/transfers/{uploadId}', { params: { path: { uploadId } } });
    },

    async status(uploadId) {
      const r = await api.GET('/uploads/{uploadId}', { params: { path: { uploadId } } });
      // 404 = 없거나 **수명이 다한** 업로드 (`Policy §7.1`). 다른 오류와 섞지 않는다.
      if (r.response.status === 404) throw new UploadGone();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('업로드 상태를 읽지 못했어요.');
      return r.data;
    },

    async register(body: DatasetCreate) {
      const r = await api.POST('/datasets', { body });
      if (r.response.status === 404) throw new UploadGone();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('데이터셋을 만들지 못했어요.');
      return { datasetId: r.data.datasetId };
    },

    async attachGrid(datasetId: string, uploadId: string) {
      // **짝을 여기서 처음 잇는다** — 화면이 들고 있던 `uploadId` 를 `datasetId` 옆에 놓는다.
      const r = await api.POST('/datasets/{datasetId}/grid-files', {
        params: { path: { datasetId } },
        body: { uploadId },
      });
      // 404 = 없거나 **수명이 다한** 업로드, 또는 경계 밖 데이터셋. 같은 문장으로 답한다.
      if (r.response.status === 404) throw new UploadGone();
      // 409 = 이미 그 축을 쓰는 격자가 있다 (`〈58〉`) 또는 이미 소비된 업로드다.
      if (r.response.status === 409) throw new GridAxisTaken();
      // 400 = 축이 확정된 격자가 없다 — 판별 실패·형상 불일치는 원장에 행을 안 남긴다.
      if (r.response.status === 400) throw new NoResolvedGrid();
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('격자를 반영하지 못했어요.');
      return r.data.items;
    },
  };
}

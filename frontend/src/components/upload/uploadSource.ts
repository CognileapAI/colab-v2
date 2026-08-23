// 업로드 수명주기 3 op 의 실서버 구현. 타입은 전부 생성물에서 온다.
//
// **픽스처 폴백을 두지 않는다.** 상세(`detailSource.ts`)는 읽기라 픽스처로 그려도 화면이
// 거짓말을 하지 않지만, 업로드는 **되돌릴 수 없는 것을 만드는 경로**다. 접수되지 않은 파일을
// 접수된 것처럼 그리면 사람이 등록을 누른다 — 실패는 실패로 보여야 한다 (`P2.md` 머리말).
import { api } from '../../api/client';
import { NotImplemented, UploadGone, type DatasetCreate, type PickedFile, type UploadSource } from './types';

export function apiUploadSource(): UploadSource {
  return {
    async create(files: PickedFile[]) {
      // 계약이 `multipart/form-data` 로 못 박았고 `fileKinds` 는 `files` 와 **같은 순서**다.
      const form = new FormData();
      for (const f of files) form.append('files', f.file, f.file.name);
      for (const f of files) form.append('fileKinds', f.kind);
      const r = await api.POST('/uploads', {
        body: form as unknown as never,
        bodySerializer: (b: unknown) => b as FormData,
      });
      if (r.response.status === 501) throw new NotImplemented();
      if (!r.data) throw new Error('파일을 올리지 못했어요.');
      return r.data;
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
  };
}

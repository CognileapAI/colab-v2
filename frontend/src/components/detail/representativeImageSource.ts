import { api } from '../../api/client';
import type { Schemas } from '../../api/client';

export type RepresentativeImageMetadata = Schemas['RepresentativeImageMetadata'];

export interface RepresentativeImageSource {
  get(datasetId: string): Promise<Blob>;
  put(datasetId: string, file: File): Promise<RepresentativeImageMetadata>;
  remove(datasetId: string): Promise<void>;
}

function messageOf(error: unknown, fallback: string): string {
  const message = (error as { message?: unknown } | undefined)?.message;
  return typeof message === 'string' && message ? message : fallback;
}

export function apiRepresentativeImageSource(): RepresentativeImageSource {
  return {
    async get(datasetId) {
      const r = await api.GET('/datasets/{datasetId}/representative-image', {
        params: { path: { datasetId } },
        parseAs: 'blob',
      });
      if (!r.data) throw new Error(messageOf(r.error, '대표 그림을 불러오지 못했어요.'));
      return r.data as unknown as Blob;
    },
    async put(datasetId, file) {
      const form = new FormData();
      form.append('image', file, file.name);
      const r = await api.PUT('/datasets/{datasetId}/representative-image', {
        params: { path: { datasetId } },
        body: form as unknown as never,
        bodySerializer: (body: unknown) => body as FormData,
      });
      if (!r.data) throw new Error(messageOf(r.error, '대표 그림을 저장하지 못했어요.'));
      return r.data;
    },
    async remove(datasetId) {
      const r = await api.DELETE('/datasets/{datasetId}/representative-image', {
        params: { path: { datasetId } },
      });
      if (!r.response.ok) throw new Error(messageOf(r.error, '대표 그림을 지우지 못했어요.'));
    },
  };
}

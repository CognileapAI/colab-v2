import type { components } from '../../generated/fe-core';
import { api } from '../../api/client';

type Schemas = components['schemas'];

export type SearchEvidenceFacts = Schemas['SearchEvidenceFacts'];
export type SearchEvidenceRecord = Schemas['SearchEvidence'];
export type SearchEvidenceItem = Schemas['SearchEvidenceItem'];
export type SearchEvidenceList = Schemas['SearchEvidenceList'];
export type SearchEvidenceWrite = Schemas['SearchEvidenceWrite'];

export class SearchEvidenceRequestError extends Error {
  constructor(public readonly status: number) {
    super(status === 409 ? '다른 변경이 먼저 저장되었습니다.' : '검색 근거를 처리하지 못했습니다.');
  }
}

export interface SearchEvidenceSource {
  list(datasetId: string): Promise<SearchEvidenceList>;
  save(datasetId: string, fileId: string, payload: SearchEvidenceWrite): Promise<SearchEvidenceRecord>;
}

export const defaultSearchEvidenceSource: SearchEvidenceSource = {
  async list(datasetId) {
    const { data, response } = await api.GET('/datasets/{datasetId}/search-evidence', {
      params: { path: { datasetId } },
    });
    if (!data) throw new SearchEvidenceRequestError(response.status);
    return data;
  },
  async save(datasetId, fileId, payload) {
    const { data, response } = await api.PUT('/datasets/{datasetId}/files/{fileId}/search-evidence', {
      params: { path: { datasetId, fileId } },
      body: payload,
    });
    if (!data) throw new SearchEvidenceRequestError(response.status);
    return data;
  },
};

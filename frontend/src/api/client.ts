// core-api seam 클라이언트. 타입은 전부 생성물에서 온다 — 여기서 다시 선언하지 않는다.
// 근거: frontend/README.md(생성된 타입·클라이언트만 쓴다) · CLAUDE.md §3-7
import createClient from 'openapi-fetch';
import type { paths, components } from '../generated/fe-core';

// seam 의 servers[0].url. 계약이 정한 값이라 화면이 고르지 않는다.
export const API_BASE_URL = '/api/v1';

export const api = createClient<paths>({ baseUrl: API_BASE_URL });

export type Schemas = components['schemas'];
export type CurrentAccount = Schemas['CurrentAccount'];
export type PermissionSwitch = Schemas['PermissionSwitch'];
export type PermissionSwitchSet = Schemas['PermissionSwitchSet'];

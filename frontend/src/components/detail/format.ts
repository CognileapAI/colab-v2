// 기본 정보 칸의 표시 규칙. 값이 없으면 지어내지 않고 비운 표시를 쓴다.
import type { DatasetBasicInfo } from './types';

/** 정본이 값을 주지 않은 칸. 빈 칸을 지우면 아홉 칸 격자가 깨지고 「없다」는 사실도 사라진다. */
export const EMPTY = '—';

/**
 * 기간 = 데이터가 다루는 시간 범위 (`§4` 용어). 목업 표기는 `2025-06 ~ 09` 다 —
 * 해가 같으면 뒤쪽 해를 다시 적지 않는다.
 *
 * **끝이 없으면 무기한이다** (`DataPeriod.end`: `[string, "null"]` · 14차 해제).
 * 빈 칸으로 두면 「기간을 모른다」와 「아직 안 끝났다」가 화면에서 갈리지 않는다.
 * ⚠ **`[미확인]`** — 화면 정본은 열린 기간의 문면을 정하지 않았다. `~ 진행 중` 은
 * 레포 안에서 고른 값이고, 스펙 문면이 정해지면 그것이 이긴다.
 */
export function formatPeriod(p: DatasetBasicInfo['period']): string {
  if (!p) return EMPTY;
  const s = p.start.slice(0, 7);
  if (!p.end) return `${s} ~ 진행 중`;
  const e = p.end.slice(0, 7);
  return s.slice(0, 4) === e.slice(0, 4) ? `${s} ~ ${e.slice(5, 7)}` : `${s} ~ ${e}`;
}

/** 단위 표기 — 목업이 쓰는 단위는 `MB` 다(`37 MB` · `148 MB`). */
function withUnit(bytes: number): string {
  const K = 1024;
  if (bytes >= K ** 3) return `${(bytes / K ** 3).toFixed(1)} GB`;
  if (bytes >= K ** 2) return `${Math.round(bytes / K ** 2)} MB`;
  if (bytes >= K) return `${Math.round(bytes / K)} KB`;
  return `${bytes} B`;
}

/** 용량 표기. 합계 자리 전용 — 0 은 「픽스처가 용량을 모르는 자리」라 `—` 다. */
export function formatBytes(bytes: number): string {
  if (bytes <= 0) return EMPTY; // 픽스처가 용량을 모르는 자리 — 0 B 라고 말하지 않는다
  return withUnit(bytes);
}

/**
 * 조각 **하나**의 크기. `null` = 모름 — `d3_file.size_bytes` 가 NULL 일 수 있고 그것은 0 과 다르다
 * (`〈339〉-(가)` 「모르는 값을 0 으로 적지 않는다」). `formatBytes` 의 「0 → `—`」 규칙과 **갈라 둔다**:
 * 여기서 0 은 진짜 0 B 다.
 */
export function formatFileSize(bytes: number | null): string {
  if (bytes === null) return '모름'; // [정본 무근거 · 〈339〉]
  return withUnit(bytes);
}

/**
 * `파일` 칸은 **조각 수와 용량 합계만** 말한다 (`§5`).
 * 파일이 한 건이면 파일명과 용량을 그대로 쓴다. 조각을 이 자리에 나열하지 않는다.
 */
export function formatFiles(files: DatasetBasicInfo['files'], fileName: string | null): string {
  const size = formatBytes(files.totalSizeBytes);
  if (files.count === 1) return fileName ? `${fileName} · ${size}` : size;
  return `조각 ${files.count}개 · 합계 ${size}`;
}

export function orEmpty(v: string | null | undefined): string {
  return v && v.length > 0 ? v : EMPTY;
}

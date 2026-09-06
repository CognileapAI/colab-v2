// WU-A5 · PRD-21 — **확장자는 확장자로만 적는다.**
//
// 화면이 보이는 것은 판별 결과 문자열이 아니라 조각의 확장자이고, 표기는 `*.nc` 다.
// `.hdf` 하나가 서로 호환되지 않는 두 포맷을 가리키므로(`P-10` · `R-09`) 화면이
// `HDF4`·`HDF5` 를 단정하면 그 자리에서 거짓말이 된다.
//
// 조립은 **한 곳**에서만 한다 (`detail/format.ts` `formatExtension`) — 같은 값의 표기가
// 두 화면에서 갈리는 자리를 만들지 않는다.
import { useState } from 'react';
import { render, screen, within, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';

import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { FIXTURE_DETAILS, fixtureDetailSource } from '../src/components/detail/fixture';
import { formatExtension } from '../src/components/detail/format';
import {
  FileDropCard,
  PREVIEWABLE_EXTENSIONS_NOTICE,
  UPLOAD_ANY_FORMAT_NOTICE,
  previewabilityNotice,
} from '../src/components/upload/FileDropCard';
import type { DatasetDetail, DetailSource } from '../src/components/detail/types';
import type { FileKind, PickedFile } from '../src/components/upload/types';

const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1'; // 낙동강 유역 강우 (2025) — 조각 `*.nc`

function sourceOf(detail: DatasetDetail): DetailSource {
  return { get: () => Promise.resolve(detail) };
}

function renderDetail(source: DetailSource = fixtureDetailSource()) {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route path="/datasets/:datasetId" element={<DatasetDetailPage source={source} />} />
      </Routes>
    </MemoryRouter>,
  );
}

function withBasicInfo(patch: Record<string, unknown>): DatasetDetail {
  const base = FIXTURE_DETAILS[OPEN_ID] as DatasetDetail;
  return { ...base, basicInfo: { ...base.basicInfo!, ...patch } } as DatasetDetail;
}

describe('PRD-21 — 조립 규칙은 한 곳에 있다', () => {
  it('확장자가 있으면 `*.nc` 다', () => {
    expect(formatExtension('nc', 'NetCDF-4')).toBe('*.nc');
  });

  it('`.hdf` 는 `*.hdf` 다 — HDF4/HDF5 를 단정하지 않는다', () => {
    expect(formatExtension('hdf', 'HDF5')).toBe('*.hdf');
  });

  it('확장자가 없으면 판별값으로 **퇴행**한다 (지어내지 않는다)', () => {
    expect(formatExtension(null, 'NetCDF-4')).toBe('NetCDF-4');
  });

  it('둘 다 없으면 빈 표시다 — 화면이 안 깨진다', () => {
    expect(formatExtension(null, null)).toBe('—');
  });
});

describe('PRD-21 — 상세 기본 정보', () => {
  it('포맷 자리에 `*.nc` 가 보이고 판별 문자열이 안 보인다', async () => {
    renderDetail(sourceOf(withBasicInfo({ fileExtension: 'nc', format: 'NetCDF-4' })));
    const cell = await screen.findByTestId('ig-포맷');
    expect(within(cell).getByText('*.nc')).toBeTruthy();
    expect(cell.textContent).not.toContain('NetCDF-4');
  });

  it('`.hdf` 는 `*.hdf` 다', async () => {
    renderDetail(sourceOf(withBasicInfo({ fileExtension: 'hdf', format: 'HDF5' })));
    const cell = await screen.findByTestId('ig-포맷');
    expect(cell.textContent).toContain('*.hdf');
    expect(cell.textContent).not.toContain('HDF5');
  });

  it('확장자가 없는 기존 행은 판별값으로 떨어지고 화면이 안 깨진다', async () => {
    renderDetail(sourceOf(withBasicInfo({ fileExtension: null, format: 'nc' })));
    const cell = await screen.findByTestId('ig-포맷');
    expect(cell.textContent).toContain('nc');
    expect(screen.getByTestId('basic-info')).toBeTruthy();
  });
});

/** 실제 모달과 같은 결선 — 놓으면 `picked` 에 쌓인다 (`UploadModal.pick`). */
function Harness() {
  const [picked, setPicked] = useState<PickedFile[]>([]);
  return (
    <FileDropCard
      picked={picked}
      onPick={(files) =>
        setPicked((cur) => [...cur, ...files.map((file) => ({ file, kind: '본체' as FileKind }))])
      }
      onKind={() => {}}
    />
  );
}

function drop(names: string[]) {
  const input = screen.getByTestId('up-drop-input') as HTMLInputElement;
  fireEvent.change(input, {
    target: { files: names.map((n) => new File([new Uint8Array(8)], n)) },
  });
}

describe('PRD-21 — 업로드 안내는 업로드 가능 / 미리보기 가능 둘로 갈린다', () => {
  it('진입 안내 축자가 놓기 전에 이미 보인다', () => {
    render(<Harness />);
    expect(screen.getByTestId('up-any-format')).toHaveTextContent(
      '어떤 포맷이든 올려요 · 같은 확장자면 여러 개를 한 데이터셋으로 묶어요',
    );
    expect(UPLOAD_ANY_FORMAT_NOTICE).toBe(
      '어떤 포맷이든 올려요 · 같은 확장자면 여러 개를 한 데이터셋으로 묶어요',
    );
  });

  it('미리보기 되는 확장자를 놓으면 되는 목록을 말한다', () => {
    render(<Harness />);
    drop(['a.nc']);
    expect(screen.getByTestId('up-previewable')).toHaveTextContent(
      '지도 미리보기까지 되는 확장자: *.nc *.tif *.hdf *.bin',
    );
    expect(PREVIEWABLE_EXTENSIONS_NOTICE).toBe(
      '지도 미리보기까지 되는 확장자: *.nc *.tif *.hdf *.bin',
    );
  });

  it('그 밖의 확장자는 못 그린다고 말한다 — 업로드를 막지는 않는다', () => {
    render(<Harness />);
    drop(['a.csv']);
    expect(screen.getByTestId('up-previewable')).toHaveTextContent('이 확장자는 지도로 못 그려요');
    expect(screen.getByTestId('up-files')).toBeTruthy();
  });

  it('안내 판정은 순수 함수 하나다', () => {
    expect(previewabilityNotice('nc')).toBe(PREVIEWABLE_EXTENSIONS_NOTICE);
    expect(previewabilityNotice('bin')).toBe(PREVIEWABLE_EXTENSIONS_NOTICE);
    expect(previewabilityNotice('csv')).toBe('이 확장자는 지도로 못 그려요');
    expect(previewabilityNotice('')).toBe('이 확장자는 지도로 못 그려요');
  });
});

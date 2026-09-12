/**
 * WU-A10 · 썸네일 넛지 (PRD-20 · `R-A-3-frontend.md §2`).
 *
 * 수용 기준 두 줄이 오라클이다.
 *  · ② 단계 진입 → 썸네일과 **교체 안내 문구가 읽힌다**
 *  · 썸네일 클릭 → **파일 선택기가 열린다**
 *
 * 대표 그림 저장 계약이 열린 뒤에도 이 시험은 파일 선택 진입과 로컬 미리보기 수명을 잰다.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PreviewPanel } from '../src/components/upload/PreviewPanel';
import type { PreviewSource } from '../src/components/upload/types';

const UPLOAD_ID = '01JYZ9K7WQ3N8V4M2X6C5B0UP1';

/** 넛지 문면 — 정본 문구다. 여기서 새로 짓지 않는다. */
const NUDGE = '눌러서 다른 그림으로 바꿀 수 있어요';

function source(): PreviewSource {
  return {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      throw new Error('이 시험은 그리지 않는다');
    },
    async getRender() {
      throw new Error('이 시험은 그리지 않는다');
    },
  } as unknown as PreviewSource;
}

async function mount(props: { file?: File | null; onFile?: (file: File | null) => void } = {}) {
  const view = render(
    <PreviewPanel
      source={source()}
      uploadId={UPLOAD_ID}
      hasReferenceGrid={false}
      representativeFile={props.file ?? null}
      onRepresentativeFileChange={props.onFile}
    />,
  );
  await screen.findByTestId('up-preview-draw');
  return view;
}

describe('WU-A10 대표 그림(썸네일) 넛지', () => {
  it('② 단계에 들어오면 썸네일 자리와 교체 안내가 함께 읽힌다', async () => {
    await mount();
    expect(await screen.findByTestId('up-thumb-block')).toBeTruthy();
    expect(screen.getByTestId('up-thumb-pick')).toBeTruthy();
    expect(screen.getByTestId('up-thumb-nudge').textContent).toContain(NUDGE);
  });

  it('썸네일을 누르면 파일 선택기가 열린다', async () => {
    await mount();
    const input = screen.getByTestId('up-thumb-input') as HTMLInputElement;
    expect(input.type).toBe('file');
    expect(input.accept).toBe('image/png,image/jpeg,image/webp');
    const click = vi.spyOn(input, 'click');

    fireEvent.click(screen.getByTestId('up-thumb-pick'));

    expect(click).toHaveBeenCalledTimes(1);
  });

  it('고른 실제 File을 바깥으로 올리고 그 File의 미리보기 주소를 교체·해제한다', async () => {
    const create = vi.fn((file: File) => `blob:local/${file.name}`);
    const revoke = vi.fn();
    vi.stubGlobal('URL', { ...URL, createObjectURL: create, revokeObjectURL: revoke });
    const onFile = vi.fn();
    const view = await mount({ onFile });
    const input = screen.getByTestId('up-thumb-input') as HTMLInputElement;

    const file = new File([new Uint8Array([1, 2, 3])], 'cover.png', { type: 'image/png' });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFile).toHaveBeenCalledWith(file);

    view.rerender(
      <PreviewPanel
        source={source()}
        uploadId={UPLOAD_ID}
        hasReferenceGrid={false}
        representativeFile={file}
        onRepresentativeFileChange={onFile}
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId('up-thumb-img').getAttribute('src')).toBe('blob:local/cover.png'),
    );
    expect(create).toHaveBeenCalledWith(file);

    fireEvent.click(screen.getByRole('button', { name: '자동 그림 사용' }));
    expect(onFile).toHaveBeenLastCalledWith(null);
    view.unmount();
    expect(revoke).toHaveBeenCalledWith('blob:local/cover.png');
    vi.unstubAllGlobals();
  });
});

/**
 * ⭑ ⟨R-BUGFIX-260912 L3b · spec v2 §6 ㉱ · Ted 승인 「모두 권고대로」⟩ 축소본 중복 방지.
 *
 * `#26` 이 자동 축소본을 지도 자리에서 접히는 설정 블록으로 옮겼다. 그 자리에는
 * 대표 그림 고르개(`up-thumb-img`)가 이미 서 있고, **고른 그림이 없으면 그 고르개가
 * `autoThumb` 를 그대로 싣는다**(`const thumbSrc = pickedThumb ?? autoThumb`).
 * 그래서 자동 축소본을 무조건 옆에 두면 같은 주소의 그림이 두 장 선다.
 *
 * 규칙 = **고른 그림이 있을 때만** 자동 축소본을 옆에 대조용으로 세운다
 * (사용자 스토리 3 — 「자동으로 잡힌 그림」과 「내가 고른 그림」이 한 자리에서 갈린다).
 */
const AUTO_THUMB = 'https://viz.example/p/thumb.png';

function drawnSource(): PreviewSource {
  const job = {
    renderId: '01JYZ9K7WQ3N8V4M2X6C5B0RE1',
    status: '완료',
    result: {
      imageUrl: 'https://viz.example/p/map.png',
      thumbnailUrl: AUTO_THUMB,
      legend: { palette: 'viridis', classes: [{ color: '#440154', min: 0, max: 5 }] },
    },
  };
  return {
    async palettes() {
      return [{ palette: 'viridis', label: '비리디스' }];
    },
    async createRender() {
      return job as never;
    },
    async getRender() {
      return job as never;
    },
  } as unknown as PreviewSource;
}

/** 그리기까지 밟아 자동 축소본이 실린 완료 화면을 세운다. */
async function drawn(file: File | null) {
  render(
    <PreviewPanel
      source={drawnSource()}
      uploadId={UPLOAD_ID}
      hasReferenceGrid
      representativeFile={file}
    />,
  );
  fireEvent.click(await screen.findByTestId('up-preview-draw'));
  await waitFor(() => expect(screen.getByTestId('up-preview-image')).toBeTruthy(), {
    timeout: 5000,
  });
}

describe('㈄ 축소본 — 접히는 설정 자리 ＋ 중복 방지 규칙', () => {
  it('17 고른 그림이 없으면 대표 그림 블록 안 그림은 한 장뿐이다 (대조군)', async () => {
    await drawn(null);
    const bl = screen.getByTestId('up-thumb-block');
    expect(bl.querySelectorAll('img').length).toBe(1);
    expect(screen.getByTestId('up-thumb-img').getAttribute('src')).toBe(AUTO_THUMB);
  });

  it('고른 그림이 있으면 자동 축소본이 그 옆에 대조용으로 선다', async () => {
    vi.stubGlobal('URL', {
      ...URL,
      createObjectURL: () => 'blob:local/cover.png',
      revokeObjectURL: () => undefined,
    });
    const file = new File([new Uint8Array([1])], 'cover.png', { type: 'image/png' });
    await drawn(file);
    const bl = screen.getByTestId('up-thumb-block');
    expect(bl.querySelectorAll('img').length).toBe(2);
    expect(screen.getByTestId('up-thumb-img').getAttribute('src')).toBe('blob:local/cover.png');
    const auto = screen.getByTestId('up-preview-thumb');
    expect(bl.contains(auto)).toBe(true);
    expect(auto.getAttribute('src')).toBe(AUTO_THUMB);
    vi.unstubAllGlobals();
  });
});

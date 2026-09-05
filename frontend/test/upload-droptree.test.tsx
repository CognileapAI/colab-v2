/**
 * 오라클 — 폴더 드래그 앤 드롭 (`dropTree.ts` + `FileDropCard` 드롭 핸들러 · `〈337〉`).
 *
 * 기존 시험의 파일 투입구(`up-drop-input` change)는 건드리지 않았다 — 여기는
 * **드롭 경로만** 본다: 폴더 재귀 펼치기 · 숨김 파일 제외 · 상대 경로 동반 ·
 * entry API 부재 시 `dt.files` 폴백.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { collectDrop } from '../src/components/upload/dropTree';
import { FileDropCard } from '../src/components/upload/FileDropCard';

function fakeFileEntry(name: string): FileSystemEntry {
  return {
    isFile: true,
    isDirectory: false,
    name,
    file: (ok: (f: File) => void) => ok(new File(['x'], name)),
  } as unknown as FileSystemEntry;
}

/** readEntries 를 100개 단위 배치처럼 — 첫 호출에 자식, 다음 호출에 빈 배치. */
function fakeDirEntry(name: string, children: FileSystemEntry[]): FileSystemEntry {
  return {
    isFile: false,
    isDirectory: true,
    name,
    createReader: () => {
      let served = false;
      return {
        readEntries: (ok: (batch: FileSystemEntry[]) => void) => {
          if (served) return ok([]);
          served = true;
          ok(children);
        },
      };
    },
  } as unknown as FileSystemEntry;
}

function dtWithEntries(entries: FileSystemEntry[]): DataTransfer {
  return {
    items: entries.map((entry) => ({ webkitGetAsEntry: () => entry })),
    files: [],
  } as unknown as DataTransfer;
}

describe('collectDrop', () => {
  it('폴더를 재귀로 펼치고 상대 경로를 붙인다 — 숨김 파일은 걸러낸다', async () => {
    const dir = fakeDirEntry('기상', [
      fakeFileEntry('서울.nc'),
      fakeFileEntry('.DS_Store'),
      fakeDirEntry('2025', [fakeFileEntry('부산.nc')]),
    ]);
    const out = await collectDrop(dtWithEntries([dir]));
    expect(out.map((d) => d.relativePath)).toEqual(['기상/서울.nc', '기상/2025/부산.nc']);
  });

  it('낱개 파일 드롭에는 상대 경로가 없다', async () => {
    const out = await collectDrop(dtWithEntries([fakeFileEntry('단독.nc')]));
    expect(out).toHaveLength(1);
    expect(out[0]?.relativePath).toBeUndefined();
  });

  it('entry API 가 없으면 dt.files 로 폴백한다', async () => {
    const dt = { items: [], files: [new File(['x'], 'a.nc')] } as unknown as DataTransfer;
    const out = await collectDrop(dt);
    expect(out.map((d) => d.file.name)).toEqual(['a.nc']);
  });
});

describe('FileDropCard 드롭', () => {
  it('드롭존에 폴더를 떨어뜨리면 onPick 이 파일 목록과 경로 지도를 받는다', async () => {
    const onPick = vi.fn();
    render(<FileDropCard picked={[]} onPick={onPick} onKind={() => {}} />);
    const dir = fakeDirEntry('관측', [fakeFileEntry('LAT.npy')]);
    fireEvent.drop(screen.getByTestId('up-drop'), { dataTransfer: dtWithEntries([dir]) });
    await waitFor(() => expect(onPick).toHaveBeenCalledTimes(1));
    const [files, paths] = onPick.mock.calls[0] as [File[], ReadonlyMap<File, string>];
    expect(files.map((f) => f.name)).toEqual(['LAT.npy']);
    expect(paths.get(files[0]!)).toBe('관측/LAT.npy');
  });

  it('목록은 상대 경로가 있으면 그것을 이름으로 보인다', () => {
    const file = new File(['x'], '서울.nc');
    render(
      <FileDropCard
        picked={[{ file, kind: '본체', relativePath: '기상/서울.nc' }]}
        onPick={() => {}}
        onKind={() => {}}
      />,
    );
    expect(screen.getByText('기상/서울.nc')).toBeInTheDocument();
  });
});

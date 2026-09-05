/**
 * `buildTree` — 파일 목록을 폴더 트리로 다시 그리는 순수 함수 (`PLAN-SoT §9 〈339〉-(나)`).
 * 저장 키는 평평하고, 트리는 `relativePath` 로만 세운다. 경로 없는 파일은 루트,
 * `기준 격자 파일` 은 본체 트리와 **따로** 선다 (업로드 모달의 `up-companion` 과 같은 구분).
 */
import { describe, expect, it } from 'vitest';
import { buildTree, type FileTreeNode } from '../src/components/detail/fileTree';
import type { DatasetFile } from '../src/components/detail/types';

let seq = 0;
function file(
  fileName: string,
  over: Partial<DatasetFile> = {},
): DatasetFile {
  seq += 1;
  return {
    fileId: `01JYZ9K7WQ3N8V4M2X6C5B0${String(seq).padStart(3, '0')}`,
    fileName,
    kind: '본체',
    byteSize: 1024,
    createdAt: '2026-08-29T00:00:00Z',
    ...over,
  };
}

/** 트리를 `이름` · `폴더/`+자식 의 짧은 표기로 편다 — 단언이 구조를 그대로 읽게. */
function flat(nodes: FileTreeNode[]): unknown[] {
  return nodes.map((n) =>
    n.kind === 'folder' ? { [n.name + '/']: flat(n.children) } : n.name,
  );
}

describe('buildTree — 중첩 폴더', () => {
  it('`relativePath` 를 `/` 로 갈라 폴더 노드를 만들고, 마지막 조각이 파일이다', () => {
    const t = buildTree([
      file('x.nc', { relativePath: 'a/b/x.nc' }),
      file('y.nc', { relativePath: 'a/y.nc' }),
    ]);
    expect(flat(t.body)).toEqual([{ 'a/': [{ 'b/': ['x.nc'] }, 'y.nc'] }]);
  });

  it('폴더 노드는 루트부터의 경로를 갖는다', () => {
    const t = buildTree([file('x.nc', { relativePath: 'a/b/x.nc' })]);
    const a = t.body[0];
    expect(a?.kind).toBe('folder');
    if (a?.kind !== 'folder') return;
    expect(a.path).toBe('a');
    const b = a.children[0];
    expect(b?.kind === 'folder' && b.path).toBe('a/b');
  });

  it('빈 조각(앞뒤 `/`·이중 `/`)은 폴더가 되지 않는다', () => {
    const t = buildTree([file('x.nc', { relativePath: '/a//x.nc/' })]);
    expect(flat(t.body)).toEqual([{ 'a/': ['x.nc'] }]);
  });
});

describe('buildTree — 루트와 격자', () => {
  it('경로 없는 파일은 루트에 놓인다', () => {
    const t = buildTree([file('z.nc'), file('x.nc', { relativePath: 'a/x.nc' })]);
    expect(flat(t.body)).toEqual([{ 'a/': ['x.nc'] }, 'z.nc']);
  });

  it('`기준 격자 파일` 은 본체 트리에 섞이지 않고 따로 모인다', () => {
    const lat = file('lat.npy', { kind: '기준 격자 파일', relativePath: 'grid/lat.npy' });
    const t = buildTree([file('z.nc'), lat]);
    expect(flat(t.body)).toEqual(['z.nc']);
    expect(t.grid.map((f) => f.fileName)).toEqual(['lat.npy']);
  });

  it('격자가 없으면 빈 배열이다 — 지어낸 항목이 없다', () => {
    expect(buildTree([file('z.nc')]).grid).toEqual([]);
  });
});

describe('buildTree — 정렬', () => {
  it('폴더가 먼저, 그 다음 파일 — 각각 이름순', () => {
    const t = buildTree([
      file('b.nc'),
      file('a.nc'),
      file('q.nc', { relativePath: 'z/q.nc' }),
      file('p.nc', { relativePath: 'c/p.nc' }),
    ]);
    expect(flat(t.body)).toEqual([{ 'c/': ['p.nc'] }, { 'z/': ['q.nc'] }, 'a.nc', 'b.nc']);
  });

  it('격자 묶음도 이름순이다', () => {
    const t = buildTree([
      file('lon.npy', { kind: '기준 격자 파일' }),
      file('lat.npy', { kind: '기준 격자 파일' }),
    ]);
    expect(t.grid.map((f) => f.fileName)).toEqual(['lat.npy', 'lon.npy']);
  });

  it('입력 배열을 바꾸지 않는다', () => {
    const input = [file('b.nc'), file('a.nc')];
    const names = input.map((f) => f.fileName);
    buildTree(input);
    expect(input.map((f) => f.fileName)).toEqual(names);
  });
});

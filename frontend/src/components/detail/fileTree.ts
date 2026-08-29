// 파일 목록 → 폴더 트리. **순수 함수**다 — 저장 키는 평평하고(`〈173〉` 키 규약 불변), 트리는
// 원장 메타 `relativePath` 로만 다시 그린다 (`PLAN-SoT §9 〈175〉-(나)`).
//
// · 경로는 `/` 로 가른다. 마지막 조각이 파일이고 나머지가 폴더다. 빈 조각(앞뒤·이중 `/`)은 폴더가 아니다
// · 경로 없는 파일은 루트에 놓인다
// · `기준 격자 파일` 은 본체 트리에 섞이지 않고 따로 모인다 — 업로드 모달의 `up-companion` 과 같은 구분
// · 정렬 = 폴더 먼저 · 이름순
import type { DatasetFile } from './types';

export type FileTreeNode =
  | { kind: 'folder'; name: string; /** 루트부터의 경로 (`a/b`). */ path: string; children: FileTreeNode[] }
  | { kind: 'file'; name: string; file: DatasetFile };

export interface FileTree {
  /** 본체 조각들 — 폴더 트리. */
  body: FileTreeNode[];
  /** 기준 격자 파일 — 평평한 목록(0~2 건 · `〈58〉`). 없으면 빈 배열이고, 화면이 「없음」을 적는다. */
  grid: DatasetFile[];
}

type Folder = Extract<FileTreeNode, { kind: 'folder' }>;

function byName(a: { name: string }, b: { name: string }): number {
  return a.name.localeCompare(b.name);
}

function sortNodes(nodes: FileTreeNode[]): FileTreeNode[] {
  const folders = nodes.filter((n): n is Folder => n.kind === 'folder').sort(byName);
  const files = nodes.filter((n) => n.kind === 'file').sort(byName);
  for (const f of folders) f.children = sortNodes(f.children);
  return [...folders, ...files];
}

/** `relativePath` 의 폴더 조각들 — 마지막 조각(파일 이름)은 뺀다. 빈 조각은 버린다. */
function folderSegments(relativePath: string | undefined): string[] {
  if (!relativePath) return [];
  const parts = relativePath.split('/').filter((s) => s.length > 0);
  return parts.slice(0, -1);
}

export function buildTree(files: readonly DatasetFile[]): FileTree {
  const root: FileTreeNode[] = [];
  const grid: DatasetFile[] = [];

  for (const file of files) {
    if (file.kind === '기준 격자 파일') {
      grid.push(file);
      continue;
    }
    let level = root;
    let path = '';
    for (const seg of folderSegments(file.relativePath)) {
      path = path ? `${path}/${seg}` : seg;
      let folder = level.find((n): n is Folder => n.kind === 'folder' && n.name === seg);
      if (!folder) {
        folder = { kind: 'folder', name: seg, path, children: [] };
        level.push(folder);
      }
      level = folder.children;
    }
    level.push({ kind: 'file', name: file.fileName, file });
  }

  return { body: sortNodes(root), grid: [...grid].sort((a, b) => a.fileName.localeCompare(b.fileName)) };
}

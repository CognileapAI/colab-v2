// 폴더 드래그 앤 드롭 펼치기 — 드롭존의 유일한 폴더 해석기 (`PLAN-SoT §9 〈337〉`).
//
// 정본은 「파일을 끌어다 놓는다 → 업로드한다」(`Policy §2` 규칙 맵)까지만 말한다.
// 연구 자료는 폴더째 움직이는 일이 잦아, 폴더가 떨어지면 **하위를 재귀로 펼쳐**
// 파일 목록으로 만들고 상대 경로를 곁들인다. 숨김 파일(.DS_Store 류)은 걸러낸다.
//
// ⚠ `readEntries` 는 100개씩 끊어 준다 — 빈 배치가 올 때까지 반복해야 전부다.
//    (Chromium 실측 — 한 번만 읽으면 큰 폴더가 조용히 잘린다.)

/** 드롭에서 나온 파일 한 건. 폴더에서 왔으면 `relativePath` 가 `폴더/이름` 꼴이다. */
export interface DroppedFile {
  file: File;
  relativePath?: string;
}

async function flattenEntry(entry: FileSystemEntry, prefix = ''): Promise<DroppedFile[]> {
  if (entry.isFile) {
    return new Promise((resolve) => {
      (entry as FileSystemFileEntry).file(
        (f) => {
          if (f.name.startsWith('.')) return resolve([]);
          const path = prefix + f.name;
          resolve([{ file: f, ...(path === f.name ? {} : { relativePath: path }) }]);
        },
        () => resolve([]),
      );
    });
  }
  if (entry.isDirectory) {
    const reader = (entry as FileSystemDirectoryEntry).createReader();
    const children: FileSystemEntry[] = [];
    await new Promise<void>((resolve) => {
      const step = () =>
        reader.readEntries((batch) => {
          if (batch.length === 0) return resolve();
          children.push(...batch);
          step();
        }, () => resolve());
      step();
    });
    const out: DroppedFile[] = [];
    for (const child of children) {
      out.push(...(await flattenEntry(child, `${prefix}${entry.name}/`)));
    }
    return out;
  }
  return [];
}

/**
 * 드롭 이벤트의 `DataTransfer` 를 파일 목록으로 푼다.
 * `webkitGetAsEntry` 가 없는 환경(오래된 브라우저·일부 시험 환경)에서는
 * `dt.files` 로 폴백한다 — 낱개 파일 드롭은 그대로 성립한다.
 *
 * ⚠ **배포에서 HTTPS 를 걷어내지 않는다.** 폴더 펼치기는 **보안 컨텍스트**를 전제한다 —
 *    HTTP 로 서비스하면 이 경로가 조용히 폴백해 **폴더가 낱개 파일 하나로 접힌다**(오류가 안 난다).
 *    로컬은 `localhost` 라 보안 컨텍스트가 잡혀 **개발 중엔 안 보인다.** dev 에 도메인이 없어
 *    CloudFront 가 HTTPS 를 주는 유일한 수단인 이유가 이것이다 (`docs/DEPLOY.md §7`).
 */
export async function collectDrop(dt: DataTransfer): Promise<DroppedFile[]> {
  const items = Array.from(dt.items ?? []);
  const entries = items
    .map((item) => (item as { webkitGetAsEntry?: () => FileSystemEntry | null })
      .webkitGetAsEntry?.() ?? null)
    .filter((e): e is FileSystemEntry => e !== null);
  if (entries.length === 0) {
    return Array.from(dt.files ?? []).map((file) => ({ file }));
  }
  const nested = await Promise.all(entries.map((entry) => flattenEntry(entry)));
  return nested.flat();
}

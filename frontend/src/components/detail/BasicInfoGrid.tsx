// 기본 정보 — **아홉 칸**: 구성 · 좌표계 · 기간 · 격자 · 포맷 · 파일 · 원천 표기 · 소유자 · 올린 사람
// (`Policy_데이터셋_상세 §5`). 공간 범위 칸은 두지 않는다 — 이름과 지도가 이미 말한다.
// 잠긴 데이터는 이 블록을 통째로 비운다(`basicInfo` null) — 부르는 쪽이 아예 그리지 않는다.
import { useState } from 'react';
import { PieceList } from './PieceList';
import { EMPTY, formatFiles, formatPeriod, orEmpty } from './format';
import type { DatasetFile, FilesSource } from './filesSource';
import type { DatasetBasicInfo } from './types';

export function BasicInfoGrid(props: {
  basicInfo: DatasetBasicInfo;
  fileName: string | null;
  datasetId: string;
  filesSource: FilesSource;
}) {
  const b = props.basicInfo;
  // 목록은 **`보기` 를 눌렀을 때만** 부른다 (계약 축자 · §5 122행). 한 번 읽은 뒤 접었다
  // 다시 펴는 것은 같은 사실을 다시 묻는 일이라 부르지 않는다.
  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<DatasetFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  function toggle() {
    if (open) {
      setOpen(false);
      return;
    }
    setOpen(true);
    if (files !== null) return;
    setError(null);
    props.filesSource
      .list(props.datasetId)
      .then(setFiles)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : '파일 목록을 불러오지 못했어요.'),
      );
  }

  const cells: [string, string][] = [
    ['구성', b.variables.length > 0 ? b.variables.join(' · ') : EMPTY],
    ['좌표계', orEmpty(b.crs)],
    ['기간', formatPeriod(b.period)],
    ['격자', orEmpty(b.grid)],
    ['포맷', orEmpty(b.format)],
    ['파일', formatFiles(b.files, props.fileName)],
    ['원천 표기', orEmpty(b.sourceLabel)],
    ['소유자', b.owner.name],
    ['올린 사람', b.uploader.name],
  ];
  return (
    <>
      <div className="infogrid" data-testid="basic-info">
        {cells.map(([k, v]) => (
          <div className="ig" key={k} data-testid={`ig-${k}`}>
            <div className="k" data-testid="ig-k">
              {k}
            </div>
            <div className="v">
              {v}
              {k === '파일' ? (
                <button type="button" className="ig-more" onClick={toggle}>
                  {open ? '접기' : '보기'}
                </button>
              ) : null}
            </div>
          </div>
        ))}
      </div>
      {/* 목록은 **격자 아래** 페이지 흐름에 그대로 붙는다 — 자체 스크롤 상자를 만들지 않는다 (§5 122행) */}
      {open ? (
        error ? (
          <p className="fl-err" role="alert">
            {error}
          </p>
        ) : files ? (
          <PieceList files={files} />
        ) : (
          <div data-testid="file-list-loading" aria-busy="true" />
        )
      ) : null}
    </>
  );
}

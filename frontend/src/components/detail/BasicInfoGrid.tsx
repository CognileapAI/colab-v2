// 기본 정보 — **아홉 칸**: 구성 · 좌표계 · 기간 · 격자 · 포맷 · 파일 · 원천 표기 · 소유자 · 올린 사람
// (`Policy_데이터셋_상세 §5`). 공간 범위 칸은 두지 않는다 — 이름과 지도가 이미 말한다.
// 잠긴 데이터는 이 블록을 통째로 비운다(`basicInfo` null) — 부르는 쪽이 아예 그리지 않는다.
import { useState } from 'react';
import { PieceList } from './PieceList';
import { VariableTable, toVariableRows } from '../common/VariableTable';
import {
  EMPTY,
  INTERVAL_MISSING_NOTICE,
  formatExtension,
  formatFiles,
  formatInterval,
  formatPeriodWithInterval,
  orEmpty,
} from './format';
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

  // ⭑ **⟨19차 해제 · PRD-35⟩ 기간 뒤에 관측 간격을 괄호로 병기한다.** 조립은
  // `formatPeriodWithInterval` **한 곳**이고 목록 카드·등록 미리보기가 같은 함수를 쓴다.
  // 간격이 비면 괄호를 그리지 않고, 대신 아래 「관측 간격 미기재」 한 줄이 선다 (PRD-17) —
  // ⛔ **빈 괄호 `()` 를 그리지 않는다**: 그것은 「없다」가 아니라 잡음이다.
  const intervalMissing = formatInterval(b.observationInterval) === null;
  // ⭑ **⟨WU-B2 · PRD-16⟩ 구성 칸은 문자열이 아니라 5열 표다** — 등록 화면과 **같은
  // 컴포넌트**를 읽기 전용으로 그린다(열 순서·라벨이 갈리지 않게 하는 자리).
  // 행이 0개인 데이터셋은 이관 대상이 아니었던 기존 행이고, 그때는 종전대로 `EMPTY` 다.
  const variableRows = toVariableRows(b.variables);
  const cells: [string, string][] = [
    ['구성', variableRows.length > 0 ? '' : EMPTY],
    ['좌표계', orEmpty(b.crs)],
    ['기간', formatPeriodWithInterval(b.period, b.observationInterval)],
    ['격자', orEmpty(b.grid)],
    // **판별 문자열이 아니라 확장자다** (PRD-21) — 못 뽑은 행만 `format` 으로 퇴행한다.
    ['포맷', formatExtension(b.fileExtension, b.format)],
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
              {k === '구성' && variableRows.length > 0 ? (
                <VariableTable rows={variableRows} />
              ) : (
                v
              )}
              {/* PRD-17 — 안 적은 행은 **그 사실을 말한다.** 「모른다」를 빈 칸으로 두면
                  「간격이 없다」와 갈리지 않는다. ⛔ 재선택을 강제하지 않는다 — 안내 한 줄이다. */}
              {k === '기간' && intervalMissing ? (
                <span className="ig-note" data-testid="ig-interval-missing">
                  {INTERVAL_MISSING_NOTICE}
                </span>
              ) : null}
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

// S-08 의 조각들. **화면 글자는 전부 정본 §8.1·§9 에서 그대로 온다** — 여기서 새 한국어를
// 만들지 않는다. 문구를 바꾸고 싶으면 정본을 먼저 고친다 (`CLAUDE.md §5`).
import type { ReactNode } from 'react';
import type { PartialFailure, PreviewBasicInfo, RenderResult, RenderStage } from './types';
import { resultImageSrc } from './tiles';
import type { ZoomPan } from './useZoomPan';

/** 정본 §8.1 「휘발 고지」 — 두 문장과 등록 길이 **한 줄**에 있다. 남은 시간은 세지 않는다. */
export function VolatileNotice(props: { onRegister: () => void }) {
  return (
    <div className="pv-volatile" data-testid="volatile-notice">
      <p className="pv-volatile-text">
        <strong>연구실에 등록하지 않은 파일이에요</strong>
        <span>
          여기서 얼마든지 열어 볼 수 있어요. 다만 이 화면을 벗어나면 사라지고, 다른 사람은 볼 수
          없어요.
        </span>
      </p>
      {/* 「몇 시간 남았다」를 세면 등록을 서두르게 하는 화면이 되고,
          등록하지 않아도 된다는 이 화면의 주장이 흐려진다 (§8.1 휘발 고지) */}
      <button type="button" className="pv-register" onClick={props.onRegister}>
        연구실에 등록 →
      </button>
    </div>
  );
}

const BYTE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB'] as const;

function formatBytes(n: number): string {
  let v = n;
  let i = 0;
  while (v >= 1024 && i < BYTE_UNITS.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v >= 10 || i === 0 ? Math.round(v) : v.toFixed(1)} ${BYTE_UNITS[i]}`;
}

/**
 * 정본 §8.1 「기본정보」 — **파일 헤더에서 읽은 값만** 세우고, **헤더에 없는 항목은 자리째 뺀다.**
 * 빈 칸을 두면 못 읽은 것인지 값이 없는 것인지 갈린다. 그래서 대시(`—`)도 쓰지 않는다.
 * 이름·주제·소속 프로젝트는 **사람이 붙이는 값**이라 등록 전에는 자리 자체가 없다.
 */
export function BasicInfoPanel(props: { basicInfo: PreviewBasicInfo }) {
  const { basicInfo } = props;
  const rows: Array<[string, string]> = [];
  if (basicInfo.format) rows.push(['포맷', basicInfo.format]);
  if (typeof basicInfo.byteSize === 'number') rows.push(['크기', formatBytes(basicInfo.byteSize)]);
  if (basicInfo.crs) rows.push(['좌표계', basicInfo.crs]);
  if (basicInfo.period) rows.push(['기간', basicInfo.period]);
  if (basicInfo.variable) rows.push(['변수', basicInfo.variable]);
  if (basicInfo.grid) rows.push(['격자', basicInfo.grid]);

  return (
    <section className="pv-basic" data-testid="preview-basicinfo" aria-label="기본정보">
      <h2 className="pv-h2">기본정보</h2>
      <dl className="pv-basic-grid">
        {rows.map(([label, value]) => (
          <div className="pv-basic-row" key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** 진행 단계 — 정본 3문구 그대로. 안내는 `aria-live=polite` (§8 미리보기 그리기). */
export function RenderStageNotice(props: { stage?: RenderStage }) {
  return (
    <p className="pv-stage" data-testid="render-stage" aria-live="polite" aria-busy="true">
      {props.stage ? `${props.stage}…` : ''}
    </p>
  );
}

/** 실패 — 서버가 준 정본 문구를 그대로 낸다. 오류는 `assertive` (§8). */
export function RenderFailureNotice(props: { message: string }) {
  return (
    <p className="pv-failure" data-testid="render-failure" aria-live="assertive" role="alert">
      {props.message}
    </p>
  );
}

/**
 * 부분 실패 — **오류가 아니다.** 문구는 정본 §9 「조각 일부를 못 읽음」 행의 모양 그대로이고,
 * 숫자는 서버가 센 값이다. 못 읽은 조각은 **이름으로 밝힌다** — 지도에서 비어 보이는 자리를
 * 데이터가 없는 것으로 잘못 읽지 않게 한다.
 */
export function PartialFailureNotice(props: { partial: PartialFailure }) {
  const { totalParts, renderedParts, missingParts } = props.partial;
  const missed = totalParts - renderedParts;
  return (
    <div className="pv-partial" data-testid="partial-failure" aria-live="polite">
      <p>{`조각 ${totalParts}개 중 ${missed}개를 읽지 못했어요. 읽은 ${renderedParts}개로 그릴 수 있어요.`}</p>
      <ul>
        {missingParts.map((p) => (
          <li key={p.fileName}>
            {p.fileName}
            {p.instant ? ` · ${p.instant}` : ''}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * 415 — **그릴 수 없는 것과 등록할 수 없는 것은 다르다.** 안 되는 것만 말하면 무엇을 올려야
 * 하는지 모른 채 떠나므로 **그릴 수 있는 형식을 함께 적는다** (정본 §9 · `details.renderableFormats`).
 * 목록을 화면이 만들지 않는다 — 서버가 준 것만 잇는다.
 */
export function NotRenderableNotice(props: { message: string; renderableFormats: string[] }) {
  return (
    <div className="pv-notrenderable" data-testid="not-renderable" aria-live="polite">
      <p>{props.message}</p>
      {props.renderableFormats.length > 0 ? (
        <p>{`지금 그릴 수 있는 형식은 ${props.renderableFormats.join(' · ')} 예요.`}</p>
      ) : null}
      <p className="pv-muted">등록·계보 확정·다운로드는 그대로 할 수 있어요.</p>
    </div>
  );
}

/** 만료 — 정본 §8.1 수명 행·§9 마지막 행의 문구 그대로. 「권한」을 말하지 않는다. */
export function ExpiredNotice(props: { message: string }) {
  return (
    <div className="pv-expired" data-testid="preview-expired" aria-live="assertive" role="alert">
      <p>{props.message}</p>
    </div>
  );
}

/**
 * 지도. **`tileUrlTemplate` 은 불투명 문자열**이라 그대로 들고 있고 `{z}`·`{x}`·`{y}` 만 바꾼다
 * (`〈68〉` 서명이 실려 있다). 층 겹치기·불투명도·시각 선택은 계약에 없어 두지 않는다.
 *
 * **확대(줌)는 선택이다** — `zoom` 을 받으면 층 묶음에 변환을 걸고 컨트롤을 세운다
 * (정본 §8 「확대(줌)」 · v2.5). 받지 않는 화면(S-08)은 지금까지와 한 글자도 다르지 않다.
 * ⚠ **변환은 `pv-layers` 하나에 건다** — 층마다 따로 걸면 정본 조건 ⑸(모든 층에 함께)가 깨진다.
 * ⚠ **범례는 `pv-layers` 밖이다** — 조건 ⑵(확대해도 범례가 바뀌지 않는다)가 그 자리를 정한다.
 */
export function PreviewMap(props: { result: RenderResult; zoom?: ZoomPan; actions?: ReactNode }) {
  const { result, zoom } = props;
  const src = resultImageSrc(result);
  return (
    <section
      className="pv-map"
      data-testid="preview-map"
      {...(result.tileUrlTemplate ? { 'data-tile-template': result.tileUrlTemplate } : {})}
      /* 좌표가 없는 결과(②비지도형)도 **완료**다 — 배지가 그 사실을 말한다 (`〈85〉`) */
      {...(result.precisionBadge ? { 'data-precision-badge': result.precisionBadge } : {})}
      {...(result.colorRangeStage ? { 'data-color-range-stage': result.colorRangeStage } : {})}
      aria-label="미리보기"
    >
      <div className="pv-mapcol">
        <div
          className="pv-viewport"
          data-testid="preview-viewport"
          ref={zoom?.viewportRef}
          {...(zoom
            ? {
                onWheel: zoom.onWheel,
                onMouseDown: zoom.onMouseDown,
                'data-zoomable': 'true',
              }
            : {})}
        >
          <div
            className="pv-layers"
            data-testid="preview-layers"
            {...(zoom
              ? {
                  'data-zoom-scale': String(zoom.scale),
                  style: {
                    transform: `translate(${zoom.x}px, ${zoom.y}px) scale(${zoom.scale})`,
                    transformOrigin: '0 0',
                  },
                }
              : {})}
          >
            {src ? (
              <img className="pv-tile" src={src} alt="" {...(zoom ? { onLoad: zoom.onImageLoad } : {})} />
            ) : null}
          </div>
        </div>
        {zoom ? <ZoomControls zoom={zoom} /> : null}
        {props.actions ?? null}
      </div>
      <dl className="pv-legend" aria-label="범례">
        {result.legend.classes.map((c) => (
          <div className="pv-legend-row" key={`${c.min}-${c.max}`}>
            <dt>
              <span className="pv-swatch" style={{ background: c.color }} />
            </dt>
            <dd>{`${c.min} ~ ${c.max}${result.legend.unit ? ` ${result.legend.unit}` : ''}`}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/**
 * 확대 컨트롤. **편집 컨트롤이 아니다** — 정본 §8 `확대·이동` 행이 「확대는 시각화 편집이
 * 아니라 보기다 … 보기 권한만 있어도 된다」로 못 박았으므로 권한으로 가리지 않는다(조건 ⑹).
 * 한계 안내 문구는 정본 축자다 — 여기서 새 한국어를 만들지 않는다(조건 ⑷).
 */
function ZoomControls(props: { zoom: ZoomPan }) {
  const { zoom } = props;
  return (
    <div className="pv-zoom" data-testid="preview-zoom">
      <button type="button" onClick={zoom.zoomIn}>
        확대
      </button>
      <button type="button" onClick={zoom.zoomOut}>
        축소
      </button>
      <button type="button" onClick={zoom.reset}>
        기본 배율로
      </button>
      {zoom.atLimit ? (
        <p className="pv-muted" data-testid="zoom-limit" aria-live="polite">
          원본 해상도까지 봤어요
        </p>
      ) : null}
    </div>
  );
}

/**
 * 정본 §8.1 「계보·족보」와 「검색·공유·승인」 — **빈 자리 + 안내 문구.**
 * 기능을 막아서가 아니라 비어 있는 것으로 등록의 값어치를 말한다.
 */
export function EmptySlots() {
  return (
    <>
      <section className="pv-slot" data-testid="slot-lineage" aria-label="계보 · 족보">
        <h2 className="pv-h2">계보 · 족보</h2>
        <p className="pv-slot-note">등록하면 AI가 가공 전 데이터를 찾아 줘요</p>
      </section>
      <section className="pv-slot" data-testid="slot-share" aria-label="검색 · 공유 · 승인">
        <h2 className="pv-h2">검색 · 공유 · 승인</h2>
        <p className="pv-slot-note">등록하면 연구실이 이 데이터를 찾을 수 있어요</p>
      </section>
    </>
  );
}

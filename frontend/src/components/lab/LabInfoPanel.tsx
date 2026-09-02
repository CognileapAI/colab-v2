// `연구실 설정 > 연구실 정보` — 연구실을 정의하는 **유일한 자리**
// (`DataModel_공통_기반 §2` 「고치는 화면은 `연구실 설정 > 연구실 정보`」).
//
// 구조는 목업 S-07 그대로다 (`mockups/제품_260817.html` · `연구실 정보(연구실 정의)` 카드):
// 읽기 요약 카드 + 헤더 오른쪽 `정보 편집` 버튼 → `연구실 정보` 편집 모달(폼 7칸 · 취소·저장).
//
// **읽기는 전 구성원, 편집만 `연구실 설정` 스위치**
// (`Policy_역할과_권한 나-2` 「연구실 정보 편집 · `연구실 설정` · 거절한다. **읽기는 전 구성원**」).
// 숨김은 안내이고 판정은 서버다 (같은 문서 7절) — 그래서 저장 실패 문안은 서버 것을 그대로 올린다.
//
// 읽기 표시는 홈 읽기 모달과 **같은 컴포넌트**(`LabInfoGrid`)이고 배선도 한 곳(`labSource`)이다.
import { useEffect, useState } from 'react';
import './lab.css';
import { PermissionGate } from '../../permission/PermissionGate';
import { LabInfoGrid } from './LabInfoGrid';
import { apiLabSource, type Lab, type LabSource, type LabUpdate } from './labSource';

/** 편집 폼 일곱 칸 — 목업 편집 모달의 라벨·순서를 한 자도 바꾸지 않는다. */
type Draft = {
  name: string;
  university: string;
  department: string;
  principalInvestigator: string;
  researchField: string;
  introduction: string;
  defaultVisibility: Lab['defaultVisibility'];
};

/** `데이터 공개 범위` 는 계약이 두 값으로 고정한다 (`LabDefaultVisibility` → `AccessState`). */
const VISIBILITIES: Lab['defaultVisibility'][] = ['열림', '잠김'];

function draftOf(lab: Lab): Draft {
  return {
    name: lab.name,
    university: lab.university ?? '',
    department: lab.department ?? '',
    principalInvestigator: lab.principalInvestigator ?? '',
    researchField: lab.researchField ?? '',
    introduction: lab.introduction ?? '',
    defaultVisibility: lab.defaultVisibility,
  };
}

/** 빈 칸은 `null` 로 보낸다 — 계약이 여섯 칸에 `null` 을 허용한다. 이름만 필수다. */
function bodyOf(d: Draft): LabUpdate {
  const orNull = (v: string) => (v.trim() === '' ? null : v.trim());
  return {
    name: d.name.trim(),
    university: orNull(d.university),
    department: orNull(d.department),
    principalInvestigator: orNull(d.principalInvestigator),
    researchField: orNull(d.researchField),
    introduction: orNull(d.introduction),
    defaultVisibility: d.defaultVisibility,
  };
}

export function LabInfoPanel(props: { source?: LabSource | undefined }) {
  const source = props.source ?? apiLabSource();
  const [lab, setLab] = useState<Lab | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    source
      .read()
      .then((value) => alive && setLab(value))
      .catch((e: unknown) => {
        if (alive) setError(e instanceof Error ? e.message : '연구실 정보를 불러오지 못했어요.');
      });
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function edit(patch: Partial<Draft>) {
    setDraft((d) => (d === null ? d : { ...d, ...patch }));
  }

  async function save() {
    if (draft === null) return;
    // 서버가 같은 자리를 400 으로 막는다 — 문안을 새로 짓지 않고 서버 것을 쓴다.
    if (draft.name.trim() === '') {
      setError('연구실 이름을 적어 주세요.');
      return;
    }
    try {
      const saved = await source.update(bodyOf(draft));
      setLab(saved);
      setDraft(null);
      setError(null);
      setNotice('연구실 정보를 저장했어요');
    } catch (e: unknown) {
      // 저장에 실패하면 **편집 모달을 유지한다** — 적은 값을 잃지 않는다(구성원·권한과 같은 규칙).
      setError(e instanceof Error ? e.message : '연구실 정보를 저장하지 못했어요.');
    }
  }

  return (
    <div className="card labinfo-card" data-panel="연구실 정보">
      <div className="card-h">
        <h3>연구실 정보</h3>
        {/* 편집 버튼만 권한자에게 — 읽기는 전 구성원이다 (E-01 나-1·나-2) */}
        {lab !== null && (
          <PermissionGate requires="연구실 설정">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setNotice(null);
                setError(null);
                setDraft(draftOf(lab));
              }}
            >
              정보 편집
            </button>
          </PermissionGate>
        )}
      </div>

      <div className="card-b">
        {/* 편집 모달이 열려 있으면 오류는 모달 안에서만 말한다 — 한 오류를 두 곳에 적지 않는다 */}
        {error !== null && draft === null && (
          <p className="labinfo-error" role="alert">
            {error}
          </p>
        )}
        {notice !== null && error === null && (
          <p className="labinfo-notice" data-testid="labinfo-notice">
            {notice}
          </p>
        )}
        {lab !== null ? <LabInfoGrid lab={lab} /> : null}
      </div>

      {draft !== null && (
        <div className="labinfo-modal-back" role="dialog" aria-modal="true" aria-label="연구실 정보 편집">
          <div className="labinfo-modal">
            <h3>연구실 정보</h3>
            <div className="form-row">
              <label htmlFor="lab-name">연구실 이름</label>
              <input
                id="lab-name"
                className="inp"
                value={draft.name}
                onChange={(e) => edit({ name: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-univ">소속 대학</label>
              <input
                id="lab-univ"
                className="inp"
                value={draft.university}
                onChange={(e) => edit({ university: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-dept">학부 · 학과</label>
              <input
                id="lab-dept"
                className="inp"
                value={draft.department}
                onChange={(e) => edit({ department: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-pi">책임교수</label>
              <input
                id="lab-pi"
                className="inp"
                value={draft.principalInvestigator}
                onChange={(e) => edit({ principalInvestigator: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-field">연구 분야</label>
              <input
                id="lab-field"
                className="inp"
                value={draft.researchField}
                onChange={(e) => edit({ researchField: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-desc">한 줄 소개</label>
              <input
                id="lab-desc"
                className="inp"
                value={draft.introduction}
                onChange={(e) => edit({ introduction: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label htmlFor="lab-scope">데이터 공개 범위</label>
              <select
                id="lab-scope"
                className="sel"
                value={draft.defaultVisibility}
                onChange={(e) =>
                  edit({ defaultVisibility: e.target.value as Lab['defaultVisibility'] })
                }
              >
                {VISIBILITIES.map((v) => (
                  <option key={v} value={v}>
                    {v}
                  </option>
                ))}
              </select>
            </div>
            {/* 목업 축자 — 공개 범위는 연구실 **기본값**이고 데이터셋 값이 이긴다 (P-27) */}
            <p className="def-note">
              공개 범위는 <b>기본값</b>이에요. 데이터셋마다 따로 정한 값이 있으면 그쪽이 이겨요.
            </p>
            {error !== null && (
              <p className="labinfo-error" role="alert">
                {error}
              </p>
            )}
            <div className="labinfo-modal-foot">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setDraft(null);
                  setError(null);
                }}
              >
                취소
              </button>
              <button type="button" className="btn btn-primary" onClick={save}>
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

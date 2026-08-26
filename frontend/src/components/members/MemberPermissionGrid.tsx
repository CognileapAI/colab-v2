// 연구실 설정 > 구성원 · 권한 — 권한 스위치를 고치는 **유일한 자리** (§3 · P-18).
//
// 정본: `E-01 Policy_역할과_권한 v1.3` §3(격자·3단 저장) · §4(숨김) · §6(역할 표기)
//       화면 문안·구조는 `mockups/제품_260817.html` S-07 `구성원 · 권한` 카드에서 그대로 가져왔다.
// 목업에 없는 요소를 발명하지 않는다. `+ 구성원 초대` 는 **P1(계정과 연구실 소속) 범위 밖**이라 뺐다
// — 계약에도 그 op 이 없다.
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { MembersPort, PortResult } from './port';
import {
  MEMBER_COLUMNS,
  PERMISSION_SWITCHES,
  diffOf,
  draftOf,
  isEditable,
  roleLabel,
  type Draft,
  type LabMember,
} from './permissions';
import './members.css';

export function MemberPermissionGrid(props: { port: MembersPort }) {
  const { port } = props;
  const [members, setMembers] = useState<LabMember[] | null>(null);
  const [draft, setDraft] = useState<Draft>({});
  const [editing, setEditing] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const apply = useCallback((result: PortResult) => {
    if (!result.ok) {
      setError(result.message);
      return false;
    }
    setError(null);
    setMembers(result.items);
    setDraft(draftOf(result.items));
    return true;
  }, []);

  useEffect(() => {
    let alive = true;
    void port.list().then((r) => {
      if (alive) apply(r);
    });
    return () => {
      alive = false;
    };
  }, [port, apply]);

  const changes = useMemo(() => (members ? diffOf(members, draft) : []), [members, draft]);

  if (members === null) return <div className="memgrid" data-testid="members-loading" />;

  /** 편집 시작 — 여기서부터 체크가 열린다. 저장하기 전까지는 반영되지 않는다 (§3). */
  function startEdit() {
    setNotice('권한 편집을 시작했어요. 저장하기 전까지는 반영되지 않아요');
    setError(null);
    setEditing(true);
  }

  /** 편집 취소 — 원래 값으로 되돌린다 (§3 표). */
  function cancelEdit() {
    setDraft(draftOf(members as LabMember[]));
    setEditing(false);
    setConfirming(false);
    setNotice('편집을 취소했어요. 권한은 그대로예요');
  }

  /** 편집 중에는 토스트를 띄우지 않고 **바뀐 칸에 표식만** 남긴다 (§3 표 · P-20). */
  function toggle(member: LabMember, sw: (typeof PERMISSION_SWITCHES)[number]) {
    setDraft((prev) => ({
      ...prev,
      [member.accountId]: {
        ...prev[member.accountId],
        [sw]: !prev[member.accountId]?.[sw],
      },
    }));
  }

  /** `저장` 은 요청이 아니라 **확인 모달**을 연다 (§3 · P-19). */
  function openConfirm() {
    if (changes.length === 0) {
      setEditing(false);
      setNotice('바뀐 권한이 없어요');
      return;
    }
    setNotice(null);
    setConfirming(true);
  }

  /** 모달의 취소는 **편집 모드를 유지한다** — 저장만 물린 것이다 (§3 표 · P-20). */
  function closeConfirm() {
    setConfirming(false);
  }

  async function save() {
    const count = changes.length;
    const result = await port.save({ items: changes });
    setConfirming(false);
    if (!apply(result)) return; // 403 등 — 편집 모드를 유지한 채 서버 문안을 보인다 (P-11)
    setEditing(false);
    setNotice(`권한 ${count}건을 저장했어요`);
  }

  return (
    <div className="card memgrid">
      <div className="card-h">
        <h3>구성원 · 권한</h3>
        <div className="memact">
          {/* 편집 중이 아닐 때만 `권한 편집`, 편집 중일 때만 `취소`·`저장` — 목업 그대로 */}
          {!editing && (
            <button type="button" className="btn btn-secondary btn-sm" onClick={startEdit}>
              권한 편집
            </button>
          )}
          {editing && (
            <>
              <button type="button" className="btn btn-ghost btn-sm" onClick={cancelEdit}>
                취소
              </button>
              <button type="button" className="btn btn-primary btn-sm" onClick={openConfirm}>
                저장
              </button>
            </>
          )}
        </div>
      </div>

      {error !== null && (
        <p className="memerr" role="alert">
          {error}
        </p>
      )}
      {notice !== null && error === null && (
        <p className="memnotice" data-testid="members-notice">
          {notice}
        </p>
      )}

      <div className="card-b">
        <table className={`tbl memtbl${editing ? ' is-editing' : ''}`}>
          <thead>
            <tr>
              {MEMBER_COLUMNS.map((c) => (
                <th key={c}>{c}</th>
              ))}
              {PERMISSION_SWITCHES.map((sw) => (
                <th key={sw} className="pc">
                  {sw}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.accountId}>
                <td className="who">
                  <div className="mn">{m.name}</div>
                  <div className="me">{m.email}</div>
                </td>
                <td>
                  <span className="chip chip--neutral">{roleLabel(m)}</span>
                </td>
                {PERMISSION_SWITCHES.map((sw) => {
                  const value = draft[m.accountId]?.[sw] === true;
                  const changed = value !== m.permissions[sw];
                  // 편집 불가 열도 **값은 보인다** — 열을 지우면 표 구조가 깨진다 (P-31).
                  // 여기에 P-12(숨김)를 적용하지 않는 이유가 그것이다.
                  return (
                    <td key={sw} className={`pc${changed ? ' is-chg' : ''}`} data-sw={sw}>
                      <input
                        type="checkbox"
                        checked={value}
                        disabled={!editing || !isEditable(m, sw)}
                        aria-label={`${m.name} · ${sw}`}
                        onChange={() => toggle(m, sw)}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 목업 하단 안내문 — 한 자도 바꾸지 않았다 */}
      <p className="memhint">
        승인 위임을 켜면 그 연구원의 할 일 함에 접근 요청이 들어오고, 연구실 설정을 켜면 상단 메뉴에
        연구실 설정이 생겨요.
      </p>

      {confirming && (
        // 확인 모달은 **변경 내역을 다시 나열하지 않는다** (§3 표 · P-20).
        // 방금 표에서 직접 체크했고 표식도 그대로 보인다.
        <div className="modal-back show">
          <div className="modal" role="dialog" aria-modal="true" aria-label="권한을 이렇게 바꿀까요?">
            <div className="modal-h">
              <h3>권한을 이렇게 바꿀까요?</h3>
            </div>
            <div className="modal-b">
              <p>바꾼 권한을 저장할까요? 저장하는 즉시 그 사람 화면에 반영돼요.</p>
            </div>
            <div className="modal-f">
              <button type="button" className="btn btn-secondary" onClick={closeConfirm}>
                취소
              </button>
              <button type="button" className="btn btn-primary" onClick={() => void save()}>
                저장
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

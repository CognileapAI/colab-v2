// 운영자 백오피스 — 계정 추가(기존) ＋ 계정 목록 · 비밀번호 재설정 · 비활성화/재활성화.
//
// 목록은 **전 연구실 한 벌**이고 필터 네 가지는 서버가 건다(화면이 받아 와서 거르지 않는다 —
// 거르면 「목록에 없다」가 「권한이 없다」와 구분되지 않는다).
// 재설정·비활성화는 확인을 거치고, 비밀번호 원문은 화면 어디에도 되돌아오지 않는다.
import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { api } from '../api/client';
import type { Schemas } from '../api/client';
import { useAccount } from '../permission/session';
import '../auth/login.css';
import { validNewPassword } from '../auth/passwordRules';
import { useWorkProtection } from '../auth/useWorkProtection';
import { useDialogFocus } from '../components/common/useDialogFocus';

type Row = Schemas['ServiceAccountSummaryV2'];
type Options = Schemas['AccountOptions'];
type Filters = { labId: string; status: string; role: string; email: string };
const EMPTY: Filters = { labId: '', status: '', role: '', email: '' };
const STATUS_LABEL: Record<string, string> = { active: '사용 중', inactive: '비활성' };
// Ted 문면 확정 대기 · R-LTH-REVIEW-1
const SELF_STATUS_REASON = '자기 계정은 비활성화할 수 없어요';
const day = (ts: string | null) => (ts ? ts.slice(0, 10) : '기록 없음');

/** 새 초기 비밀번호 두 칸. 값은 대화상자 밖으로 나가지 않고 성공하면 그 자리에서 사라진다. */
function ResetDialog(props: { row: Row; busy: boolean; onClose(): void; onConfirm(pw: string): void }) {
  const titleId = useId();
  const valueId = useId();
  const confirmId = useId();
  const [value, setValue] = useState('');
  const [confirm, setConfirm] = useState('');
  const dialogRef = useDialogFocus(props.onClose, props.busy);
  const ready = validNewPassword(value) && value === confirm;
  return (
    <div className="account-modal-back">
      <div ref={dialogRef} tabIndex={-1} className="account-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h3 id={titleId}>비밀번호 재설정</h3>
        <p className="account-modal-lead">
          <b>{props.row.email}</b> 의 새 초기 비밀번호를 입력하고 당사자에게 직접 전달하세요.
          그 사람의 기존 로그인은 모든 기기에서 끝나고, 다음 로그인 때 비밀번호 변경을 다시 요구해요.
        </p>
        <label className="login-label" htmlFor={valueId}>새 초기 비밀번호</label>
        <input id={valueId} className="login-input" type="password" autoComplete="new-password"
               value={value} onChange={e => setValue(e.target.value)} />
        <label className="login-label" htmlFor={confirmId}>새 초기 비밀번호 확인</label>
        <input id={confirmId} className="login-input" type="password" autoComplete="new-password"
               value={confirm} onChange={e => setConfirm(e.target.value)} />
        <p className="account-modal-help">10~512자로 입력하세요. 확인 칸까지 같아야 보낼 수 있어요.</p>
        <div className="account-modal-actions">
          <button type="button" className="btn btn-secondary" disabled={props.busy} onClick={props.onClose}>그대로 두기</button>
          <button type="button" className="btn btn-strong" disabled={props.busy || !ready}
                  onClick={() => props.onConfirm(value)}>재설정</button>
        </div>
      </div>
    </div>
  );
}

/** 비활성화/재활성화 확인. 「데이터는 사라지지 않아요」를 확인 문구보다 먼저 말한다. */
function StatusDialog(props: { row: Row; next: 'active' | 'inactive'; busy: boolean; onClose(): void; onConfirm(): void }) {
  const titleId = useId();
  const dialogRef = useDialogFocus(props.onClose, props.busy);
  const off = props.next === 'inactive';
  return (
    <div className="account-modal-back">
      <div ref={dialogRef} tabIndex={-1} className="account-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h3 id={titleId}>{off ? '계정 비활성화' : '계정 재활성화'}</h3>
        <p className="account-modal-lead">
          <b>데이터는 사라지지 않아요.</b> {props.row.email} 이 올린 자료와 소유권은 그대로 남아요.
        </p>
        <p className="account-modal-help">
          {off
            ? '비활성화하면 이 사람은 바로 로그인할 수 없고, 열려 있던 로그인도 모든 기기에서 끝나요.'
            : '재활성화하면 다시 로그인할 수 있어요. 비밀번호는 예전 그대로예요.'}
        </p>
        <div className="account-modal-actions">
          <button type="button" className="btn btn-secondary" disabled={props.busy} onClick={props.onClose}>그대로 두기</button>
          <button type="button" className="btn btn-strong" disabled={props.busy} onClick={props.onConfirm}>
            {off ? '비활성화' : '재활성화'}
          </button>
        </div>
      </div>
    </div>
  );
}

/** 시스템 관리자 지정·해제 확인. 무엇이 달라지는지를 확인 문구보다 먼저 말한다. */
function OperatorDialog(props: { row: Row; next: boolean; busy: boolean; onClose(): void; onConfirm(): void }) {
  const titleId = useId();
  const dialogRef = useDialogFocus(props.onClose, props.busy);
  const title = props.next ? '시스템 관리자 지정' : '시스템 관리자 해제';
  return (
    <div className="account-modal-back">
      <div ref={dialogRef} tabIndex={-1} className="account-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h3 id={titleId}>{title}</h3>
        <p className="account-modal-lead">
          <b>{props.row.email}</b> 을(를) {props.next ? '시스템 관리자로 지정해요.' : '시스템 관리자에서 해제해요.'}
        </p>
        <p className="account-modal-help">
          {props.next
            ? '시스템 관리자는 계정을 추가·재설정·비활성화할 수 있고, 모든 연구실의 자료와 구성원을 조회·등록·수정·삭제할 수 있어요.'
            : '해제하면 계정 관리 화면과 다른 연구실 자료를 더는 볼 수 없어요. 자기 연구실 권한은 그대로예요.'}
        </p>
        <p className="account-modal-help">이 사람의 열려 있던 로그인은 모든 기기에서 끝나요.</p>
        <div className="account-modal-actions">
          <button type="button" className="btn btn-secondary" disabled={props.busy} onClick={props.onClose}>그대로 두기</button>
          <button type="button" className="btn btn-strong" disabled={props.busy} onClick={props.onConfirm}>{title}</button>
        </div>
      </div>
    </div>
  );
}

export function AccountAdminPage() {
  const account = useAccount();
  const operator = account?.canManageServiceAccounts === true;
  const [options, setOptions] = useState<Options>();
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const formRef = useRef<HTMLFormElement | null>(null);

  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [rows, setRows] = useState<Row[]>();
  const [listError, setListError] = useState<string | null>(null);
  const [rowBusy, setRowBusy] = useState(false);
  const [resetRow, setResetRow] = useState<Row | null>(null);
  const [statusRow, setStatusRow] = useState<Row | null>(null);
  const [operatorRow, setOperatorRow] = useState<Row | null>(null);
  const [tab, setTab] = useState<'list' | 'create'>('list');
  // ⭑ ⟨2026-09-17 · #84⟩ 기본값은 **꺼짐**이다 ／ 종전 ~~`useState(true)`~~ — 주 동작은
  //   일반 사용자 계정 생성이고, 권한이 기본값이 되면 안 된다.
  const [createOperator, setCreateOperator] = useState(false);
  /**
   * ⭑ ⟨2026-09-17 · #84⟩ 연구실·역할은 uncontrolled(`name` ＋ FormData)다.
   * `disabled` 만 붙이면 FormData 에서 빠져 **전송은 비지만 화면 값은 남는다.**
   * 「값을 비움」을 실제로 만들려면 두 칸의 `value` 를 되돌려야 한다 — 가장 작은 수단이
   * ref reset 이다. controlled 로 바꾸면 「등록 탭 값이 목록 탭을 다녀와도 유지된다」를
   * 다시 세워야 한다. ⛔ `name` 은 지우거나 바꾸지 않는다(dev-seed 러너가 짚는 계약값).
   */
  const labRef = useRef<HTMLSelectElement | null>(null);
  const roleRef = useRef<HTMLSelectElement | null>(null);
  /** 체크 상태를 한 자리에서 바꾼다 — 끄고 켤 때 화면과 전송이 갈리지 않게 한다. */
  const changeCreateOperator = (next: boolean) => {
    setCreateOperator(next);
    if (next) {
      if (labRef.current) labRef.current.value = '';
      if (roleRef.current) roleRef.current.value = '';
    }
  };

  useWorkProtection('account-admin', {
    dirty, inFlight: busy || rowBusy,
    discard: () => { formRef.current?.reset(); setDirty(false); setCreateOperator(false); },
  });

  const load = useCallback(async () => {
    const query: Record<string, string> = {};
    if (filters.labId) query.labId = filters.labId;
    if (filters.status) query.status = filters.status;
    if (filters.role) query.role = filters.role;
    if (filters.email) query.email = filters.email;
    try {
      const { data, error } = await api.GET('/admin/accounts-v2', { params: { query } });
      if (data) { setRows(data.accounts); setListError(null); }
      else setListError(error?.message ?? '계정 목록을 불러오지 못했어요.');
    } catch { setListError('서버에 연결하지 못했어요. 잠시 뒤에 다시 시도해 주세요.'); }
  }, [filters]);

  useEffect(() => {
    if (!operator) return;
    void api.GET('/admin/account-options').then(({ data }) => data && setOptions(data));
  }, [operator]);
  useEffect(() => { if (operator) void load(); }, [operator, load]);

  // 본문 영역은 셸(`AppLayout` 의 `<main className="appmain">`)것 하나다 — 화면이 또 만들면
  // 보조기기가 본문을 둘로 읽는다. 이 화면은 `div`/`section` 으로만 구역을 나눈다.
  if (!operator) return <div><h1>계정 관리</h1><p>서비스 운영자만 사용할 수 있어요.</p></div>;

  const pick = (key: keyof Filters) => (e: { target: { value: string } }) =>
    setFilters(current => ({ ...current, [key]: e.target.value }));

  async function send(path: '/admin/accounts/{accountId}/password-reset' | '/admin/accounts/{accountId}/status'
                            | '/admin/accounts/{accountId}/operator',
                     accountId: string, body: Record<string, string | boolean>, done: string) {
    setRowBusy(true);
    setMessage(null);
    try {
      const { error } = await api.POST(path, {
        params: { path: { accountId } },
        body: body as never,
      });
      if (error) { setMessage(error.message ?? '요청을 처리하지 못했어요.'); return false; }
      setMessage(done);
      await load();
      return true;
    } catch { setMessage('서버에 연결하지 못했어요. 결과를 확인한 뒤 다시 시도해 주세요.'); return false; }
    finally { setRowBusy(false); }
  }

  return (
    /* ⭑ ⟨2026-09-17 · #84⟩ `account-admin` 은 세로 가운데 정렬을 덮는 **수식 클래스**다.
       공용 `.login` 을 직접 고치면 로그인 화면과 비밀번호 변경 화면이 함께 깨진다 —
       그 두 화면은 이번 대상이 아니다(`login.css` 의 `.login.account-admin`). */
    <div className="login account-admin">
      <h1>계정 관리</h1>
      <div className="settabs" role="tablist" aria-label="계정 관리 탭">
        <button type="button" role="tab" aria-selected={tab === 'list'}
                className={`st${tab === 'list' ? ' on' : ''}`} onClick={() => setTab('list')}>
          사용자 목록
        </button>
        <button type="button" role="tab" aria-selected={tab === 'create'}
                className={`st${tab === 'create' ? ' on' : ''}`} onClick={() => setTab('create')}>
          {/* ⭑ ⟨2026-09-17 · #84⟩ 탭·카드 제목·제출 버튼을 한 문면으로 통일한다 —
              한 화면에 「초대」·「관리자 등록」·「사용자 생성」이 섞이면 무슨 일이
              일어나는지 알 수 없다. 주 동작은 일반 사용자 계정 생성이다. */}
          사용자 생성
        </button>
      </div>
      <div hidden={tab !== 'create'}>
      <section className="login-card account-card" data-testid="account-create">
        <span className="login-brand">Co-Lab</span>
        <h2 className="login-title">사용자 생성</h2>
        <p className="login-lead">소속이 있으면 연구실과 역할을 함께 지정하세요. 둘 다 비우면 무소속 시스템 관리자로 등록돼요.</p>
        <form ref={formRef} className="account-form" onInput={() => setDirty(true)} onSubmit={async e => {
          e.preventDefault();
          if (busy) return;
          setMessage(null);
          const form = e.currentTarget;
          const f = new FormData(form);
          const initialPassword = String(f.get('initialPassword'));
          if (!validNewPassword(initialPassword)) { setMessage('초기 비밀번호는 10~512자로 입력해 주세요.'); return; }
          const labId = String(f.get('labId') ?? '');
          const role = String(f.get('role') ?? '');
          if (Boolean(labId) !== Boolean(role)) { setMessage('연구실과 역할을 함께 지정하거나 함께 비워 주세요.'); return; }
          if (!createOperator && !labId) { setMessage('일반 사용자는 연구실과 역할을 지정해 주세요.'); return; }
          setBusy(true);
          try {
            const { data, error } = await api.POST('/admin/accounts-v2', { body: {
              email: String(f.get('email')), name: String(f.get('name')),
              initialPassword,
              ...(createOperator ? { operator: true } : {}),
              ...(labId ? {
                labId,
                role: role as '교수' | '연구원',
              } : {}),
            } });
            setMessage(data ? data.email + ' 계정을 추가했어요.' : (error?.message ?? '계정을 추가하지 못했어요.'));
            // 성공 뒤 폼을 되돌린다. 체크박스는 controlled 라 `reset()` 이 닿지 않으므로
            // 기본값(꺼짐)을 여기서 직접 되돌린다 — 다음 생성이 관리자로 시작하지 않는다.
            if (data) { form.reset(); setDirty(false); setCreateOperator(false); void load(); }
          } catch { setMessage('서버에 연결하지 못했어요. 계정이 추가됐는지 확인한 뒤 다시 시도해 주세요.'); }
          finally { setBusy(false); }
        }}>
          {/* ⭑ ⟨2026-09-17 · #84⟩ 관리자 여부가 **폼의 첫 요소**다 — 그 선택이 아래 칸을
              채울 필요가 있는지를 결정한다. 체크하면 연구실·역할이 비활성이 되고 값이 빈다. */}
          <label className="login-label account-operator-check">
            <input type="checkbox" name="operator" data-testid="ac-operator" checked={createOperator}
                   onChange={e => changeCreateOperator(e.target.checked)} /> 시스템 관리자로 등록
          </label>
          <p className="login-label">시스템 관리자는 계정을 관리하고 모든 연구실 자료와 구성원을 관리할 수 있어요.</p>
          <label className="login-label">이름<input className="login-input" name="name" data-testid="ac-name" required /></label>
          <label className="login-label">이메일<input className="login-input" name="email" data-testid="ac-email" type="email" required /></label>
          <label className="login-label">연구실<select ref={labRef} className="login-input" name="labId" data-testid="ac-lab" disabled={createOperator}><option value="">소속 없음</option>{options?.labs.map(l => <option key={l.labId} value={l.labId}>{l.name}</option>)}</select></label>
          <label className="login-label">역할<select ref={roleRef} className="login-input" name="role" data-testid="ac-role" disabled={createOperator}><option value="">신분 없음</option>{options?.roles.map(r => <option key={r} value={r}>{r === '교수' ? '교수 관리자' : r}</option>)}</select></label>
          <label className="login-label">초기 비밀번호<input className="login-input" name="initialPassword" data-testid="ac-password" aria-describedby="initial-password-help" type="password" autoComplete="new-password" required /></label>
          <p id="initial-password-help" className="login-label">10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니에요. 사용자는 첫 로그인 때 비밀번호를 변경해야 해요.</p>
          <button className="login-submit" type="submit" data-testid="ac-submit" disabled={busy}>{busy ? '등록하는 중…' : '사용자 생성'}</button>
        </form>
      </section>
      </div>
      <div hidden={tab !== 'list'}>
      <section className="login-card account-list-card" data-testid="account-list">
        <h2 className="login-title">계정 목록</h2>
        <p className="login-lead">전 연구실 계정을 한 목록으로 봐요. 비밀번호 분실·퇴소를 여기서 처리해요.</p>
        <fieldset className="account-filters" aria-label="계정 목록 필터">
          <label className="login-label">연구실
            <select className="login-input" value={filters.labId} onChange={pick('labId')}>
              <option value="">전체</option>
              {options?.labs.map(l => <option key={l.labId} value={l.labId}>{l.name}</option>)}
            </select>
          </label>
          <label className="login-label">상태
            <select className="login-input" value={filters.status} onChange={pick('status')}>
              <option value="">전체</option>
              <option value="active">사용 중</option>
              <option value="inactive">비활성</option>
            </select>
          </label>
          <label className="login-label">역할
            <select className="login-input" value={filters.role} onChange={pick('role')}>
              <option value="">전체</option>
              {options?.roles.map(r => <option key={r} value={r}>{r === '교수' ? '교수 관리자' : r}</option>)}
            </select>
          </label>
          <label className="login-label">이메일
            <input className="login-input" type="search" value={filters.email} onChange={pick('email')} />
          </label>
        </fieldset>

        {listError ? <p className="account-status" role="alert">{listError}</p> : null}
        {/* 표 좌우 이동 안내 ＋ 키보드 초점 래퍼 = 다른 표 3자리와 같은 공용 패턴
            (`CatalogTable`·`ProjectTable`·`ProjectDatasetTable`). 안내는 1100px 이하에서만
            보인다(`design-system.css` 의 `.table-scroll-hint`) — 규칙을 이 화면에 다시 쓰지 않는다. */}
        <p className="table-scroll-hint">표를 좌우로 밀면 나머지 항목과 작업을 볼 수 있어요.</p>
        <div className="account-table-scroll" role="region" aria-label="계정 목록 표 스크롤" tabIndex={0}>
          <table className="account-table" aria-label="계정 목록">
            <thead>
              <tr>
                <th scope="col">이메일</th><th scope="col">이름</th><th scope="col">역할</th>
                <th scope="col">연구실</th><th scope="col">상태</th><th scope="col">시스템 관리자</th>
                <th scope="col">최근 로그인</th>
                <th scope="col" aria-label="행 동작" />
              </tr>
            </thead>
            <tbody>
              {rows?.map(row => {
                const self = row.accountId === account?.accountId;
                return (
                <tr key={row.accountId}>
                  <td>{row.email}</td>
                  <td>{row.name}</td>
                  <td>{row.role === '교수' ? '교수 관리자' : row.role ?? '없음'}</td>
                  <td>{row.labName ?? '없음'}</td>
                  <td>{STATUS_LABEL[row.status] ?? row.status}</td>
                  <td>{row.operator ? '시스템 관리자' : '아니요'}</td>
                  <td>{day(row.lastLoginAt)}</td>
                  <td className="account-row-actions">
                    {/* 자기 자신 해제는 화면에서 막는다 — 되살릴 사람이 없어지는 자리라
                        서버도 400 을 내지만, 누를 수 있게 두면 그 거절이 사고처럼 보인다.
                        「마지막 한 명」은 화면이 셀 수 없다(목록이 필터로 좁혀져 있을 수 있다) —
                        그 판정은 서버가 하고 화면은 그 문구를 그대로 보여 준다. */}
                    <button type="button" className="btn btn-secondary"
                            disabled={rowBusy || self}
                            onClick={() => setOperatorRow(row)}>
                      {row.operator ? '시스템 관리자 해제' : '시스템 관리자 지정'}
                    </button>
                    <button type="button" className="btn btn-secondary" disabled={rowBusy}
                            onClick={() => setResetRow(row)}>비밀번호 재설정</button>
                    {/* 자기 줄 비활성화도 시스템 관리자 해제와 같은 꼴로 막는다 — 서버가 거절하는 것을
                        눌리게 두면 그 거절이 사고처럼 보인다. 서버 가드(`accounts.py`)는 그대로 둔다. */}
                    <button type="button" className="btn btn-secondary" disabled={rowBusy || self}
                            onClick={() => setStatusRow(row)}>
                      {row.status === 'inactive' ? '재활성화' : '비활성화'}
                    </button>
                    {self ? <span className="account-row-note">{SELF_STATUS_REASON}</span> : null}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {rows && rows.length === 0 ? <p className="account-status" role="status">조건에 맞는 계정이 없어요.</p> : null}
      </section>
      </div>
      {message ? <p className="account-status" role="status">{message}</p> : null}

      {resetRow ? (
        <ResetDialog row={resetRow} busy={rowBusy} onClose={() => setResetRow(null)}
          onConfirm={pw => {
            const target = resetRow;
            void send('/admin/accounts/{accountId}/password-reset', target.accountId,
                      { newPassword: pw }, `${target.email} 의 비밀번호를 재설정했어요.`)
              .then(ok => { if (ok) setResetRow(null); });
          }} />
      ) : null}
      {operatorRow ? (
        <OperatorDialog row={operatorRow} next={!operatorRow.operator} busy={rowBusy}
          onClose={() => setOperatorRow(null)}
          onConfirm={() => {
            const target = operatorRow;
            const next = !target.operator;
            void send('/admin/accounts/{accountId}/operator', target.accountId, { operator: next } as never,
                      next ? `${target.email} 을 시스템 관리자로 지정했어요.` : `${target.email} 의 시스템 관리자 권한을 해제했어요.`)
              .then(ok => { if (ok) setOperatorRow(null); });
          }} />
      ) : null}
      {statusRow ? (
        <StatusDialog row={statusRow} next={statusRow.status === 'inactive' ? 'active' : 'inactive'} busy={rowBusy}
          onClose={() => setStatusRow(null)}
          onConfirm={() => {
            const target = statusRow;
            const next = target.status === 'inactive' ? 'active' : 'inactive';
            void send('/admin/accounts/{accountId}/status', target.accountId, { status: next },
                      next === 'inactive' ? `${target.email} 을 비활성화했어요.` : `${target.email} 을 다시 활성화했어요.`)
              .then(ok => { if (ok) setStatusRow(null); });
          }} />
      ) : null}
    </div>
  );
}

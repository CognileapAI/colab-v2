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

type Row = Schemas['ServiceAccountSummary'];
type Options = Schemas['AccountOptions'];
type Filters = { labId: string; status: string; role: string; email: string };
const EMPTY: Filters = { labId: '', status: '', role: '', email: '' };
const STATUS_LABEL: Record<string, string> = { active: '사용 중', inactive: '비활성' };
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

/** 관리자 지정·해제 확인. 무엇이 달라지는지를 확인 문구보다 먼저 말한다. */
function OperatorDialog(props: { row: Row; next: boolean; busy: boolean; onClose(): void; onConfirm(): void }) {
  const titleId = useId();
  const dialogRef = useDialogFocus(props.onClose, props.busy);
  const title = props.next ? '관리자 지정' : '관리자 해제';
  return (
    <div className="account-modal-back">
      <div ref={dialogRef} tabIndex={-1} className="account-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <h3 id={titleId}>{title}</h3>
        <p className="account-modal-lead">
          <b>{props.row.email}</b> 을(를) {props.next ? '관리자로 지정해요.' : '관리자에서 해제해요.'}
        </p>
        <p className="account-modal-help">
          {props.next
            ? '관리자는 계정을 추가·재설정·비활성화할 수 있고, 모든 연구실의 자료를 읽기 전용으로 볼 수 있어요. 고치거나 지우는 건 자기 연구실에서만 할 수 있어요.'
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

  useWorkProtection('account-admin', {
    dirty, inFlight: busy || rowBusy,
    discard: () => { formRef.current?.reset(); setDirty(false); },
  });

  const load = useCallback(async () => {
    const query: Record<string, string> = {};
    if (filters.labId) query.labId = filters.labId;
    if (filters.status) query.status = filters.status;
    if (filters.role) query.role = filters.role;
    if (filters.email) query.email = filters.email;
    try {
      const { data, error } = await api.GET('/admin/accounts', { params: { query } });
      if (data) { setRows(data.accounts); setListError(null); }
      else setListError(error?.message ?? '계정 목록을 불러오지 못했어요.');
    } catch { setListError('서버에 연결하지 못했어요. 잠시 뒤에 다시 시도해 주세요.'); }
  }, [filters]);

  useEffect(() => {
    if (!operator) return;
    void api.GET('/admin/account-options').then(({ data }) => data && setOptions(data));
  }, [operator]);
  useEffect(() => { if (operator) void load(); }, [operator, load]);

  if (!operator) return <main><h1>계정 관리</h1><p>서비스 운영자만 사용할 수 있어요.</p></main>;

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
    <main className="login">
      <section className="login-card account-card" data-testid="account-create">
        <span className="login-brand">Co-Lab</span>
        <h1 className="login-title">서비스 계정 추가</h1>
        <p className="login-lead">기존 연구실과 역할을 지정하고 초기 비밀번호를 사용자에게 전달하세요.</p>
        <form ref={formRef} className="account-form" onInput={() => setDirty(true)} onSubmit={async e => {
          e.preventDefault();
          if (busy) return;
          setMessage(null);
          const form = e.currentTarget;
          const f = new FormData(form);
          const initialPassword = String(f.get('initialPassword'));
          if (!validNewPassword(initialPassword)) { setMessage('초기 비밀번호는 10~512자로 입력해 주세요.'); return; }
          setBusy(true);
          try {
            const { data, error } = await api.POST('/admin/accounts', { body: {
              email: String(f.get('email')), name: String(f.get('name')),
              labId: String(f.get('labId')), role: String(f.get('role')) as '교수' | '연구원',
              initialPassword,
              // 체크하지 않으면 아예 보내지 않는다 — 서버 기본값(아니다)을 화면이 덮어쓰지 않는다.
              ...(f.get('operator') ? { operator: true } : {}),
            } });
            setMessage(data ? data.email + ' 계정을 추가했어요.' : (error?.message ?? '계정을 추가하지 못했어요.'));
            if (data) { form.reset(); setDirty(false); void load(); }
          } catch { setMessage('서버에 연결하지 못했어요. 계정이 추가됐는지 확인한 뒤 다시 시도해 주세요.'); }
          finally { setBusy(false); }
        }}>
          <label className="login-label">이름<input className="login-input" name="name" required /></label>
          <label className="login-label">이메일<input className="login-input" name="email" type="email" required /></label>
          <label className="login-label">연구실<select className="login-input" name="labId" required>{options?.labs.map(l => <option key={l.labId} value={l.labId}>{l.name}</option>)}</select></label>
          <label className="login-label">역할<select className="login-input" name="role" required>{options?.roles.map(r => <option key={r}>{r}</option>)}</select></label>
          <label className="login-label">초기 비밀번호<input className="login-input" name="initialPassword" aria-describedby="initial-password-help" type="password" required /></label>
          <label className="login-label account-operator-check">
            <input type="checkbox" name="operator" /> 관리자로 등록
          </label>
          <p className="login-label">관리자는 계정을 관리하고 모든 연구실 자료를 읽기 전용으로 볼 수 있어요.</p>
          <p id="initial-password-help" className="login-label">10~512자로 입력하세요. 영문·숫자·특수문자 조합은 필수가 아니에요. 사용자는 첫 로그인 때 비밀번호를 변경해야 해요.</p>
          <button className="login-submit" type="submit" disabled={busy}>{busy ? '추가하는 중…' : '계정 추가'}</button>
        </form>
        {message ? <p className="account-status" role="status">{message}</p> : null}
      </section>

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
              {options?.roles.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>
          <label className="login-label">이메일
            <input className="login-input" type="search" value={filters.email} onChange={pick('email')} />
          </label>
        </fieldset>

        {listError ? <p className="account-status" role="alert">{listError}</p> : null}
        <div className="account-table-scroll">
          <table className="account-table" aria-label="계정 목록">
            <thead>
              <tr>
                <th scope="col">이메일</th><th scope="col">이름</th><th scope="col">역할</th>
                <th scope="col">연구실</th><th scope="col">상태</th><th scope="col">관리자</th>
                <th scope="col">최근 로그인</th>
                <th scope="col" aria-label="행 동작" />
              </tr>
            </thead>
            <tbody>
              {rows?.map(row => (
                <tr key={row.accountId}>
                  <td>{row.email}</td>
                  <td>{row.name}</td>
                  <td>{row.role ?? '없음'}</td>
                  <td>{row.labName}</td>
                  <td>{STATUS_LABEL[row.status] ?? row.status}</td>
                  <td>{row.operator ? '관리자' : '아니요'}</td>
                  <td>{day(row.lastLoginAt)}</td>
                  <td className="account-row-actions">
                    {/* 자기 자신 해제는 화면에서 막는다 — 되살릴 사람이 없어지는 자리라
                        서버도 400 을 내지만, 누를 수 있게 두면 그 거절이 사고처럼 보인다.
                        「마지막 한 명」은 화면이 셀 수 없다(목록이 필터로 좁혀져 있을 수 있다) —
                        그 판정은 서버가 하고 화면은 그 문구를 그대로 보여 준다. */}
                    <button type="button" className="btn btn-secondary"
                            disabled={rowBusy || row.accountId === account?.accountId}
                            onClick={() => setOperatorRow(row)}>
                      {row.operator ? '관리자 해제' : '관리자 지정'}
                    </button>
                    <button type="button" className="btn btn-secondary" disabled={rowBusy}
                            onClick={() => setResetRow(row)}>비밀번호 재설정</button>
                    <button type="button" className="btn btn-secondary" disabled={rowBusy}
                            onClick={() => setStatusRow(row)}>
                      {row.status === 'inactive' ? '재활성화' : '비활성화'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows && rows.length === 0 ? <p className="account-status" role="status">조건에 맞는 계정이 없어요.</p> : null}
      </section>

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
                      next ? `${target.email} 을 관리자로 지정했어요.` : `${target.email} 의 관리자 권한을 해제했어요.`)
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
    </main>
  );
}

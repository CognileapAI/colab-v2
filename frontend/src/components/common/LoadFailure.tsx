// 「못 불러왔다」의 한 자리.
//
// **없는 것과 못 읽은 것을 가른다.** 목록이 비어 보이는 두 이유 — 조건에 맞는 것이 없거나,
// 읽지 못했거나 — 는 사람이 할 일이 다르다. 앞의 것은 조건을 풀고, 뒤의 것은 다시 불러온다.
// 뒤의 것을 앞의 문구로 그리면 사람은 있는 데이터를 없다고 믿고 화면을 떠난다.
//
// 결은 `TodoInbox`(`Policy_홈_대시보드 §9`)에서 왔다 — 문장 하나 + 다시 불러오기 하나.
// 원인을 지어내지 않고, 실패한 요청의 원문(`Failed to fetch` 같은 것)도 그대로 내보내지 않는다.
export function LoadFailure(props: {
  message: string;
  onRetry: () => void;
  /** 시험이 잡는 손잡이. 화면마다 다른 값을 준다 — 어느 구역이 실패했는지가 시험에 남는다. */
  testId: string;
  /** 손잡이 문구. 읽어 오는 자리는 「다시 불러오기」(`TodoInbox` 선례)가 기본이다. */
  retryLabel?: string;
  retryTestId?: string;
}) {
  return (
    <div className="loadfail" role="alert" data-testid={props.testId}>
      <p className="loadfail-msg">{props.message}</p>
      <button
        type="button"
        className="loadfail-retry"
        {...(props.retryTestId ? { 'data-testid': props.retryTestId } : {})}
        onClick={props.onRetry}
      >
        {props.retryLabel ?? '다시 불러오기'}
      </button>
    </div>
  );
}

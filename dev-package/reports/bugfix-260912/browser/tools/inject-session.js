// 세션 주입 — /tmp 에서 읽은 값을 브라우저 localStorage 규약(store.ts SESSION_KEY)으로 심는다.
// 값 자체는 실행 시 stdin 치환으로 들어온다.
(() => {
  const s = __SESSION__;
  localStorage.setItem('colab.browser-session.v1', JSON.stringify({
    token: s.token, sessionId: s.sessionId, expiresAt: s.expiresAt,
    revocationToken: s.revocationToken, epoch: crypto.randomUUID(), suspended: false,
  }));
  return 'ok';
})();

// CloudFront Function (viewer-request) — 기본 동작(웹 버킷 오리진)에만 붙인다. `〈178〉-㉮`
//
// SPA 라우트(확장자 없는 경로)를 /index.html 로 되쓴다. 「오류 응답 403/404 → index.html」 방식은 배포 전역이라
// /api/* 의 진짜 오류 JSON 까지 HTML 로 바꿔 버린다 — 그래서 함수로 한다. /api/* · /previews/* 동작에는
// 이 함수를 붙이지 않는다(방어로 한 번 더 거른다).
function handler(event) {
  var req = event.request;
  var uri = req.uri;
  if (uri.startsWith('/api/') || uri.startsWith('/previews/')) return req;
  var last = uri.split('/').pop();
  if (last.indexOf('.') === -1) req.uri = '/index.html';
  return req;
}

// `tileUrlTemplate` 소비 규약. **템플릿은 불투명 문자열이다** — `〈68〉` 로 렌더에 묶인
// 단명 서명이 실려 있고, 질의부를 떼거나 다시 조립하면 서명이 깨진다
// (`P2-viz-report` 부록 `A-4` — 「치환은 `{z}`·`{x}`·`{y}` 셋뿐이다」).
//
// 그래서 이 파일에는 **치환 함수 하나**만 있다. 파싱도, 캐시 키 만들기도 하지 않는다.

/** `{z}`·`{x}`·`{y}` **셋만** 바꾼다. 나머지 한 글자도 건드리지 않는다. */
export function tileUrl(template: string, z: number, x: number, y: number): string {
  return template
    .replace('{z}', String(z))
    .replace('{x}', String(x))
    .replace('{y}', String(y));
}

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

/**
 * 그릴 이미지 한 장. **계약이 `oneOf` 다**(`〈85〉` · `〈80〉-㉯ 1`) —
 * stage 1 은 단일 이미지(`imageUrl`)를 내고, 타일 갈래는 stage 2 확대 뷰의 자리다.
 * **둘 다 없으면 `undefined`** 다 — 빈 `src` 로 깨진 이미지를 그리지 않는다.
 */
export function resultImageSrc(result: {
  imageUrl?: string;
  tileUrlTemplate?: string;
}): string | undefined {
  if (result.imageUrl) return result.imageUrl;
  if (result.tileUrlTemplate) return tileUrl(result.tileUrlTemplate, 0, 0, 0);
  return undefined;
}

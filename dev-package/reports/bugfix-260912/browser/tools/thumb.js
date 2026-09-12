// #26 실측 — 축소본(`up-thumb-img`)의 DOM 자리와 지도 자리(`.mapcanvas`/`.pv-frame`) 침범 여부.
(() => {
  const thumbs = Array.from(document.querySelectorAll('[data-testid="up-thumb-img"], .th-img'));
  const details = document.querySelector('.up-preview-options') || document.querySelector('details.up-preview-options');
  const frame = document.querySelector('[data-testid="up-preview-slot"]');
  const map = document.querySelector('.mapcanvas');
  return {
    thumbCount: thumbs.length,
    thumbs: thumbs.map((t) => ({
      cls: t.className,
      insideFrame: !!(frame && frame.contains(t)),
      insideMap: !!(map && map.contains(t)),
      insideOptions: !!(details && details.contains(t)),
      rect: t.getBoundingClientRect().toJSON(),
      visible: t.getBoundingClientRect().width > 0,
    })),
    optionsFound: !!details,
    optionsOpen: details ? details.open : null,
    optionsSummary: details ? (details.querySelector('summary') || {}).textContent : null,
    // 대표 그림 고르개 자리의 이미지 수
    imagesInOptions: details ? details.querySelectorAll('img').length : null,
    imagesInFrame: frame ? frame.querySelectorAll('img').length : null,
    mapFound: !!map,
  };
})();

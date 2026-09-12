Array.from(document.querySelectorAll('img')).map((i) => ({
  t: i.getAttribute('data-testid'), cls: i.className,
  src: i.getAttribute('src'), resolved: i.src, w: i.naturalWidth, h: i.naturalHeight,
}));

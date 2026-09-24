// Pure PNG-vs-PNG comparison used by diff.mjs and locked by test/visual-diff.test.ts.
// Spec: dev-package/prd/specs/S-DESIGN-STRUCTURE-P0-20260924.md (verdict = strict).
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

/** Verdict setting: every colour delta and every anti-aliased pixel counts. */
export const STRICT = Object.freeze({threshold: 0, includeAA: true});
/** Reference column only (pixelmatch default threshold). Never used for the verdict. */
export const LENIENT = Object.freeze({threshold: 0.1});

// Non-overlapping area of differently sized images is filled with two colours that
// differ under both settings, so it always counts as difference.
const PAD_A = [255, 0, 255, 255];
const PAD_B = [0, 255, 0, 255];

const asBuffer = (bytes) => Buffer.from(bytes.buffer, bytes.byteOffset, bytes.byteLength);

/** @param {Uint8Array} bytes */
export function decodePng(bytes) {
  const png = PNG.sync.read(asBuffer(bytes));
  return {width: png.width, height: png.height, data: new Uint8Array(png.data.buffer, png.data.byteOffset, png.data.byteLength)};
}

/** @param {{width: number, height: number, data: Uint8Array}} image */
export function encodePng({width, height, data}) {
  const png = new PNG({width, height});
  png.data = asBuffer(data);
  const out = PNG.sync.write(png);
  return new Uint8Array(out.buffer, out.byteOffset, out.byteLength);
}

function padTo(image, width, height, fill) {
  if (image.width === width && image.height === height) return image.data;
  const out = new Uint8Array(width * height * 4);
  for (let i = 0; i < width * height; i++) out.set(fill, i * 4);
  for (let y = 0; y < image.height; y++) {
    out.set(image.data.subarray(y * image.width * 4, (y + 1) * image.width * 4), y * width * 4);
  }
  return out;
}

/**
 * @param {Uint8Array} baselinePng
 * @param {Uint8Array} candidatePng
 */
export function comparePng(baselinePng, candidatePng) {
  const a = decodePng(baselinePng);
  const b = decodePng(candidatePng);
  const sizeMismatch = a.width !== b.width || a.height !== b.height;
  const width = Math.max(a.width, b.width);
  const height = Math.max(a.height, b.height);
  const da = padTo(a, width, height, PAD_A);
  const db = padTo(b, width, height, PAD_B);
  const diff = new Uint8Array(width * height * 4);
  const strict = pixelmatch(da, db, diff, width, height, STRICT);
  const lenient = pixelmatch(da, db, undefined, width, height, LENIENT);
  return {strict, lenient, sizeMismatch, width, height, totalPixels: width * height, diffPng: encodePng({width, height, data: diff})};
}

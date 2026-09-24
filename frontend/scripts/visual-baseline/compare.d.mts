// Type declarations for compare.mjs (frontend-typecheck includes test/, which imports it).
export interface RawImage {
  width: number;
  height: number;
  /** RGBA, 4 bytes per pixel, row-major. */
  data: Uint8Array;
}

export interface CompareResult {
  /** Verdict: pixelmatch threshold 0 · includeAA true. */
  strict: number;
  /** Reference only: pixelmatch threshold 0.1. */
  lenient: number;
  sizeMismatch: boolean;
  /** Compared canvas = max width × max height of the two inputs. */
  width: number;
  height: number;
  totalPixels: number;
  diffPng: Uint8Array;
}

export declare const STRICT: Readonly<{threshold: number; includeAA: boolean}>;
export declare const LENIENT: Readonly<{threshold: number}>;
export declare function decodePng(bytes: Uint8Array): RawImage;
export declare function encodePng(image: RawImage): Uint8Array;
export declare function comparePng(baselinePng: Uint8Array, candidatePng: Uint8Array): CompareResult;

// Type declarations for judge.mjs (frontend-typecheck includes test/, which imports it).
export const METRICS_SCHEMA: 'colab-visual-metrics/1';
export const OCCLUSION_SCENES: string[];
export const MAP_BOUNDARY: number;
export const MIN_TAP: number;
export const MIN_FONT: number;
export const LANES: string[];
export const EXEMPT_METRICS: string[];

export interface Target {
  n: number;
  screen: string;
  selector: string;
  /** L1 · L2a · L2b · L3a · L3b, or — for the regression watch 50–53. */
  lane: string;
  /** Scenes where the target has a box at 390 (widthHidden: at 1024). */
  scenes: string[];
  captureBlind?: boolean;
  widthHidden?: boolean;
  heightOnly?: boolean;
  measure?: 'row';
}

export interface TargetList {
  schema: string;
  laneScenes: Record<string, string[]>;
  targets: Target[];
}

export interface TargetHit {
  /** Element identity within one metrics file (same element under two targets = same id). */
  id: number;
  w: number;
  h: number;
  /** false = display none or zero width/height: 「재지 않음」. */
  box: boolean;
  via: string;
  path: string;
  /** Indexes into the metrics file's exemptList whose selector matches the element. */
  exempt: number[];
}

export interface MapMetrics {
  cellWidth: number | null;
  touchAction: string | null;
  dragAxis: string | null;
  viewportData: Record<string, string>;
  valueState: string | null;
  coverage: {
    imagePct: number | null;
    fourTools: number | null;
    zoomGroup: number | null;
    tools: Record<string, number | null>;
    overlays: unknown[];
  } | null;
}

export interface Metrics {
  schema: string;
  scene: string;
  theme: string;
  viewport: string;
  width: number;
  height: number;
  input: 'touch' | 'mouse';
  exemptList: { metric: string; selector: string }[];
  targets: { n: number; hits: TargetHit[]; error?: string }[] | null;
  smallOther: { count: number; top: unknown[] } | null;
  inputFont: { of: number; small: { path: string; fontSize: number; exempt: number[] }[] } | null;
  overflow: { scrollWidth: number; innerWidth: number; roots: { path: string; right: number; exempt: number[] }[] };
  map: MapMetrics | null;
}

export interface ExemptLine { line: number; metric: string; selector: string; reason: string }
export interface ParsedExempt { lines: ExemptLine[]; errors: { line: number; text: string; why: string }[] }
export function parseExempt(text: string): ParsedExempt;

export interface RedItem {
  metric: string;
  capture: string | null;
  n?: number;
  selector?: string;
  value?: unknown;
  path?: string;
  line?: number;
  why?: string;
  cellWidth?: number;
}

export interface JudgeResult {
  code: 0 | 1 | 78;
  lane: string | null;
  files: number;
  readiness: string[];
  red: RedItem[];
  outsideRed: Record<string, number>;
  unmeasured: number[];
  notMeasured: number;
  captureBlind: number;
  exemptHits: number;
  exemptHoles: ExemptLine[];
  exemptUnused: ExemptLine[];
  smallOther: number;
  recorded: {
    capture: string; cellWidth: number | null; judged: boolean; fourTools: number | null; zoomGroup: number | null;
    tools: Record<string, number | null> | null; touchAction: string | null; dragAxis: string | null; valueState: string | null;
  }[];
}

export function judge(input: { metrics: Metrics[]; targets: TargetList; exempt: ParsedExempt; lane?: string | null }): JudgeResult;

export interface LinksResult {
  code: 0 | 78;
  measuredScenes: string[];
  missing: number[];
  declaredNotDrawn: { n: number; scene: string }[];
  drawnIn: Record<string, string[]>;
}

export function links(input: { metrics: Metrics[]; targets: TargetList }): LinksResult;

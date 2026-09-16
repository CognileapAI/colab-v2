import { cloneElement, type ReactElement } from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import type { DatasetPreviewSource } from '../src/components/datasetpreview/types';

const TEST_FILE_ID = '01JYZ9K7WQ3N8V4M2X6C5B0TF1';

/** 기존 상세 시험을 새 명시 실행 계약으로 세운다. */
export function renderDatasetPreview(
  element: ReactElement<{ source?: DatasetPreviewSource | undefined }>,
) {
  const original = element.props.source;
  if (!original) return render(element);
  const source = withDatasetPreviewFixture(original);
  const rendered = render(cloneElement(element, { source }));
  void waitFor(() => expectEnabled(screen.getByTestId('dt-preview-draw')))
    .then(() => fireEvent.click(screen.getByTestId('dt-preview-draw')));
  return rendered;
}

export function withDatasetPreviewFixture(original: DatasetPreviewSource): DatasetPreviewSource {
  return {
    ...original,
    files: original.files ?? (async () => [{ fileId: TEST_FILE_ID, fileName: 'fixture.nc', renderable: true }]),
    describe: original.describe ?? (async () => ({
      variables: ['fixture'], instants: null,
      default: { variable: 'fixture', instant: null },
    })),
  };
}

export function drawDatasetPreviewWhenReady() {
  void waitFor(() => expectEnabled(screen.getByTestId('dt-preview-draw')))
    .then(() => fireEvent.click(screen.getByTestId('dt-preview-draw')));
}

function expectEnabled(button: HTMLElement) {
  if ((button as HTMLButtonElement).disabled) throw new Error('preview draw is disabled');
}

// R-UPLOAD-PREVIEW 승인 rev2: 읽기 순서 검증. 치수는 실제 브라우저에서 잰다.
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { DatasetDetailPage } from '../src/routes/DatasetDetailPage';
import { fixtureDetailSource } from '../src/components/detail/fixture';
import { fixtureLineageSource } from '../src/components/lineage/graphFixture';
import { DETAIL_SECTIONS } from '../src/components/detail/SectionMenu';
const OPEN_ID = '01JYZ9K7WQ3N8V4M2X6C5B0AA1';
function renderDetail() {
  return render(
    <MemoryRouter initialEntries={[`/datasets/${OPEN_ID}`]}>
      <Routes>
        <Route
          path="/datasets/:datasetId"
          element={
            <DatasetDetailPage
              source={fixtureDetailSource()}
              lineageSource={fixtureLineageSource()}
            />
          }
        />
        <Route path="/datasets" element={<div>카탈로그</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

async function settle() {
  return screen.findByRole('heading', { level: 1, name: '낙동강 유역 강우 (2025)' });
}


function before(a: Element, b: Element) {
  expect(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
}
describe('rev2 상세 정보 읽기 순서', () => {
  it('기본 정보 뒤 설명, 변수 표, 소유/파일 정보가 이어진다', async () => {
    renderDetail(); await settle();
    before(screen.getByTestId('ig-분류'), screen.getByTestId('dh-sum'));
    before(screen.getByTestId('dh-sum'), screen.getByTestId('ig-구성'));
    before(screen.getByTestId('ig-구성'), screen.getByTestId('ig-소유자'));
    before(screen.getByTestId('ig-구성'), screen.getByTestId('ig-파일'));
  });
  it('다운로드/편집 행동은 기본 정보보다 먼저 나타난다', async () => {
    renderDetail(); await settle();
    before(screen.getByTestId('detail-grid-actions'), screen.getByTestId('basic-info'));
  });
  it('기본 정보 다음 계보, 미리보기, 활용으로 읽는다', async () => {
    renderDetail(); await settle();
    before(screen.getByTestId('basic-info'), document.getElementById('sec-lineage')!);
    before(document.getElementById('sec-lineage')!, document.getElementById('sec-preview')!);
    before(document.getElementById('sec-preview')!, document.getElementById('sec-usage')!);
  });
  it('각 구역 메뉴는 화면의 실제 구역으로 연결된다', async () => {
    renderDetail(); await settle();
    for (const s of DETAIL_SECTIONS) {
      expect(document.getElementById(s.id)).not.toBeNull();
      expect(document.querySelector(`a[href="#${s.id}"]`)).not.toBeNull();
    }
  });
});

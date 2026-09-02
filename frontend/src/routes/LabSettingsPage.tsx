// S-07 연구실 설정 — `연구실 정보` / `구성원 · 권한` 두 탭 (IA_사이트맵 §3·§7 · Policy_공통_기반 §2).
// 이 화면 자체가 `연구실 설정` 스위치로 가려진다. 주소를 직접 쳐도 같은 결과여야 하므로(P-11)
// 서버가 403 을 내는 것이 정본이고, 여기 숨김은 UX 다.
//
// 이 파일은 **탭 자리만** 정한다. `구성원 · 권한` 본체는 components/members 가,
// `연구실 정보` 본체는 components/lab/LabInfoPanel 이 든다.
import { useState } from 'react';
import { LabInfoPanel } from '../components/lab/LabInfoPanel';
import type { LabSource } from '../components/lab/labSource';
import { MemberPermissionGrid } from '../components/members/MemberPermissionGrid';
import { livePort, type MembersPort } from '../components/members/port';

type SettingsTab = 'info' | 'member';

export function LabSettingsPage(props: { port?: MembersPort; labSource?: LabSource }) {
  // 첫 탭은 `연구실 정보` 다 — 목업 순서 그대로. 연구실이 무엇인지가 정해져야 누구를 부를지가 정해진다.
  const [tab, setTab] = useState<SettingsTab>('info');
  const port = props.port ?? livePort;

  return (
    <div data-screen="S-07">
      <div className="settabs" role="tablist" aria-label="연구실 설정 탭">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'info'}
          className={`st${tab === 'info' ? ' on' : ''}`}
          onClick={() => setTab('info')}
        >
          연구실 정보
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'member'}
          className={`st${tab === 'member' ? ' on' : ''}`}
          onClick={() => setTab('member')}
        >
          구성원 · 권한
        </button>
      </div>

      {tab === 'info' && <LabInfoPanel source={props.labSource} />}
      {tab === 'member' && <MemberPermissionGrid port={port} />}
    </div>
  );
}

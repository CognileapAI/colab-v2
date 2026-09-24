// Product and visual fixtures use one deterministic CSS entry.
// P2a — 층 순서를 가장 먼저 선언한다(tokens < base < primitives < patterns < screens). 층을 넘는 우선순위는
// 이 선언이 정하고, 같은 층 안의 동률만 아래 import 순서가 정한다.
import './layers.css';
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import './tokens.css';
// P2b — 원소 기본(`@layer base`). 층 선언이 순위를 정하므로 import 자리는 층 안 동률 순서만 정한다.
import './base.css';
import '../components/catalog/catalog.css';
import '../components/detail/detail.css';
import '../components/project/project.css';
import '../components/members/members.css';
import '../components/lab/lab.css';
import '../components/search/search.css';
import '../components/dashboard/dashboard.css';
import '../components/preview/preview.css';
import '../components/lineage/lineage.css';
import '../components/lineage/lineageGraph.css';
import '../components/upload/upload.css';
import '../components/approval/approval.css';
import '../components/common/toast.css';
import '../components/common/variableTable.css';
import '../auth/login.css';
import '../shell/shell.css';

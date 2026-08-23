"""cross-domain 인터페이스. **여기에 도메인 구현이 없다.**

D2·D3·D4·D6·D8 은 서로를 직접 import 하지 않고 이 자리의 타입으로만 말한다
(`gates/config/importlinter.ini` 계약 3). 구현은 소유 도메인에 있고, 조립은 `app` 이 한다.
"""
from .lineage import LineageSummary, LineageSummaryPort
from .access import (DatasetAccess, DatasetAccessPort, DatasetVerification,
                     MemberPermissions)
from .project_link import DatasetProjects, ProjectLinkPort, ProjectUse

__all__ = [
    "LineageSummary", "LineageSummaryPort",
    "DatasetAccess", "DatasetAccessPort", "DatasetVerification", "MemberPermissions",
    "DatasetProjects", "ProjectLinkPort", "ProjectUse",
]

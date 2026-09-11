# IS4 state 복구 승인 packet

## 준비 결과

- 2026-09-11 실제 Cloudflare 읽기 전용 prepare를 실행했다. 종료 78은 실행 실패가 아니라 원격 metadata apply 승인 대기다.
- 빈 0700 bundle에서 import와 scratch refresh-only를 수행했다. 원격 resource apply는 0회다.
- 최종 full plan 판정은 resource 정확히 1건, address `cloudflare_zero_trust_tunnel_cloudflared_config.staging`, action `update`, before와 after 값 동일, sensitivity metadata만 상이했다.
- 승인 후보 plan SHA-256은 `6e752d0dda330d94293601e806c9f3b9b0d8c28ec35580f87d9a93e00d20e53c`다.
- private bundle은 `/tmp/colab-is4-approval-stage12-recovery`에 보존했다. state·saved plan·full JSON·원문 로그는 모두 0600이고, 디렉터리는 0700이다. 최종 dev 배포 후에도 final.tfplan 4917B·위 SHA 불변을 재확인했다. 이는 원격 drift 재검사를 대신하지 않는다. Git·보고서·채팅 첨부로 반입하지 않는다.

## 승인 뒤 한 번의 실행

사용자가 위 hash를 승인한 경우에만 부모가 전달한 private bundle 경로로 아래 형식을 실행한다.

```bash
bash infra/staging/tunnel/rehearse-state-recovery.sh \
  --apply-approved /tmp/colab-is4-approval-stage12-recovery \
  --plan-sha256 6e752d0dda330d94293601e806c9f3b9b0d8c28ec35580f87d9a93e00d20e53c
```

실행기는 bundle 단위 배타 잠금을 먼저 잡고 bundle·state·plan·선언·image digest·provider lock hash를 대조한다. 적용 직전 공개 staging health 200과 독립 refresh-only plan의 remote/state drift 0을 확인한다. saved plan을 다시 full JSON으로 판정하고 정확한 `final.tfplan`만 한 번 적용한다. apply 시도 표식은 원자적으로 먼저 생기며, 성공 여부와 관계없이 재사용할 수 없다. 후속 detailed plan 종료 0과 공개 staging health 200이 literal `No changes`와 서비스 생존 증거다.

## 한계와 rollback

- 승인 대기 중 remote ingress 또는 state가 달라지면 현재 packet은 폐기하고 새 prepare와 새 승인을 받는다.
- provider 또는 네트워크 실패도 같은 plan 자동 재시도로 덮지 않는다.
- apply 전 health가 200이 아니면 apply 0회로 즉시 중단한다. apply 후 health가 200이 아니어도 성공으로 보고하지 않고 즉시 중단·보고한다.
- `terraform state push`는 rollback으로 사용하지 않는다. rollback은 현재 remote를 다시 읽어 별도 plan을 준비하고 독립 검토·hash 승인을 받아야 한다.
- 실제 apply 전까지 IS4를 완료로 닫지 않는다. 이번 packet은 원격 설정 값 변경 0인 metadata 정착 apply 1회의 입력만 고정했다.

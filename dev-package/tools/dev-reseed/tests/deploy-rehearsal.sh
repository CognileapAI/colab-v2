#!/usr/bin/env bash
# Local connection tests only; these do not establish candidate deployment readiness.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../../.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/repo/scripts" "$TMP/run" "$TMP/bin"
export EFFECTS="$TMP/effects"
: > "$EFFECTS"
for tool in ssh scp docker aws; do
  printf '#!/usr/bin/env bash\necho forbidden-%s >> "$EFFECTS"\nexit 99\n' "$tool" > "$TMP/bin/$tool"
done
chmod +x "$TMP/bin/"*
export PATH="$TMP/bin:$PATH"
REPO_ROOT="$ROOT" RUN_DIR="$TMP/run" DRY_RUN=0 STAGE_LOG="$TMP/stage.log"
TARGET_SHA="$(git -C "$ROOT" rev-parse --short=12 HEAD)"
FULL_SHA="$(git -C "$ROOT" rev-parse HEAD)"
CURRENT_STAGE=rehearse RELEASE_PLAN=''
. "$HERE/../lib.sh"
. "$HERE/../stages.sh"
fail=0; cases=0
check() { cases=$((cases+1)); [ "$1" = "$2" ] || { echo "FAIL $3: got=$1 expected=$2"; fail=1; }; }

# No plan must stop before any old remote rehearsal primitive.
( stage_rehearse ) > "$TMP/missing.out" 2>&1; check "$?" 78 missing-plan
check "$(wc -l < "$EFFECTS" | tr -d ' ')" 0 no-remote-without-plan

# Simulated executor success records argv; unlike production --check it does not validate evidence.
cat > "$TMP/repo/scripts/deploy_release.py" <<'PY'
import os, pathlib, sys
assert sys.argv[1:3] == ['run', '--plan'] and sys.argv[4:] == ['--check'], sys.argv
assert pathlib.Path(sys.argv[3]).read_bytes() == pathlib.Path(os.environ['PLAN_INPUT']).read_bytes()
open(os.environ['CHECK_TRACE'], 'a').write('check\n')
raise SystemExit(int(os.environ.get('CHECK_RC','0')))
PY
export CHECK_TRACE="$TMP/check.trace"
# A shallow checkout has no HEAD^. Build both real comparison commits in a local fixture.
wrong_head_repo="$TMP/wrong-head"
git init -q -b fixture "$wrong_head_repo"
git -C "$wrong_head_repo" -c user.name=fixture -c user.email=fixture@invalid -c commit.gpgsign=false commit --allow-empty -qm first
wrong_head_sha="$(git -C "$wrong_head_repo" rev-parse HEAD)"
git -C "$wrong_head_repo" -c user.name=fixture -c user.email=fixture@invalid -c commit.gpgsign=false commit --allow-empty -qm second
for mode in match wrong-sha wrong-env rejected recursive wrong-head; do
  RELEASE_PLAN="$TMP/plan.json"; export PLAN_INPUT="$RELEASE_PLAN"
  fixture_sha="$FULL_SHA"
  comparison_repo="$ROOT"
  if [ "$mode" = wrong-head ]; then
    fixture_sha="$wrong_head_sha"; comparison_repo="$wrong_head_repo"
  fi
  python3 - "$RELEASE_PLAN" "$mode" "$fixture_sha" <<'PY'
import json,sys
p,mode,sha=sys.argv[1:]
target={'name':'st' if mode=='wrong-env' else 'dv', 'version':'b'*40 if mode=='wrong-sha' else sha}
if mode=='recursive': target['deploy']=[['bash','dev-package/tools/dev-reseed/reseed.sh']]
json.dump({'targets':[target]},open(p,'w'))
PY
  : > "$CHECK_TRACE"
  export CHECK_RC=0; [ "$mode" != rejected ] || CHECK_RC=78
  # The root remains a real checkout for candidate resolution; only executor script location is isolated.
  ( REPO_ROOT="$TMP/repo"; TARGET_SHA="$fixture_sha"; git() { command git -C "$comparison_repo" "${@:3}"; }; rehearse_release_plan ) > "$TMP/$mode.out" 2>&1
  rc=$?
  case "$mode" in match) want=0; calls=1 ;; rejected) want=78; calls=1 ;; *) want=1; calls=0 ;; esac
  check "$rc" "$want" "plan-$mode"
  check "$(wc -l < "$CHECK_TRACE" | tr -d ' ')" "$calls" "executor-$mode"
done

# Real executor entrypoint: missing pre-evidence must reject before declared commands run.
python3 - "$TMP/real-plan.json" "$FULL_SHA" "$EFFECTS" <<'PY'
import json,sys
p,sha,effects=sys.argv[1:]
cmd=[sys.executable,'-c',f'open({effects!r},"a").write("DEPLOY\\n")']
json.dump({'schema':'colab-deploy/1','id':'rehearsal-fixture','targets':[{'name':'dv','version':sha,'deploy':[cmd],'verify':[cmd]}]},open(p,'w'))
PY
( cd "$ROOT"; python3 scripts/deploy_release.py run --plan "$TMP/real-plan.json" --check ) > "$TMP/real-check.out" 2>&1
check "$?" 78 real-pre-evidence-refusal
check "$(wc -l < "$EFFECTS" | tr -d ' ')" 0 no-deploy-or-network

# Valid local evidence fixture, using the same registry/collector as release-evidence tests.
# This is synthetic CI evidence, never production authorization. No validator is bypassed.
python3 - "$ROOT" "$TMP/valid" "$EFFECTS" <<'PY'
import importlib.util,json,pathlib,subprocess,sys
root,repo,effects=map(pathlib.Path,sys.argv[1:])
repo.mkdir(); (repo/'marker').write_text('fixture')
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),'-c','user.name=fixture','-c','user.email=fixture@invalid',*args],text=True).strip()
git('init','-q','-b','develop');git('add','marker');git('commit','-qm','fixture')
sha=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');git('update-ref','refs/remotes/origin/develop',sha)
(repo/'scripts').symlink_to(root/'scripts',target_is_directory=True)
spec=importlib.util.spec_from_file_location('fixture_ci',root/'scripts/harness/verify_evidence.py')
ci=importlib.util.module_from_spec(spec);spec.loader.exec_module(ci)
registry=ci.load_registry();bundle=repo/'bundle';bundle.mkdir()
filters={k:'false' for item in registry.values() for k in item['filters']}
needs={item['job']:{'result':'skipped'} for item in registry.values()}
needs.update({k:{'result':'success'} for k in ['changes','repo-hygiene','product-safety']})
for producer in ('repo-hygiene','product-safety'):
    for name,check in registry[producer]['checks'].items():
        folder=bundle/name;folder.mkdir()
        (folder/'evidence.json').write_text(json.dumps({'schema':'colab-ci-check/1','producer':producer,'check':name,'run_id':'1','run_attempt':1,'commit':sha,'tree':tree,'kind':check['kind'],'command':check['command'],'exit':0,'counts':{'green':1,'red_judgment':0,'red_readiness':0}}))
        (folder/'gate-summary.json').write_text(json.dumps({'schema':'colab-gate-summary/1','commit':sha,'tree':tree,'counts':{'green':len(check['gates']),'red_판정':0,'red_준비':0},'gates':[{'name':g,'status':'green','state':'green','exit':0} for g in check['gates']]}))
event={'after':sha,'before':'c'*40}
jobs=ci.collect_ci('1',1,sha,tree,registry,needs,filters,bundle)
evidence=ci.build_ci_evidence('1',1,sha,tree,ci.event_shas('push',event,sha),jobs)
evidence['inputs']={'event_name':'push','event':event,'needs':needs,'filters':filters}
pre={'schema':'colab-release-evidence/1','sha':sha,'environment':'dev','release_id':'fixture','run_id':'1','started_at':'2026-09-15T00:00:00+00:00','pr':{'merged':True,'merge_commit_sha':sha,'base':'develop','number':1},'ci':evidence,'artifact_root':str(bundle)}
(repo/'pre.json').write_text(json.dumps(pre))
cmd=[sys.executable,'-c',f'open({str(effects)!r},"a").write("DEPLOY\\n")']
(repo/'plan.json').write_text(json.dumps({'schema':'colab-deploy/1','id':'fixture','targets':[{'name':'dv','version':sha,'release_evidence':{'pre':'pre.json','post':'post.json'},'deploy':[cmd],'verify':[cmd]}]}))
PY
(
  REPO_ROOT="$TMP/valid" RELEASE_PLAN="$TMP/valid/plan.json"
  TARGET_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
  rehearse_release_plan
) > "$TMP/valid.out" 2>&1
check "$?" 0 real-valid-plan-check
mkdir "$TMP/valid/subdir"
(
  cd "$TMP/valid/subdir"
  REPO_ROOT="$TMP/valid" RELEASE_PLAN=../plan.json
  TARGET_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
  rehearse_release_plan
) > "$TMP/relative.out" 2>&1
check "$?" 0 nonroot-relative-plan
check "$(wc -l < "$EFFECTS" | tr -d ' ')" 0 valid-check-no-command-effects
check "$(find "$TMP/valid/.git" -name deploy-releases | wc -l | tr -d ' ')" 0 valid-check-no-release-state

# Real executor run + emitted post evidence. Only the doctor measurements are stubbed,
# through its existing test injection seam; pre/post validators and executor remain real.
cat > "$TMP/valid/verify-local.py" <<'PYVERIFY'
import json,os,pathlib,shutil,sys
root,case=map(pathlib.Path,sys.argv[1:3]);sys.path.insert(0,str(root))
assert os.environ['COLAB_DEPLOY_MANAGED']=='1'
with (case/'calls').open('a') as f: f.write('verify\n')
if case.name=='post-fail': raise SystemExit(0)
from scripts.tests.test_harness_release_evidence import DoctorEmitterTests
fixture=DoctorEmitterTests();fixture.setUp()
try:
    fixture.pre=json.loads((case/'pre.json').read_text());sha=fixture.pre['sha']
    fixture.pre_path.write_text(json.dumps(fixture.pre))
    for name in ('CURRENT_SHA','CURRENT_FULL_SHA','MAIN_SHA'):
        p=fixture.state/name;p.write_text(p.read_text().replace('a'*40,sha).replace('a'*12,sha[:12]))
    manifest=fixture.source/'OPS_SOURCE_MANIFEST'
    manifest.write_text(manifest.read_text().replace('a'*40,sha).replace('a'*12,sha[:12]))
    assert fixture.emit()==0
    for name in ('post.json','doctor.log'):
        shutil.copyfile(fixture.out/name,case/'artifacts'/name)
finally:
    fixture.doCleanups()
PYVERIFY
python3 - "$ROOT" "$TMP/valid" <<'PYSETUP'
import hashlib,json,pathlib,sys
root,repo=map(pathlib.Path,sys.argv[1:])
for name in ('success','post-fail'):
    case=repo/name;case.mkdir();(case/'artifacts').mkdir(mode=0o700)
    pre=json.loads((repo/'pre.json').read_text());pre['release_id']='fixture-'+name
    (case/'pre.json').write_text(json.dumps(pre))
    deploy=[sys.executable,'-c',f'import os; assert os.environ["COLAB_DEPLOY_MANAGED"]=="1"; open({str(case/"calls")!r},"a").write("deploy\\n")']
    verify=[sys.executable,str(repo/'verify-local.py'),str(root),str(case)]
    plan={'schema':'colab-deploy/1','id':pre['release_id'],'inputs':[{'path':'verify-local.py','sha256':hashlib.sha256((repo/'verify-local.py').read_bytes()).hexdigest()}],
          'targets':[{'name':'dv','version':pre['sha'],'release_evidence':{'pre':name+'/pre.json','post':name+'/artifacts/post.json'},'deploy':[deploy],'verify':[verify]}]}
    (case/'plan.json').write_text(json.dumps(plan))
PYSETUP
for mode in success post-fail; do
  (
    REPO_ROOT="$TMP/valid" RELEASE_PLAN="$TMP/valid/$mode/plan.json"
    TARGET_SHA="$(git -C "$REPO_ROOT" rev-parse HEAD)"
    # Test invocation only: keep production notification policy unchanged.
    python3() {
      if [ "$1" = "$REPO_ROOT/scripts/deploy_release.py" ]; then command python3 "$@" --notification-off;
      else command python3 "$@"; fi
    }
    stage_deploy && echo reached > "$TMP/valid/$mode/reset"
  ) > "$TMP/real-run-$mode.out" 2>&1
  rc=$?; want=0; [ "$mode" != post-fail ] || want=78
  check "$rc" "$want" "real-executor-$mode"
  check "$(tr '\n' ',' < "$TMP/valid/$mode/calls")" 'deploy,verify,' "real-$mode-command-once"
  if [ "$mode" = post-fail ]; then check "$(test -e "$TMP/valid/$mode/reset"; echo $?)" 1 real-post-failure-reset-zero; fi
done
check "$(wc -l < "$EFFECTS" | tr -d ' ')" 0 real-executor-external-zero

# Real stage_deploy must call the executor once, without the former direct deployment path.
cat > "$TMP/repo/scripts/deploy_release.py" <<'PYEXEC'
import hashlib,json,os,pathlib,stat,sys
mode='check' if '--check' in sys.argv else 'run'
p=pathlib.Path(sys.argv[sys.argv.index('--plan')+1])
raw=p.read_bytes()
with open(os.environ['CHECK_TRACE'],'a') as log:
    log.write(json.dumps({'mode':mode,'path':str(p),'hash':hashlib.sha256(raw).hexdigest(),'permissions':stat.S_IMODE(p.stat().st_mode),'directory_permissions':stat.S_IMODE(p.parent.stat().st_mode),'notification_off':'--notification-off' in sys.argv})+'\n')
if mode=='check' and os.environ.get('MUTATE_INPUT')=='1':
    pathlib.Path(os.environ['PLAN_INPUT']).write_text('changed after validation')
raise SystemExit(int(os.environ.get('CHECK_RC' if mode=='check' else 'RUN_RC','0')))
PYEXEC
for mode in success missing check-fail run-fail post-fail busy tamper dry; do
  : > "$CHECK_TRACE"; : > "$TMP/reset"
  RELEASE_PLAN="$TMP/execute-plan.json"; export PLAN_INPUT="$RELEASE_PLAN"
  printf '{"targets":[{"name":"dv","version":"%s"}]}' "$FULL_SHA" > "$RELEASE_PLAN"
  export CHECK_RC=0 RUN_RC=0 MUTATE_INPUT=0
  case "$mode" in
    missing) RELEASE_PLAN='' ;;
    check-fail) CHECK_RC=78 ;;
    run-fail) RUN_RC=1 ;;
    post-fail) RUN_RC=78 ;;
    busy) RUN_RC=75 ;;
    tamper) MUTATE_INPUT=1 ;;
  esac
  (
    REPO_ROOT="$TMP/repo"
    git() { command git -C "$ROOT" "${@:3}"; }
    [ "$mode" != dry ] || DRY_RUN=1
    stage_deploy && echo reset-reached > "$TMP/reset"
  ) > "$TMP/execute-$mode.out" 2>&1
  rc=$?
  case "$mode" in success|tamper|dry) want=0 ;; missing|check-fail|post-fail) want=78 ;; busy) want=75 ;; *) want=1 ;; esac
  check "$rc" "$want" "execute-$mode-code"
  if [ "$want" = 0 ]; then check "$(wc -l < "$TMP/reset" | tr -d ' ')" 1 "execute-$mode-next-stage";
  else check "$(wc -l < "$TMP/reset" | tr -d ' ')" 0 "execute-$mode-reset-zero"; fi
  case "$mode" in missing|dry) expected='' ;; check-fail) expected=check ;; *) expected=check,run ;; esac
  got="$(python3 - "$CHECK_TRACE" <<'PYTRACE'
import json,sys
rows=[json.loads(line) for line in open(sys.argv[1])]
print(','.join(row['mode'] for row in rows))
if rows:
    assert all(row['permissions']==0o600 for row in rows)
    assert all(row['directory_permissions']==0o700 for row in rows)
    assert len({(row['path'],row['hash']) for row in rows})==1
    assert all(row['notification_off'] for row in rows if row['mode']=='run')
PYTRACE
)"; check "$?" 0 "execute-$mode-same-private-snapshot"
  check "$got" "$expected" "execute-$mode-once"
done
check "$(wc -l < "$EFFECTS" | tr -d ' ')" 0 executor-no-direct-transport
check "$(find "$RUN_DIR" -maxdepth 1 -name 'release-plan.*' | wc -l | tr -d ' ')" 0 snapshot-cleanup

# Existing entrypoint fixtures use local repositories and docker/transport stubs.
bash "$ROOT/infra/dev/tests/build-platform.sh" > "$TMP/build.out" 2>&1
rc=$?; check "$rc" 0 real-build-entrypoints
[ "$rc" = 0 ] || cat "$TMP/build.out"
bash "$ROOT/infra/dev/tests/ship-gate.sh" > "$TMP/ship.out" 2>&1
rc=$?; check "$rc" 0 real-ship-entrypoint
[ "$rc" = 0 ] || cat "$TMP/ship.out"
echo "deploy-rehearsal — local cases $cases · external effects $(wc -l < "$EFFECTS" | tr -d ' ') · candidate readiness NOT measured"
[ "$fail" = 0 ]

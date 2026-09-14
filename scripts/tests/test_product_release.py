import hashlib, json, subprocess, sys
import pytest
from scripts.product_release import PreparationError, ReleaseRejected, artifact_redirect_url, authorize_release, bind_release, candidate_from_record, classify_candidate, initialization_mode, load_operator_input, materialize_plan, materialize_reseed_plan, provision_release, select_promotion_run, select_release, verify_check_binding, verify_manifest_binding

SHA={"base":"1"*40,"head":"2"*40,"merge":"3"*40}
def event(**changes):
 value={"action":"closed","repository":{"full_name":"example/repo"},"pull_request":{"number":17,"merged":True,"merge_commit_sha":SHA["merge"],"base":{"ref":"product","sha":SHA["base"],"repo":{"full_name":"example/repo"}},"head":{"ref":"develop","sha":SHA["head"],"repo":{"full_name":"example/repo"}},"merged_by":{"id":42,"type":"User"}}};value["pull_request"].update(changes);return value

def test_select_release_accepts_allowed_human_same_repo_develop_merge():
 assert select_release(event(),"example/repo",{42})=={"sha":SHA["merge"],"pr_number":17,"actor_id":42,"head_sha":SHA["head"],"base_sha":SHA["base"]}

@pytest.mark.parametrize("bad",[{"merged":False},{"merge_commit_sha":None},{"head":{"ref":"feature","sha":SHA["head"],"repo":{"full_name":"example/repo"}}},{"head":{"ref":"develop","sha":SHA["head"],"repo":{"full_name":"fork/repo"}}},{"merged_by":{"id":42,"type":"Bot"}},{"merged_by":{"id":7,"type":"User"}}])
def test_select_release_rejects_ineligible_events(bad):
 with pytest.raises(ReleaseRejected):select_release(event(**bad),"example/repo",{42})

def test_select_release_rejects_push_and_wrong_repository():
 with pytest.raises(ReleaseRejected):select_release({"ref":"refs/heads/product"},"example/repo",{42})
 with pytest.raises(ReleaseRejected):select_release(event(),"other/repo",{42})

def test_api_response_must_match_original_event():
 changed=event(head={"ref":"develop","sha":"4"*40,"repo":{"full_name":"example/repo"}})
 with pytest.raises(ReleaseRejected,match="API"):bind_release(event(),changed,"example/repo",{42},[SHA["base"],SHA["head"]])

def test_merge_parents_and_manifest_digest_bind_release(tmp_path):
 manifest=tmp_path/"manifest.json";manifest.write_text('{"schema":"colab-product-manifest/1","items":[]}');digest=hashlib.sha256(manifest.read_bytes()).hexdigest()
 assert bind_release(event(),event(),"example/repo",{42},[SHA["base"],SHA["head"]],manifest,digest)["manifest_sha256"]==digest
 manifest.write_text("changed")
 with pytest.raises(ReleaseRejected,match="manifest"):bind_release(event(),event(),"example/repo",{42},[SHA["base"],SHA["head"]],manifest,digest)
 with pytest.raises(ReleaseRejected,match="부모"):bind_release(event(),event(),"example/repo",{42},[SHA["head"],SHA["base"]],manifest,digest)

def test_operator_input_requires_refs_and_rejects_inline_secrets(tmp_path):
 p=tmp_path/"operator.json";p.write_text(json.dumps({"schema":"colab-product-operator-input/1","repository":"example/repo","allowed_actor_ids":[42],"environment":"prod","deploy_plan_path":"plan.json","manifest_path":"manifest.json","manifest_sha256":"a"*64,"state_directory":"/var/lib/colab/product-release","host_config_path":"/run/secrets/colab-product-host","github_token_env":"GITHUB_TOKEN","promotion_workflow_id":123,"promotion_workflow_path":".github/workflows/product-promotion.yml","required_checks":[{"name":"ci","app_id":1}]}))
 assert load_operator_input(p)["allowed_actor_ids"]==[42]
 raw=json.loads(p.read_text());raw["password"]="inline";p.write_text(json.dumps(raw))
 with pytest.raises(ReleaseRejected,match="비밀"):load_operator_input(p)

def test_missing_operator_input_is_readiness_failure(tmp_path):
 with pytest.raises(PreparationError):load_operator_input(tmp_path/"missing.json")

def test_check_cli_has_no_state_or_deploy_side_effects(tmp_path):
 e=tmp_path/"event.json";e.write_text(json.dumps(event()));result=subprocess.run([sys.executable,"scripts/product_release.py","--event",str(e),"--config",str(tmp_path/"missing.json"),"--check"],text=True,capture_output=True)
 assert result.returncode==78;assert list(tmp_path.iterdir())==[e]

def test_duplicate_is_skipped_and_stale_or_unrelated_candidate_is_rejected():
 ancestor=lambda older,newer:(older,newer) in {("old","new"),("old","old"),("new","new")}
 assert classify_candidate("old","old",ancestor)=="duplicate"
 assert classify_candidate("old","new",ancestor)=="deploy"
 with pytest.raises(ReleaseRejected,match="낡은"):classify_candidate("new","old",ancestor)
 with pytest.raises(ReleaseRejected,match="관련 없는"):classify_candidate("left","right",ancestor)

def test_deploy_template_is_bound_to_actual_merge_without_mutating_source(tmp_path):
 source=tmp_path/"template.json";source.write_text(json.dumps({"schema":"colab-deploy/1","id":"product","targets":[{"name":"pr","version":"UNBOUND","deploy":[["deploy"]],"verify":[["verify"]]}]}))
 target=tmp_path/"state"/"bound.json";materialize_plan(source,target,{"sha":SHA["merge"],"pr_number":17})
 assert json.loads(source.read_text())["targets"][0]["version"]=="UNBOUND"
 bound=json.loads(target.read_text());assert bound["candidate_sha"]==SHA["merge"];assert bound["targets"][0]["version"]==SHA["merge"]

def test_reseed_template_only_binds_candidate_and_requires_null_placeholder(tmp_path):
 source=tmp_path/"reseed.json";template={"schema":"colab-product-reseed/1","id":"first","environment":"prod","candidate_sha":None,"manifest_sha":"a"*64,"stages":[{"name":"one","argv":["run"]}]};source.write_text(json.dumps(template))
 target=tmp_path/"state"/"initial-reseed-plan.json";materialize_reseed_plan(source,target,SHA["merge"])
 assert json.loads(target.read_text())==dict(template,candidate_sha=SHA["merge"])
 template["candidate_sha"]=SHA["head"];source.write_text(json.dumps(template))
 with pytest.raises(ReleaseRejected,match="null"):materialize_reseed_plan(source,target,SHA["merge"])

def test_actor_type_must_positively_identify_a_user():
 with pytest.raises(ReleaseRejected):
  select_release(event(merged_by={"id":42}),"example/repo",{42})

def cli_fixture(tmp_path, monkeypatch):
 from scripts import product_release as release
 repo=tmp_path/"repo";repo.mkdir()
 def git(*args):
  return subprocess.check_output(["git","-C",str(repo),"-c","user.name=Fixture","-c","user.email=fixture@example.invalid",*args],text=True).strip()
 git("init","-q","-b","product");(repo/"file").write_text("base");manifest=repo/'manifest.json';manifest.write_text('{}')
 workflow=repo/'.github/workflows/product-promotion.yml';workflow.parent.mkdir(parents=True);workflow.write_text('name: protected-promotion\n')
 git("add",".");git("commit","-qm","base");base=git("rev-parse","HEAD")
 git("checkout","-qb","develop");(repo/"file").write_text("head");git("commit","-qam","head");head=git("rev-parse","HEAD")
 git("checkout","-q","product");git("merge","--no-ff","-qm","merge","develop");merge=git("rev-parse","HEAD")
 ev=event();ev['pull_request']['base']['sha']=base;ev['pull_request']['head']['sha']=head;ev['pull_request']['merge_commit_sha']=merge
 event_file=tmp_path/'event.json';event_file.write_text(json.dumps(ev))
 plan=tmp_path/'plan.json';plan.write_text(json.dumps({'schema':'colab-deploy/1','id':'template','targets':[{'name':'pr','version':'UNBOUND','deploy':[['true']],'verify':[['true']]}]}))
 host=tmp_path/'host.json';host.write_text('{}')
 config=tmp_path/'operator.json';config.write_text(json.dumps({'schema':'colab-product-operator-input/1','repository':'example/repo','allowed_actor_ids':[42],'environment':'prod','deploy_plan_path':str(plan),'manifest_path':'manifest.json','manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'state_directory':str(tmp_path/'state'),'host_config_path':str(host),'github_token_env':'FIXTURE_TOKEN','promotion_workflow_id':123,'promotion_workflow_path':'.github/workflows/product-promotion.yml','required_checks':[{'name':'ci','app_id':1}]}))
 policy=json.loads(config.read_text());policy['promotion_workflow_sha256']=hashlib.sha256(workflow.read_bytes()).hexdigest();config.write_text(json.dumps(policy))
 monkeypatch.chdir(repo);monkeypatch.setenv('FIXTURE_TOKEN','fixture')
 monkeypatch.setattr(release,'fetch_pr',lambda *args:ev)
 promotion={'schema':'colab-product-promotion/1','pr_number':17,'base_sha':base,'head_sha':head,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'required_checks':[{'name':'ci','app_id':1}],'check_sha':merge}
 monkeypatch.setattr(release,'fetch_promotion_approval',lambda *args:promotion)
 monkeypatch.setattr(release,'fetch_commit_parents',lambda *args:[base,head])
 monkeypatch.setattr(release,'fetch_checks',lambda *args:[{'name':'ci','head_sha':merge,'status':'completed','conclusion':'success','app':{'id':1}}])
 return release,git,event_file,config,plan,tmp_path/'state'

def test_valid_check_checks_pinned_checkout_without_creating_state(tmp_path,monkeypatch):
 release,git,ev,config,plan,state=cli_fixture(tmp_path,monkeypatch)
 assert release.cli(['--event',str(ev),'--config',str(config),'--check'])==0
 assert not state.exists()

def test_wrong_checkout_cannot_validate_pinned_release(tmp_path,monkeypatch):
 release,git,ev,config,plan,state=cli_fixture(tmp_path,monkeypatch)
 git('checkout','-q','develop')
 assert release.cli(['--event',str(ev),'--config',str(config),'--check'])==1
 assert not state.exists()

def test_check_rejects_invalid_deployment_template(tmp_path,monkeypatch):
 release,git,ev,config,plan,state=cli_fixture(tmp_path,monkeypatch)
 plan.write_text('{"schema":"invalid"}')
 assert release.cli(['--event',str(ev),'--config',str(config),'--check'])==1
 assert not state.exists()

def approval():return {'schema':'colab-product-promotion/1','pr_number':17,'base_sha':SHA['base'],'head_sha':SHA['head'],'manifest_sha256':'a'*64,'required_checks':[{'name':'ci','app_id':1}],'check_sha':'c'*40}

def test_absent_release_record_never_auto_starts(tmp_path):
 with pytest.raises(PreparationError,match='등록'):authorize_release(tmp_path,{'pr_number':17,'base_sha':SHA['base'],'head_sha':SHA['head'],'sha':SHA['merge'],'manifest_sha256':'a'*64},approval(),False)
 assert list(tmp_path.iterdir())==[]

def test_explicit_provision_is_private_and_binds_one_initial_pr(tmp_path):
 provision_release(tmp_path,approval(),17)
 record=json.loads((tmp_path/'release.json').read_text());assert record['status']=='ready';assert record['initial_reseed_pr_number']==17;assert (tmp_path/'release.json').stat().st_mode & 0o777==0o600
 with pytest.raises(ReleaseRejected):provision_release(tmp_path,dict(approval(),head_sha='c'*40),17)

def test_authorization_rechecks_promotion_binding_and_requires_human_resume(tmp_path):
 provision_release(tmp_path,approval(),17);bound={'pr_number':17,'base_sha':SHA['base'],'head_sha':SHA['head'],'sha':SHA['merge'],'manifest_sha256':'a'*64}
 assert authorize_release(tmp_path,bound,approval(),False)['initial_reseed_pr_number']==17
 path=tmp_path/'release.json';record=json.loads(path.read_text());record['status']='failed';path.write_text(json.dumps(record))
 with pytest.raises(ReleaseRejected,match='재개'):authorize_release(tmp_path,bound,approval(),False)
 assert authorize_release(tmp_path,bound,approval(),True)['status']=='failed'
 record['status']='running';path.write_text(json.dumps(record));assert authorize_release(tmp_path,bound,approval(),True)['status']=='running'
 with pytest.raises(ReleaseRejected,match='승격'):authorize_release(tmp_path,dict(bound,head_sha='c'*40),approval(),True)

def test_promotion_run_selection_requires_exact_workflow_pr_head_and_success():
 good={'id':99,'workflow_id':123,'path':'.github/workflows/product-promotion.yml@refs/pull/17/merge','event':'pull_request','status':'completed','conclusion':'success','head_sha':SHA['head'],'pull_requests':[{'number':17}]}
 assert select_promotion_run([good],123,'.github/workflows/product-promotion.yml',17,SHA['head'])['id']==99
 for change in ({'workflow_id':124},{'path':'.github/workflows/other.yml@x'},{'event':'push'},{'conclusion':'failure'},{'head_sha':'4'*40},{'pull_requests':[{'number':18}]}):
  with pytest.raises(ReleaseRejected,match='promotion'):select_promotion_run([dict(good,**change)],123,'.github/workflows/product-promotion.yml',17,SHA['head'])
 newer=dict(good,id=100);assert select_promotion_run([good,newer],123,'.github/workflows/product-promotion.yml',17,SHA['head'])['id']==100

def test_initial_reseed_is_only_for_provisioned_pr_and_never_for_later_release():
 record={'initial_reseed':'ready','initial_reseed_pr_number':17}
 assert initialization_mode(record,17)=='initial'
 with pytest.raises(ReleaseRejected,match='최초'):initialization_mode(record,18)
 record['initial_reseed']='succeeded'
 assert initialization_mode(record,18)=='normal'

def test_manifest_binding_reads_exact_head_blob_and_merge_file(tmp_path):
 repo=tmp_path/'repo';repo.mkdir();subprocess.run(['git','-C',str(repo),'init','-q'],check=True);(repo/'manifest.json').write_text('{"reset":1}');subprocess.run(['git','-C',str(repo),'-c','user.name=T','-c','user.email=t@x','add','manifest.json'],check=True);subprocess.run(['git','-C',str(repo),'-c','user.name=T','-c','user.email=t@x','commit','-qm','m'],check=True);sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();digest=hashlib.sha256((repo/'manifest.json').read_bytes()).hexdigest()
 assert verify_manifest_binding(repo,sha,'manifest.json',digest)==repo/'manifest.json'
 (repo/'manifest.json').write_text('changed')
 with pytest.raises(ReleaseRejected,match='manifest'):verify_manifest_binding(repo,sha,'manifest.json',digest)
 with pytest.raises(ReleaseRejected,match='경로'):verify_manifest_binding(repo,sha,'../outside',digest)

def test_release_record_is_only_candidate_order_source_and_missing_is_rejected():
 assert candidate_from_record({'status':'verified','latest_sha':SHA['merge']})==SHA['merge']
 for record in ({'status':'verified'},{'status':'verified','latest_sha':'bad'},{'status':'mystery','latest_sha':SHA['merge']}):
  with pytest.raises(PreparationError):candidate_from_record(record)

def test_artifact_redirect_only_allows_unsigned_github_blob_download():
 assert artifact_redirect_url('https://productionresultssa1.blob.core.windows.net/a')=='https://productionresultssa1.blob.core.windows.net/a'
 for url in ('http://productionresultssa1.blob.core.windows.net/a','https://evil.example/a','https://blob.core.windows.net.evil.example/a'):
  with pytest.raises(ReleaseRejected,match='redirect'):artifact_redirect_url(url)


def test_check_suite_sha_parents_bind_exact_pr_base_and_head():
 approval={'base_sha':SHA['base'],'head_sha':SHA['head']}
 assert verify_check_binding(approval,[SHA['base'],SHA['head']])
 with pytest.raises(ReleaseRejected,match='check SHA'):
  verify_check_binding(approval,[SHA['base'],'f'*40])


def test_premerge_check_sha_can_differ_from_actual_human_merge(tmp_path, monkeypatch):
 release,git,ev,config,plan,state=cli_fixture(tmp_path,monkeypatch)
 previous=release.fetch_promotion_approval()
 check=dict(previous,check_sha='e'*40)
 monkeypatch.setattr(release,'fetch_promotion_approval',lambda *args:check)
 monkeypatch.setattr(release,'fetch_checks',lambda *args:[{'name':'ci','head_sha':'e'*40,'status':'completed','conclusion':'success','app':{'id':1}}])
 assert release.cli(['--event',str(ev),'--config',str(config),'--check'])==0
 assert not state.exists()


def test_wrong_promotion_workflow_policy_digest_blocks_release(tmp_path, monkeypatch):
 release,git,ev,config,plan,state=cli_fixture(tmp_path,monkeypatch)
 value=json.loads(config.read_text());value['promotion_workflow_sha256']='0'*64;config.write_text(json.dumps(value))
 assert release.cli(['--event',str(ev),'--config',str(config),'--check'])==1
 assert not state.exists()

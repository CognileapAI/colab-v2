import datetime as dt
from pathlib import Path
import tempfile
import unittest
from infra.notifications.archive import Archive
from infra.notifications.delivery import FileStore,process
from infra.notifications.digest import build
from infra.notifications import jobs

NOW=dt.datetime(2026,9,12,0,tzinfo=dt.timezone.utc)
def collection(labs=('lab-1',),status='complete'):
    return {'status':status,'labs':[{'id':lab,'name':lab} for lab in labs],
            'sources':[{'lab_id':lab,'source':source,'status':'complete','pending':0} for lab in labs for source in ('d2','d3','d5','d6','d8')],
            'collected_at':NOW.isoformat()}
def manifest():
    return {'environment':'dev','usage':'live','coverage_started_at':'2026-09-11T00:00:00+09:00',
            'test_exclusions':{'lab_ids':[],'account_ids':[],'effective_at':'2026-09-11T00:00:00+09:00'},
            'sources':['d2','d3','d5','d6','d8'],'collection':collection()}
def audit(source,action='project.deleted',**extra):
    return {'source_id':source,'lab_id':'lab-1','actor_id':'actor-1','target_id':'target-1',
            'action':action,'occurred_at':'2026-09-11T01:00:00+00:00',**extra}

class DigestRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.archive=Archive(Path(self.tmp.name)/'archive');self.store=FileStore(Path(self.tmp.name)/'delivery')
        self.manifest=manifest()
    def test_restart_after_generation_replays_identical_outbox(self):
        first=jobs.run(NOW,self.manifest,self.archive)
        restarted=Archive(Path(self.tmp.name)/'archive')
        second=jobs.run(NOW,self.manifest,restarted)
        self.assertEqual(first,second);self.assertTrue(first)
        self.assertFalse(restarted.snapshot()['reports']['2026-09-11']['complete'])
        jobs.publish(second,self.manifest,restarted,self.store)
        posts=[]
        for index,event_id in enumerate(self.store.due(NOW)):
            process(event_id,self.store,lambda c,t:(posts.append(t) or (200,'ok',None)),NOW+dt.timedelta(seconds=index*2))
        jobs.reconcile(restarted,self.store)
        self.assertEqual(jobs.run(NOW,self.manifest,restarted),[])
        self.assertEqual(len(posts),len(first))
    def test_partial_store_failure_replays_without_replacing_first_part(self):
        self.archive.accept(audit('long-audit',before={'label':'X'*7000}))
        parts=jobs.run(NOW,self.manifest,self.archive)
        original=self.store.put;calls=[]
        def fail_second(record):
            calls.append(record)
            if len(calls)==2:raise OSError('simulated disk failure')
            return original(record)
        self.store.put=fail_second
        with self.assertRaises(OSError):jobs.publish(parts,self.manifest,self.archive,self.store)
        self.store.put=original
        replay=jobs.run(NOW,self.manifest,self.archive)
        self.assertEqual(parts,replay);jobs.publish(replay,self.manifest,self.archive,self.store)
        self.assertEqual(len(self.store.due(NOW)),len(parts))
    def test_collection_missing_failed_and_no_targets_are_distinct(self):
        for metadata,expected in [(None,'집계 불완전'),(collection(status='failed'),'전체 수집 실패'),(collection(labs=()),'대상 연구실 0개')]:
            with tempfile.TemporaryDirectory() as folder:
                m=manifest();m['collection']=metadata
                body='\n'.join(p['text'] for p in build('2026-09-11',m,Archive(Path(folder))))
                self.assertIn(expected,body);self.assertNotIn('상태: 활동 없음',body)
    def test_upload_registration_deduplicated_by_upload_id(self):
        self.archive.accept(audit('accepted','upload.accepted',target_id='upload-1',upload_id='upload-1'))
        self.archive.accept(audit('registered','dataset.registered',target_id='dataset-1',upload_id='upload-1'))
        body='\n'.join(p['text'] for p in build('2026-09-11',self.manifest,self.archive))
        self.assertIn('활동 1',body);self.assertIn('등록 1건',body)
    def test_late_commit_creates_revision_after_initial_delivery(self):
        first=jobs.run(NOW,self.manifest,self.archive);jobs.publish(first,self.manifest,self.archive,self.store)
        for index,event_id in enumerate(self.store.due(NOW)):
            process(event_id,self.store,lambda *x:(200,'ok',None),NOW+dt.timedelta(seconds=index*2))
        jobs.reconcile(self.archive,self.store)
        self.archive.accept(audit('late-commit',before={'name':'deleted-late'}))
        revised=jobs.run(NOW,self.manifest,self.archive)
        self.assertTrue(revised);self.assertEqual(revised[0]['revision'],2)
        self.assertIn('정정 보고',revised[0]['text'])
        self.assertIn('deleted-late','\n'.join(p['text'] for p in revised))
class DynamoDigestTests(unittest.TestCase):
    def setUp(self):
        from scripts.tests.test_operator_aws_runtime import DynamoSDK
        from infra.notifications.aws_store import DynamoStore,DynamoArchive
        self.sdk=DynamoSDK();self.store=DynamoStore(self.sdk,'report-table');self.archive=DynamoArchive(self.store)
        self.manifest=manifest();self.archive.record_collection(self.manifest.pop('collection'))
    def test_durable_remote_outbox_replays_after_restart(self):
        from infra.notifications.aws_store import DynamoArchive
        first=jobs.run(NOW,self.manifest,self.archive)
        restarted=DynamoArchive(self.store)
        self.assertEqual(first,jobs.run(NOW,self.manifest,restarted))
        jobs.publish(first,self.manifest,restarted,self.store)
        for index,event_id in enumerate(self.store.due(NOW)):
            process(event_id,self.store,lambda *x:(200,'ok',None),NOW+dt.timedelta(seconds=index*2))
        jobs.reconcile(restarted,self.store)
        self.assertEqual(jobs.run(NOW,self.manifest,restarted),[])
    def test_late_arrival_fences_stale_report_and_retry_recovers(self):
        from infra.notifications.aws_store import ConcurrentWrite
        self.archive.accept(audit('initial'))
        self.archive.snapshot()
        self.store.accept_archive(audit('arrived-during-render'))
        with self.assertRaises(ConcurrentWrite):build('2026-09-11',self.manifest,self.archive)
        parts=build('2026-09-11',self.manifest,self.archive)
        self.assertTrue(parts);self.assertIn('활동 2',parts[0]['text'])
    def test_large_report_parts_are_separate_durable_items(self):
        for index in range(150):self.archive.accept(audit('large-'+str(index),before={'label':'Z'*3000}))
        parts=build('2026-09-11',self.manifest,self.archive)
        self.assertGreater(len(parts),100)
        packed=self.sdk.items['report#2026-09-11']['body']['S']
        self.assertLess(len(packed.encode()),350000)
        self.assertEqual(sum(p['text'].count('Z') for p in parts),450000)

if __name__=='__main__':unittest.main()

class CollectionRecoveryTests(unittest.TestCase):
    def test_post_midnight_collection_corrects_already_sent_incomplete_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Archive(Path(tmp)/'archive');store=FileStore(Path(tmp)/'store')
            m=manifest();m.pop('collection')
            before=collection();before['collected_at']='2026-09-11T14:59:59+00:00'
            archive.record_collection(before)
            first=jobs.run(NOW,m,archive);jobs.publish(first,m,archive,store)
            for i,identity in enumerate(store.due(NOW)):
                process(identity,store,lambda *a:(200,'ok',None),NOW+dt.timedelta(seconds=i*2))
            jobs.reconcile(archive,store)
            self.assertIn('날짜 마감 이후 수집 확인 없음',first[0]['text'])
            archive.record_collection(collection())
            corrected=jobs.run(NOW,m,archive)
            self.assertTrue(corrected)
            self.assertEqual(corrected[0]['revision'],2)
            self.assertIn('활동 없음',corrected[0]['text'])
            jobs.publish(corrected,m,archive,store)
            for i,identity in enumerate(store.due(NOW+dt.timedelta(minutes=1))):
                process(identity,store,lambda *a:(200,'ok',None),NOW+dt.timedelta(minutes=1,seconds=i*2))
            jobs.reconcile(archive,store)
            later=collection();later['collected_at']=(NOW+dt.timedelta(minutes=2)).isoformat()
            archive.record_collection(later)
            self.assertEqual(jobs.run(NOW+dt.timedelta(minutes=2),m,archive),[])

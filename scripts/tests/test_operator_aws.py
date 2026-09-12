import copy
import http.server
import json
import re
import threading
import unittest
from pathlib import Path
from infra.notifications.aws_events import normalize
from infra.notifications import handlers
from infra.notifications.http_sender import HttpSender
from scripts.tests.test_operator_aws_runtime import CONFIG, NOW, DynamoSDK


ROOT = Path(__file__).resolve().parents[2]


def health():
    return {'id':'transport-copy-one','account':'123456789012','region':'us-east-1','source':'aws.health',
        'detail-type':'AWS Health Event','time':'2026-09-12T00:00:00Z',
        'detail':{'eventArn':'arn:aws:health:ap-northeast-2::event/RDS/issue/one','statusCode':'open',
            'service':'RDS','eventRegion':'ap-northeast-2','eventTypeCategory':'issue',
            'eventScopeCode':'PUBLIC','lastUpdatedTime':'Sat, 12 Sep 2026 00:00:00 GMT',
            'startTime':'Sat, 12 Sep 2026 00:00:00 GMT','page':'1','totalPages':'2'}}


class AwsTests(unittest.TestCase):
    def test_cloud_event_survives_application_shutdown(self):
        posts={'development':[],'activity':[]}; endpoints={}; servers=[]
        for channel in posts:
            def handler_for(label):
                class Handler(http.server.BaseHTTPRequestHandler):
                    def do_POST(self):
                        posts[label].append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                        self.send_response(200);self.end_headers();self.wfile.write(b'ok')
                    def log_message(self,*args):pass
                return Handler
            server=http.server.HTTPServer(('127.0.0.1',0),handler_for(channel));servers.append(server)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
            endpoints[channel]='http://127.0.0.1:'+str(server.server_port)+'/hook'
        sender=HttpSender(endpoints,local_only=True); sdk=DynamoSDK()
        message={'Records':[{'messageId':'aws-message','eventSourceARN':'arn:queue:dev','body':json.dumps(health())}]}
        for _ in range(2):
            result=handlers.consume(message,None,client=sdk,sender=sender,config=CONFIG,now=NOW)
            self.assertEqual(result,{'batchItemFailures':[]})
        self.assertEqual(len(posts['development']),1);self.assertEqual(posts['activity'],[])

    def test_health_close_and_alarm_are_normalized(self):
        raw=health();raw['detail']['statusCode']='closed'
        result=normalize(raw,CONFIG['manifest'])[0]
        self.assertEqual(result['payload']['kind'],'aws.health.closed')
        self.assertIn('앱 복구',result['payload']['status'])
        alarm={'account':'123456789012','region':'ap-northeast-2','source':'aws.cloudwatch',
               'detail':{'alarmName':'core-status','state':{'value':'INSUFFICIENT_DATA','timestamp':NOW.isoformat()}}}
        self.assertEqual(normalize(alarm,CONFIG['manifest'])[0]['payload']['status'],'관측 불가')
        alarm['detail']['state']['value']='OK'
        self.assertNotIn('회복',normalize(alarm,CONFIG['manifest'])[0]['payload']['status'])
        alarm['detail']['previousState']={'value':'ALARM'}
        self.assertIn('회복',normalize(alarm,CONFIG['manifest'])[0]['payload']['status'])

    def test_wrong_account_is_rejected(self):
        raw=health();raw['account']='wrong'
        with self.assertRaises(ValueError):normalize(raw,CONFIG['manifest'])

    def test_split_delivery_and_cross_region_duplicates_have_stable_identity(self):
        first=health();second=copy.deepcopy(first);second.update(id='another-transport',region='ap-northeast-2')
        second['detail']['page']='2'
        one,two=normalize(first,CONFIG['manifest'])[0],normalize(second,CONFIG['manifest'])[0]
        self.assertEqual(one['event_id'],two['event_id'])
        self.assertEqual(one['payload'],two['payload'])

    def test_unrelated_resource_ignored_and_scheduled_change_keeps_time(self):
        raw=health();raw['detail'].update(eventScopeCode='ACCOUNT_SPECIFIC',affectedEntities=[{'entityValue':'unknown'}])
        self.assertEqual(normalize(raw,CONFIG['manifest']),[])
        raw['detail'].update(affectedEntities=[{'entityValue':'i-core'}],eventTypeCategory='scheduledChange',statusCode='upcoming')
        event=normalize(raw,CONFIG['manifest'])[0]
        self.assertEqual(event['payload']['kind'],'aws.health.scheduled')
        self.assertEqual(event['payload']['scheduled_at'],NOW.isoformat())


class TemplateBoundaryTests(unittest.TestCase):
    def test_runtime_roles_have_fixed_names_and_permissions_boundary(self):
        template = (ROOT / 'infra/notifications/template.yaml').read_text()
        expected = {
            'ConsumerRole': 'colab-notify-20260912-consumer',
            'RetryRole': 'colab-notify-20260912-retry',
            'IngestRole': 'colab-notify-20260912-ingest',
        }
        self.assertIn('PermissionsBoundaryArn:', template)
        self.assertIn(
            'Default: arn:aws:iam::606175197146:policy/colab-notifications-runtime-boundary',
            template,
        )
        for logical_id, role_name in expected.items():
            block = re.search(
                rf'^  {logical_id}:\n(?P<body>.*?)(?=^  \S|\Z)',
                template,
                re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(block, logical_id)
            self.assertIn(f'RoleName: {role_name}', block.group('body'))
            self.assertIn('PermissionsBoundary: !Ref PermissionsBoundaryArn', block.group('body'))
        for function, role in {
            'ConsumerFunction': 'ConsumerRole',
            'RetryFunction': 'RetryRole',
            'IngestFunction': 'IngestRole',
        }.items():
            block = re.search(
                rf'^  {function}:\n(?P<body>.*?)(?=^  \S|\Z)',
                template,
                re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(block, function)
            self.assertIn(f'Role: !GetAtt {role}.Arn', block.group('body'))

    def test_health_forward_role_has_fixed_name_and_permissions_boundary(self):
        template = (ROOT / 'infra/notifications/health-global.template.yaml').read_text()
        self.assertIn('PermissionsBoundaryArn:', template)
        self.assertIn('RoleName: colab-notify-20260912-health-forward', template)
        self.assertIn('PermissionsBoundary: !Ref PermissionsBoundaryArn', template)

if __name__=='__main__':unittest.main()

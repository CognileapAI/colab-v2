import datetime as dt
import unittest

class ProducerTests(unittest.TestCase):
    def test_retry_does_not_deploy_again(self):
        from scripts.tests.operator_notifications_support import run_case
        result=run_case("st_verification_failed_then_delivery_retry")
        self.assertEqual(result["deploy_count"],1)
        self.assertEqual(result["success_messages"],[])
        self.assertEqual(result["failure_event_ids"],[result["expected_id"]])

    def test_probe_requires_two_failures_and_recovers_once(self):
        from infra.notifications.producers import observe
        now=dt.datetime(2026,9,12,tzinfo=dt.timezone.utc);state={}
        state,e1=observe(state,False,"dev","core",now)
        state,e2=observe(state,False,"dev","core",now)
        state,e3=observe(state,False,"dev","core",now)
        state,e4=observe(state,True,"dev","core",now)
        state,e5=observe(state,True,"dev","core",now)
        self.assertEqual([len(x) for x in (e1,e2,e3,e4,e5)],[0,1,0,1,0])

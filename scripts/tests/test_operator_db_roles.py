"""Real PostgreSQL permission tests, in an unexposed disposable container."""
from pathlib import Path
import subprocess
import time
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[2]
LAB1='00000000000000000000000001'
LAB2='00000000000000000000000002'
REPORTER='colab_operator_reporter'
EXPORTER='colab_operator_exporter'

class OperatorRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.container='colab_operator_roles_'+uuid.uuid4().hex[:12]
        subprocess.run(['docker','run','-d','--rm','--name',cls.container,
            '--tmpfs','/var/lib/postgresql/data','-e','POSTGRES_HOST_AUTH_METHOD=trust','postgres:16-alpine'],
            check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        cls.addClassCleanup(lambda:subprocess.run(['docker','rm','-f',cls.container],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
        for _ in range(100):
            probe=subprocess.run(['docker','exec',cls.container,'pg_isready','-h','127.0.0.1','-U','postgres'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if probe.returncode==0:break
            time.sleep(.1)
        else:raise RuntimeError('disposable role test PostgreSQL was not ready')
        cls.sql((ROOT/'db/platform/schema.sql').read_text(),check=True)
        cls.sql('REVOKE CREATE ON SCHEMA public FROM PUBLIC;',check=True)
        cls.sql((ROOT/'services/core-api/ops/operator-roles.sql').read_text(),check=True)
        cls.sql(f"""
            INSERT INTO d1_lab(id,name,opened_at) VALUES ('{LAB1}','Lab One',now()),('{LAB2}','Lab Two',now());
            INSERT INTO d1_account(id,lab_id,name,email) VALUES
              ('00000000000000000000000011','{LAB1}','Actor One','one@example.invalid'),
              ('00000000000000000000000012','{LAB2}','Actor Two','two@example.invalid');
            INSERT INTO d2_operator_audit(id,source_id,lab_id,actor_id,target_id,action) VALUES
              ('00000000000000000000000021','00000000000000000000000031','{LAB1}','00000000000000000000000011','00000000000000000000000011','permission.changed'),
              ('00000000000000000000000022','00000000000000000000000032','{LAB2}','00000000000000000000000012','00000000000000000000000012','permission.changed');
            INSERT INTO d2_operator_export(id,source_id,lab_id,occurred_at,payload) VALUES
              ('00000000000000000000000041','00000000000000000000000031','{LAB1}',now(),'{{}}'),
              ('00000000000000000000000042','00000000000000000000000032','{LAB2}',now(),'{{}}');
        """,check=True)

    @classmethod
    def sql(cls,query,check=False):
        result=subprocess.run(['docker','exec','-i',cls.container,'psql','-X','-A','-t','-v','ON_ERROR_STOP=1','-U','postgres','-d','postgres'],
                              input=query,text=True,capture_output=True)
        if check and result.returncode:raise AssertionError(result.stderr)
        return result

    def scoped(self,role,query,lab=LAB1):
        return self.sql(f"SET ROLE {role}; BEGIN; SET LOCAL app.current_lab='{lab}'; {query}; COMMIT;")

    def test_permission_groups_are_not_logins_or_privileged(self):
        result=self.sql(f"SELECT count(*) FROM pg_roles WHERE rolname IN ('{REPORTER}','{EXPORTER}') AND NOT(rolcanlogin OR rolsuper OR rolbypassrls OR rolcreatedb OR rolcreaterole OR rolreplication);")
        self.assertEqual(result.stdout.strip(),'2')
        self.assertEqual(self.sql((ROOT/'services/core-api/ops/operator-roles.sql').read_text()).returncode,0)

    def test_reporter_scoped_read_and_no_scope_do_not_cross_labs(self):
        result=self.scoped(REPORTER,'SELECT count(*) FROM d2_operator_audit')
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('\n1\n',result.stdout)
        result=self.scoped(REPORTER,f"SELECT count(*) FROM d2_operator_audit WHERE lab_id='{LAB2}'")
        self.assertIn('\n0\n',result.stdout)
        result=self.sql(f'SET ROLE {REPORTER}; SELECT count(*) FROM d2_operator_audit;')
        self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(result.stdout.strip().endswith('0'))
        result=self.sql(f'SET ROLE {REPORTER}; SELECT count(id) FROM d1_lab;')
        self.assertTrue(result.stdout.strip().endswith('2'))

    def test_reporter_cannot_write_or_read_email_or_business_data(self):
        for query in ["UPDATE d2_operator_export SET receipt_hash=repeat('0',64),received_at=now()",
                      'SELECT email FROM d1_account','SELECT * FROM d3_dataset','CREATE TABLE forbidden(id int)']:
            result=self.scoped(REPORTER,query)
            self.assertNotEqual(result.returncode,0,query);self.assertIn('permission denied',result.stderr)

    def test_exporter_can_ack_only_receipt_columns(self):
        result=self.scoped(EXPORTER,"UPDATE d2_operator_export SET receipt_hash=repeat('1',64),received_at=now()")
        self.assertEqual(result.returncode,0,result.stderr);self.assertIn('UPDATE 1',result.stdout)
        for query in ["UPDATE d2_operator_export SET payload='{}'",'DELETE FROM d2_operator_export',
                      'SELECT * FROM d2_operator_audit',"UPDATE d1_account SET name='changed'"]:
            result=self.scoped(EXPORTER,query)
            self.assertNotEqual(result.returncode,0,query);self.assertIn('permission denied',result.stderr)

    def test_unsafe_inherited_membership_is_rejected(self):
        self.sql(f'CREATE ROLE operator_unsafe_parent; GRANT operator_unsafe_parent TO {REPORTER};',check=True)
        try:
            result=self.sql((ROOT/'services/core-api/ops/operator-roles.sql').read_text())
            self.assertNotEqual(result.returncode,0)
            self.assertIn('must not inherit',result.stderr)
        finally:self.sql(f'REVOKE operator_unsafe_parent FROM {REPORTER};',check=True)

if __name__=='__main__':unittest.main()

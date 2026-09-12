"""Execute required behavior tests and compare the actual successful test IDs."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

def check(config, passed):
    cases=config.get('cases',[])
    mapping=config.get('evidence',{})
    if config.get('required_count')!=20 or len(set(cases))!=20 or len(cases)!=20 or set(mapping)!=set(cases):
        return 78
    missing={case:[name for name in mapping[case] if name not in passed] for case in cases}
    missing={case:names for case,names in missing.items() if names or not mapping[case]}
    if missing:
        print(json.dumps({'missing_evidence':missing},ensure_ascii=False));return 1
    return 0

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.passed=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.passed.append(test.id().split('.')[-1])

def main():
    config=tomllib.loads((ROOT/'gates/config/operator-notifications.toml').read_text())
    modules=sorted('scripts.tests.'+p.stem for p in (ROOT/'scripts/tests').glob('test_operator*.py'))
    modules.append('scripts.tests.test_deploy_release')
    suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
    result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
    if not result.testsRun:return 78
    if not result.wasSuccessful() or result.skipped:return 1
    py=ROOT/'services/core-api/.venv/bin/python'
    if not py.exists() or not os.environ.get('COLAB_CORE_TEST_DATABASE_URL'):return 78
    with tempfile.TemporaryDirectory() as tmp:
        xml=Path(tmp)/'core.xml'
        completed=subprocess.run([str(py),'-m','pytest','tests/test_operator_notifications_e2e.py','-q','--tb=short',f'--junitxml={xml}'],cwd=ROOT/'services/core-api')
        if completed.returncode:return 1
        cases=list(ET.parse(xml).iter('testcase'))
        if not cases:return 78
        passed=result.passed+[c.attrib['name'] for c in cases if not list(c)]
    rc=check(config,passed)
    report={'required_cases':config['cases'],'successful_tests':passed,'exit_code':rc}
    destination=os.environ.get('COLAB_OPERATOR_CASE_REPORT')
    if destination:Path(destination).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'operator-notifications: actual tests {len(passed)}, required cases {len(config["cases"])}, exit {rc}')
    return rc
if __name__=='__main__':raise SystemExit(main())

"""An archived release must execute notifications without the checkout on sys.path."""
import json, os, shutil, subprocess, sys, tarfile, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
class SourceBundleTests(unittest.TestCase):
 def test_unpackaged_checkout_is_not_needed_by_operator_entrypoint(self):
  with tempfile.TemporaryDirectory() as d:
   base=Path(d);repo=base/'repo';repo.mkdir()
   paths=['infra/ops','infra/notifications','infra/__init__.py','services/core-api/ops','services/core-api/src','services/core-api/pyproject.toml','services/core-api/requirements.in','services/core-api/requirements.txt','db/platform','db/ai','gates/tools/rls_coverage.py','gates/config/rls-allowlist.toml']
   for name in paths:
    src=ROOT/name;dst=repo/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir():shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__','.venv'))
    else:shutil.copy2(src,dst)
   subprocess.run(['git','init','-q',str(repo)],check=True);subprocess.run(['git','-C',str(repo),'add','.'],check=True)
   subprocess.run(['git','-C',str(repo),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
   sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip();out=base/'bundle'
   subprocess.run(['bash',str(ROOT/'infra/ops/build-source-bundle.sh'),'--repo',str(repo),'--sha',sha,'--output',str(out)],check=True,stdout=subprocess.DEVNULL)
   unpack=base/'unpack';unpack.mkdir()
   with tarfile.open(next(out.glob('*.tar.gz'))) as archive:archive.extractall(unpack,filter='data')
   self.assertTrue((unpack/'infra/notifications/cli.py').is_file(),'notification runtime missing from trusted source bundle')
   for name in paths[4:8]:self.assertTrue((unpack/name).exists(),name)
   code="import pathlib,sys;sys.path.insert(0,sys.argv[1]);import infra.notifications.cli as c;assert pathlib.Path(c.__file__).is_relative_to(sys.argv[1]);c.main(['--help'])"
   result=subprocess.run([sys.executable,'-I','-c',code,str(unpack)],cwd=base,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr);self.assertIn('drain-spool',result.stdout)

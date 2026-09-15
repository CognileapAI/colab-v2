#!/usr/bin/env python3
"""Run an explicitly named unittest file; zero execution is readiness failure."""
import argparse
import importlib.util
from pathlib import Path
import sys
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    args = parser.parse_args()
    path = args.file.resolve()
    if not path.is_file():
        print('::gate-readiness-failure:: unittest input file missing', file=sys.stderr)
        return 78
    spec = importlib.util.spec_from_file_location('explicit_unittest_input', path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        print(f'::gate-readiness-failure:: unittest import failed: {error}', file=sys.stderr)
        return 78
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    collected = suite.countTestCases()
    if not collected:
        print('::gate-readiness-failure:: unittest collected=0', file=sys.stderr)
        return 78
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    executed = result.testsRun - len(result.skipped)
    print(f'unittest collected={collected} executed={executed} skipped={len(result.skipped)}')
    if not result.wasSuccessful():
        return 1
    if executed == 0 or result.testsRun != collected:
        print('::gate-readiness-failure:: unittest did not execute its declared suite', file=sys.stderr)
        return 78
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

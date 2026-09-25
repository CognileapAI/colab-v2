"""One disposable AI database per xdist worker; never print credentials."""
import os
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url


def pytest_configure(config):
    worker = getattr(config, 'workerinput', None)
    if worker is None:
        return
    directory = os.environ.get('COLAB_AI_XDIST_DB_DIR')
    worker_id = worker.get('workerid')
    if not directory or not worker_id:
        raise pytest.UsageError('AI worker database wiring is missing')
    try:
        value = (Path(directory) / worker_id).read_text().strip()
        if not value:
            raise ValueError('empty URL')
        url = make_url(value)
    except (OSError, ValueError):
        raise pytest.UsageError('AI worker database input is unavailable') from None
    os.environ['COLAB_AI_TEST_DICT_DB_URL'] = value
    os.environ['COLAB_AI_TEST_KNOWLEDGE_DB_URL'] = url.set(
        username='colab_knowledge_writer', password='knowledge-test-only').render_as_string(hide_password=False)

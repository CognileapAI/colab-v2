import tempfile
import unittest
import zipfile
from pathlib import Path

from reference_evidence import collect_sources, verify_sources


class SourceEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.document(self.root / 'source.docx')
        self.roles = [dict(dataset_key='D1', file='input.npy', source_document='source.docx')]
        self.datasets = [dict(id='dataset-1', manifest_key='D1',
                              files=[dict(id='file-1', file_name='input.npy')])]

    def document(self, path, text='모델 입력은 관측값이 아닙니다.'):
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('word/document.xml',
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                f'<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>')

    def test_source_text_and_target_are_bound_without_inventing_claims(self):
        report = collect_sources(self.root, self.roles, self.datasets)
        self.assertEqual(report['sources'][0]['paragraphs'][0]['text'], '모델 입력은 관측값이 아닙니다.')
        self.assertEqual(report['bindings'][0]['dataset_id'], 'dataset-1')
        self.assertEqual(report['bindings'][0]['file_id'], 'file-1')
        self.assertFalse(report['automatically_verified'])
        self.assertEqual(verify_sources(self.root, report), [])

    def test_changed_source_invalidates_previous_collection(self):
        report = collect_sources(self.root, self.roles, self.datasets)
        self.document(self.root / 'source.docx', '수정된 설명')
        self.assertEqual(verify_sources(self.root, report), ['source.docx'])

    def test_ambiguous_source_is_not_chosen_arbitrarily(self):
        (self.root / 'other').mkdir()
        self.document(self.root / 'other/source.docx')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            collect_sources(self.root, self.roles, self.datasets)

    def test_missing_target_file_is_rejected(self):
        self.datasets[0]['files'] = []
        with self.assertRaisesRegex(ValueError, 'target'):
            collect_sources(self.root, self.roles, self.datasets)

    def test_manifest_cannot_verify_a_source_outside_root(self):
        with self.assertRaises(ValueError):
            verify_sources(self.root, {'sources': [{'path': '../outside.docx', 'sha256': 'x'}]})

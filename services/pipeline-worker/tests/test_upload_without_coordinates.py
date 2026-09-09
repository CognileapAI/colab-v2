"""Coordinates missing defers map production, not valid file registration (D.6-4)."""
from pathlib import Path

from colab_pipeline.d5.pipeline import run_file
from colab_pipeline.domains.d5_ingestion import IngestionService, UploadFileWork, UploadWork
from fixture_builders import make_hsr_bin_gz, make_npy_2d
from memory_ledger import MemoryLedger

LAB = '01JQ0000000000000000000001'
ACCOUNT = '01JQ0000000000000000000002'
UPLOAD = '01JQ0000000000000000000003'
FILE = '01JQ00000000000000000000F1'


def work_for(tmp_path: Path, paths: list[Path], grid_dir=None):
    return UploadWork(upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT,
                      workdir=tmp_path / 'work', previews_root=tmp_path / 'previews',
                      grid_dir=grid_dir,
                      files=[UploadFileWork(file_id=f'{FILE[:-1]}{i+1}', path=p,
                                            kind='본체', file_name=p.name)
                             for i, p in enumerate(paths)])


def process(work):
    ledger = MemoryLedger()
    ledger.accept(upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT)
    return ledger, IngestionService(ledger).process_upload(work, stage1=False)


def test_bin_without_coordinates_keeps_metadata_and_registration_ready(tmp_path, event_validator):
    source = make_hsr_bin_gz(tmp_path / 'rain.bin.gz', nx=8, ny=6)
    work = work_for(tmp_path, [source])
    ledger, result = process(work)
    assert [event['type'] for event in result.events] == [
        'file.format-detected', 'file.header-parsed', 'upload.ready']
    header = result.events[1]['payload']
    assert header['variables'] == ['블록1']
    assert header['period']['start'].startswith('2025-08-13T10:00:00')
    assert header['grid'] == '6x8'
    assert header['byteSizeTotal'] == source.stat().st_size
    assert header['crs'] is None
    assert header['unreadableFiles'] == []
    assert ledger.load_upload(UPLOAD)['ready'] is True
    assert ledger.load_upload(UPLOAD)['failed_at'] is None
    assert result.events[-1]['payload']['metadataComplete'] is False
    assert result.artifacts == []
    assert list(tmp_path.rglob('*.tif')) == []
    assert ledger.formats[FILE] == 'Binary'
    for event in result.events:
        assert event_validator(event) == []
    # The map converter's negative oracle is unchanged: no fake coordinate success.
    converted = run_file(source, workdir=tmp_path / 'convert')
    assert converted.status == 'FAILURE'
    assert converted.metadata.crs == '[미상]'
    assert converted.cog_path is None


def test_invalid_binary_is_still_failed_not_registration_ready(tmp_path):
    source = tmp_path / 'broken.bin'
    source.write_bytes(b'\x00' * 1024)
    ledger, result = process(work_for(tmp_path, [source]))
    assert result.events[-1]['type'] == 'upload.failed'
    assert ledger.load_upload(UPLOAD)['ready'] is False
    assert not any(event['type'] == 'file.header-parsed' for event in result.events)


def test_mixed_coordinate_availability_does_not_claim_cog_for_deferred_file(tmp_path):
    good = make_hsr_bin_gz(tmp_path / 'good.bin.gz', nx=600, ny=520)
    deferred = make_hsr_bin_gz(tmp_path / 'small.bin.gz', nx=8, ny=6)
    grid = tmp_path / 'grid'
    grid.mkdir()
    make_npy_2d(grid / 'Lat_HSR.npy', 520, 600, start=33.0)
    make_npy_2d(grid / 'Lon_HSR.npy', 520, 600, start=124.0)
    ledger, result = process(work_for(tmp_path, [good, deferred], grid))
    assert ledger.load_upload(UPLOAD)['ready'] is True
    header = next(e['payload'] for e in result.events if e['type'] == 'file.header-parsed')
    assert header['unreadableFiles'] == []
    assert header['byteSizeTotal'] == good.stat().st_size + deferred.stat().st_size
    for event in result.events:
        if event['type'] in ('file.crs-normalized', 'preview.cog-built'):
            assert event['payload']['fileIds'] == [FILE]
    assert result.events[-1]['payload']['metadataComplete'] is False
    assert len(result.artifacts) == 1


def test_deferred_first_uses_converted_file_crs_for_normalization(tmp_path, event_validator):
    deferred = make_hsr_bin_gz(tmp_path / 'small.bin.gz', nx=8, ny=6)
    good = make_hsr_bin_gz(tmp_path / 'good.bin.gz', nx=600, ny=520)
    grid = tmp_path / 'grid'
    grid.mkdir()
    make_npy_2d(grid / 'Lat_HSR.npy', 520, 600, start=33.0)
    make_npy_2d(grid / 'Lon_HSR.npy', 520, 600, start=124.0)
    ledger, result = process(work_for(tmp_path, [deferred, good], grid))
    assert ledger.load_upload(UPLOAD)['ready'] is True
    normalized = next(e['payload'] for e in result.events if e['type'] == 'file.crs-normalized')
    assert normalized['sourceCrs'] == 'WGS84 (기준 격자 파일)'
    assert normalized['transformed'] is True
    assert normalized['fileIds'] == [FILE[:-1] + '2']
    for event in result.events:
        assert event_validator(event) == []


def test_already_ready_deferred_rerun_invalidates_value_preview(tmp_path):
    source = make_hsr_bin_gz(tmp_path / 'rain.bin.gz')
    work = work_for(tmp_path, [source])
    ledger, first = process(work)
    assert first.events[-1]['type'] == 'upload.ready'
    repeated = IngestionService(ledger).process_upload(work, stage1=False)
    assert 'preview.backend-rerun' in [e['type'] for e in repeated.events]
    assert not any(e['type'] in ('file.crs-normalized', 'preview.cog-built') for e in repeated.events)


def test_failed_upload_recovery_clears_previous_failure_fields(tmp_path):
    from datetime import datetime, timezone
    source = make_hsr_bin_gz(tmp_path / 'rain.bin.gz')
    ledger = MemoryLedger()
    ledger.accept(upload_id=UPLOAD, lab_id=LAB, actor_account_id=ACCOUNT)
    ledger.record_status(UPLOAD, ready=False, failed_at=datetime.now(timezone.utc),
                         failure_class='재시도 가능', failure_reason='좌표계 변환 실패')
    result = IngestionService(ledger).process_upload(work_for(tmp_path, [source]), stage1=False)
    saved = ledger.load_upload(UPLOAD)
    assert saved['ready'] is True
    assert saved['failed_at'] is None
    assert saved['failure_class'] is None
    assert saved['failure_reason'] is None
    assert result.events[-1]['type'] == 'upload.ready'


def test_grid_injection_after_deferred_ready_builds_real_cog(tmp_path, event_validator):
    from dataclasses import replace
    source = make_hsr_bin_gz(tmp_path / 'rain.bin.gz', nx=600, ny=520)
    work = work_for(tmp_path, [source])
    ledger, first = process(work)
    assert first.artifacts == []
    grid = tmp_path / 'grid'
    grid.mkdir()
    make_npy_2d(grid / 'Lat_HSR.npy', 520, 600, start=33.0)
    make_npy_2d(grid / 'Lon_HSR.npy', 520, 600, start=124.0)
    result = IngestionService(ledger).process_upload(replace(work, grid_dir=grid), stage1=False)
    assert len(result.artifacts) == 1
    assert result.artifacts[0].path.exists()
    normalized = next(e['payload'] for e in result.events if e['type'] == 'file.crs-normalized')
    assert normalized['sourceCrs'] == 'WGS84 (기준 격자 파일)'
    assert normalized['transformed'] is True
    assert ledger.load_upload(UPLOAD)['metadata_complete'] is True
    for event in result.events:
        assert event_validator(event) == []

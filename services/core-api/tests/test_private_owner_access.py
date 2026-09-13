"""ST regression: a private upload must remain usable by its owner only."""
from conftest import TOKEN_RES, TOKEN_PROF, TOKEN_B, auth
from test_dataset_registration import make_upload, register
from colab_core.app.main import API_PREFIX


def test_private_owner_can_read_files_and_save_evidence(p2_client):
    client = p2_client(session_secret="private-owner-download-regression")
    created = register(client, make_upload(client), accessState="잠김")
    assert created.status_code == 201, created.text
    dataset = created.json()["datasetId"]
    path = f"{API_PREFIX}/datasets/{dataset}"
    detail = client.get(path, headers=auth(TOKEN_RES))
    assert detail.status_code == 200
    assert detail.json()["bodyAccessible"] is True
    files = client.get(path + "/files", headers=auth(TOKEN_RES))
    assert files.status_code == 200, files.text
    evidence = client.get(path + "/search-evidence", headers=auth(TOKEN_RES))
    assert evidence.status_code == 200, evidence.text
    item = evidence.json()["items"][0]
    payload = {"expectedRevision": 0, "expectedFileRevision": item["fileRevision"],
               "facts": {"roles": ["validation"]}, "status": "reviewed",
               "source": {"label": "합성 시험", "locator": "역할", "text": "검증용 합성 파일"}}
    saved = client.put(path + f"/files/{item['fileId']}/search-evidence",
                       headers=auth(TOKEN_RES), json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "reviewed"
    ticket = client.get(path + f"/files/{item['fileId']}/download", headers=auth(TOKEN_RES))
    assert ticket.status_code == 200, ticket.text
    downloaded = client.get(ticket.json()["url"])
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content
    # Independent requests must observe persisted evidence after the write.
    again = client.get(path + "/search-evidence", headers=auth(TOKEN_RES))
    assert again.json()["items"][0]["evidence"]["source"]["text"] == "검증용 합성 파일"
    for token in (TOKEN_PROF, TOKEN_B):
        for suffix in ("/files", "/search-evidence", f"/files/{item['fileId']}/download"):
            response = client.get(path + suffix, headers=auth(token))
            assert response.status_code in (403, 404), response.text

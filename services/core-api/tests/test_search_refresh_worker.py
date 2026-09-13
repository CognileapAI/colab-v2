from types import SimpleNamespace
import pytest
from colab_core.kernel.auth import Subject
from colab_core.kernel.ids import Ulid
from conftest import ACC_A_RES,LAB_A


def test_runtime_rechecks_credential_flags_and_version():
    from colab_core.app.search_refresh_worker import actor
    credential=SimpleNamespace(subject=Subject(Ulid(ACC_A_RES),Ulid(LAB_A)),status='active',must_change_password=False,session_version=1)
    store=SimpleNamespace(find=lambda name:credential)
    subject,validate=actor(store,'fixture');validate(subject)
    credential.session_version=2
    with pytest.raises(ValueError):validate(subject)
    credential.must_change_password=True
    with pytest.raises(ValueError):actor(store,'fixture')
    credential.must_change_password=False;credential.status='inactive'
    with pytest.raises(ValueError):actor(store,'fixture')


@pytest.mark.parametrize('raw',[None,'[]','["a","a"]','{"account":"a"}','[1]'])
def test_missing_or_ambiguous_runtime_scope_fails_closed(raw):
    from colab_core.app.search_refresh_worker import configured_accounts
    with pytest.raises(ValueError):configured_accounts({} if raw is None else {'COLAB_SEARCH_REFRESH_ACCOUNTS':raw})

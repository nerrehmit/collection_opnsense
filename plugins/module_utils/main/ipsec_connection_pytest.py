import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.ipsec_connection import Connection
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import MockAnsibleModule

# 'version' option labels as returned by 'ipsec/connections/get'
#   the keys are 0..2, so the API returns the options as a JSON list
VERSION_LABELS = {
    '26.7.7': ['IKEv1+IKEv2', 'IKEv1', 'IKEv2'],
    # 26.7.8 deprecated IKEv1 and renamed the labels (opnsense/core#10925)
    '26.7.8': ['IKEv1+IKEv2 (allows deprecated IKEv1)', 'IKEv1 (deprecated)', 'IKEv2'],
}
VERSION_KEYS = {'ikev1+2': 0, 'ikev1': 1, 'ikev2': 2}
UUID = 'fe1b5c3a-6c1e-4d8f-9a62-4f3e3c4b9a01'
NAME = 'ANSIBLE_TEST_1_1'


def _option_dict(options: dict, selected: str) -> dict:
    return {k: {'value': v, 'selected': 1 if k == selected else 0} for k, v in options.items()}


def _api_connection(version: str, release: str) -> dict:
    labels = VERSION_LABELS[release]
    port_options = {'': '500 (default)', '4500': '4500 (NAT-T)'}

    return {
        'enabled': '1',
        'proposals': _option_dict({'default': 'default', 'aes256-sha256-modp2048': 'aes256-sha256-modp2048'}, 'default'),
        'unique': _option_dict({'no': 'No (default)', 'never': 'Never', 'keep': 'Keep', 'replace': 'Replace'}, 'no'),
        'aggressive': '0',
        'version': [
            {'value': label, 'selected': 1 if idx == VERSION_KEYS[version] else 0}
            for idx, label in enumerate(labels)
        ],
        'mobike': '1',
        'local_addrs': {},
        'local_port': _option_dict(port_options, ''),
        'remote_addrs': {},
        'remote_port': _option_dict(port_options, ''),
        'encap': '0',
        'reauth_time': '',
        'rekey_time': '',
        'over_time': '',
        'dpd_delay': '',
        'dpd_timeout': '',
        'pools': {},
        'send_certreq': '1',
        'send_cert': _option_dict({'': 'Default', 'ifasked': 'If asked', 'never': 'Never', 'always': 'Always'}, ''),
        'keyingtries': '',
        'description': NAME,
        'local_ts': '',
        'remote_ts': '',
    }


def _api_get_response(version: str, release: str) -> dict:
    return {'swanctl': {
        'Connections': {'Connection': {UUID: _api_connection(version, release)}},
        'Pools': {'Pool': {}},
    }}


def _connection(mocker, version: str, existing_version: str, release: str) -> (Connection, dict):
    module = MockAnsibleModule()
    module.check_mode = True
    module.params.update({
        'name': NAME,
        'local_addresses': [],
        'local_port': '500',
        'remote_addresses': [],
        'remote_port': '500',
        'pools': [],
        'proposals': ['default'],
        'unique': 'no',
        'aggressive': False,
        'version': version,
        'mobike': True,
        'encapsulation': False,
        'reauth_seconds': None,
        'rekey_seconds': None,
        'over_seconds': None,
        'dpd_delay_seconds': None,
        'dpd_timeout_seconds': None,
        'send_certificate_request': True,
        'send_certificate': None,
        'keying_tries': None,
        'enabled': True,
        'state': 'present',
        'reload': False,
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    conn = Connection(module=module, result=result)
    mocker.patch.object(conn, '_api_get', return_value=_api_get_response(existing_version, release))
    return conn, result


@pytest.mark.parametrize('release', VERSION_LABELS.keys())
@pytest.mark.parametrize('version', VERSION_KEYS.keys())
def test_ipsec_connection_reads_version(mocker, release: str, version: str):
    conn, _ = _connection(mocker, version=version, existing_version=version, release=release)
    conn.check()

    assert conn.exists
    assert conn.tunnel['version'] == version


@pytest.mark.parametrize('release', VERSION_LABELS.keys())
@pytest.mark.parametrize('version', VERSION_KEYS.keys())
def test_ipsec_connection_version_unchanged(mocker, release: str, version: str):
    conn, result = _connection(mocker, version=version, existing_version=version, release=release)
    conn.check()
    conn.process()

    assert result['changed'] is False


@pytest.mark.parametrize('release', VERSION_LABELS.keys())
def test_ipsec_connection_version_changed(mocker, release: str):
    conn, result = _connection(mocker, version='ikev2', existing_version='ikev1+2', release=release)
    conn.check()
    conn.process()

    assert result['changed'] is True
    assert result['diff']['before']['version'] == 'ikev1+2'
    assert result['diff']['after']['version'] == 'ikev2'

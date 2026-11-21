import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.nat_source import SNat
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    MockAnsibleModule, AnsibleError


def test_nat_source_uses_rule_endpoints():
    assert SNat.CMDS['search'] == 'search_rule'
    assert SNat.CMDS['detail'] == 'get_rule'
    assert SNat.API_KEY_PATH == 'rule'


def test_nat_source_normalizes_protocol_to_existing_opnsense_case(mocker):
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present',
        'enabled': True,
        'sequence': 1,
        'no_nat': False,
        'interface': 'lan',
        'target': '192.168.0.5',
        'target_port': '',
        'description': 'ANSIBLE_TEST_SNAT',
        'ip_protocol': 'inet',
        'protocol': 'TCP',
        'source_invert': False,
        'source_net': 'any',
        'source_port': '',
        'destination_invert': False,
        'destination_net': '192.168.0.1',
        'destination_port': '',
        'log': False,
        'static_port': False,
        'match_fields': ['description'],
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    snat = SNat(module=module, result=result)

    mocker.patch.object(snat, '_check_mode')
    mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')

    snat.check()

    assert snat.p['protocol'] == 'TCP'


def test_nat_source_existing_uppercase_protocol_stays_idempotent(mocker):
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present',
        'enabled': True,
        'sequence': 1,
        'no_nat': False,
        'interface': 'lan',
        'target': '192.168.0.5',
        'target_port': '',
        'description': 'ANSIBLE_TEST_SNAT',
        'ip_protocol': 'inet',
        'protocol': 'tcp',
        'source_invert': False,
        'source_net': 'any',
        'source_port': '',
        'destination_invert': False,
        'destination_net': '192.168.0.1',
        'destination_port': '',
        'log': False,
        'static_port': False,
        'match_fields': ['description'],
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    snat = SNat(module=module, result=result)

    snat.rule = {
        'uuid': 'rule-1',
        'enabled': True,
        'sequence': 1,
        'no_nat': False,
        'interface': 'lan',
        'target': '192.168.0.5',
        'target_port': '',
        'description': 'ANSIBLE_TEST_SNAT',
        'ip_protocol': 'inet',
        'protocol': 'TCP',
        'source_invert': False,
        'source_net': 'any',
        'source_port': '',
        'destination_invert': False,
        'destination_net': '192.168.0.1',
        'destination_port': '',
        'log': False,
        'static_port': False,
    }

    mocker.patch.object(snat, '_check_mode')
    mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')

    snat.check()
    snat._base_update(enable_switch=False)

    assert result['changed'] is False


def test_nat_source_any_protocol_stays_lowercase(mocker):
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present',
        'enabled': True,
        'sequence': 1,
        'no_nat': False,
        'interface': 'lan',
        'target': '192.168.0.5',
        'target_port': '',
        'description': 'ANSIBLE_TEST_SNAT',
        'ip_protocol': 'inet',
        'protocol': 'ANY',
        'source_invert': False,
        'source_net': 'any',
        'source_port': '',
        'destination_invert': False,
        'destination_net': '192.168.0.1',
        'destination_port': '',
        'log': False,
        'static_port': False,
        'match_fields': ['description'],
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    snat = SNat(module=module, result=result)

    mocker.patch.object(snat, '_check_mode')
    mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')

    snat.check()

    assert snat.p['protocol'] == 'any'


def _mode_response(mode: str, path: str = 'general') -> dict:
    modes = {m: {'value': m, 'selected': int(m == mode)} for m in ['automatic', 'hybrid', 'advanced', 'disabled']}
    if path == 'general':
        return {'filter': {'general': {'snat_mode': modes}}}

    return {'filter': {'settings': {'nat': {'snat_mode': modes}}}}


def test_nat_source_manual_mode_passes(mocker):
    module = MockAnsibleModule()
    module.params.update({'state': 'present'})
    snat = SNat(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})
    snat.s = mocker.Mock()

    for path in ['general', 'settings']:
        for mode in SNat.MANUAL_MODES:
            snat.s.get.return_value = _mode_response(mode, path)
            snat._check_mode()


def test_nat_source_automatic_mode_fails_on_present(mocker):
    module = MockAnsibleModule()
    module.params.update({'state': 'present'})
    snat = SNat(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})
    snat.s = mocker.Mock()
    snat.s.get.return_value = _mode_response('automatic')

    with pytest.raises(AnsibleError, match="'automatic'"):
        snat._check_mode()


def test_nat_source_automatic_mode_warns_on_absent(mocker):
    module = MockAnsibleModule()
    module.params.update({'state': 'absent'})
    module.warn = mocker.Mock()
    module.fail_json = mocker.Mock()
    snat = SNat(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})
    snat.s = mocker.Mock()
    snat.s.get.return_value = _mode_response('disabled')

    snat._check_mode()

    module.fail_json.assert_not_called()
    module.warn.assert_called_once()


def _rule_api_26_1_4() -> dict:
    # a rule as 'get_rule' returns it before OPNsense 26.1.5, which added 'staticnatport' (upstream issue #466)
    return {
        'uuid': 'rule-1', 'enabled': '1', 'nonat': '0', 'sequence': '1',
        'interface': {'lan': {'value': 'LAN', 'selected': 0}, 'wan': {'value': 'WAN', 'selected': 1}},
        'ipprotocol': {'inet': {'value': 'IPv4', 'selected': 1}, 'inet6': {'value': 'IPv6', 'selected': 0}},
        'protocol': {'any': {'value': 'any', 'selected': 0}, 'TCP': {'value': 'TCP', 'selected': 1}},
        'source_net': '198.51.100.0/24', 'source_not': '0', 'source_port': '',
        'destination_net': '203.0.113.0/24', 'destination_not': '0', 'destination_port': '',
        'target': 'wanip', 'target_port': '', 'log': '0', 'categories': [], 'tagged': '',
        'description': 'ANSIBLE_TEST_SNAT',
    }


def _snat_26_1_4(params: dict = None) -> (SNat, dict):
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present', 'enabled': True, 'sequence': 1, 'no_nat': False, 'interface': 'wan',
        'target': 'wanip', 'target_port': '', 'description': 'ANSIBLE_TEST_SNAT', 'ip_protocol': 'inet',
        'protocol': 'TCP', 'source_invert': False, 'source_net': '198.51.100.0/24', 'source_port': '',
        'destination_invert': False, 'destination_net': '203.0.113.0/24', 'destination_port': '',
        'log': False, 'static_port': False, 'match_fields': ['description'],
        **(params or {}),
    })
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    snat = SNat(module=module, result=result)
    snat.s = None
    return snat, result


def test_nat_source_reads_rule_without_staticnatport():
    snat, _ = _snat_26_1_4()
    simple = snat.simplify_existing(_rule_api_26_1_4())

    assert 'static_port' not in simple
    assert simple['interface'] == 'wan'
    assert simple['no_nat'] is False


@pytest.mark.parametrize('params, changed', [
    ({}, False),
    ({'static_port': True}, False),  # the field can't be compared, OPNsense before 26.1.5 has no such setting
    ({'sequence': 2}, True),
    ({'log': True}, True),
])
def test_nat_source_rule_without_staticnatport_is_idempotent(mocker, params: dict, changed: bool):
    snat, result = _snat_26_1_4(params)
    snat.rule = snat.simplify_existing(_rule_api_26_1_4())
    snat.exists = True
    mocker.patch.object(snat, '_check_mode')
    mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')

    snat.check()
    snat.build_diff(data=snat.rule)
    snat.m.check_mode = True
    snat._base_update(enable_switch=False)

    assert result['changed'] is changed


def _build_snat(mocker, **params) -> SNat:
    module = MockAnsibleModule()
    module.params.update({
        'state': 'present', 'interface': 'lan', 'target': '', 'protocol': '', 'match_fields': ['description'],
        'enabled': True, 'sequence': 1, 'no_nat': False, 'target_port': '', 'description': 'T',
        'ip_protocol': 'inet', 'source_invert': False, 'source_net': 'any', 'source_port': '',
        'destination_invert': False, 'destination_net': '192.168.0.1', 'destination_port': '',
        'log': False, 'static_port': False, **params,
    })
    snat = SNat(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})
    mocker.patch.object(snat, '_check_mode')
    mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')
    return snat


def test_check_allows_empty_target(mocker):
    _build_snat(mocker).check()


def test_check_requires_interface(mocker):
    with pytest.raises(AnsibleError):
        _build_snat(mocker, interface='').check()

from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.nat_source import SNat
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    MockAnsibleModule


def test_nat_source_uses_rule_endpoints():
    assert SNat.CMDS['search'] == 'search_rule'
    assert SNat.CMDS['detail'] == 'get_rule'
    assert SNat.API_KEY_PATH == 'rule'


def test_nat_source_normalizes_protocol_before_matching(mocker):
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

    find = mocker.patch.object(snat, 'find')
    mocker.patch.object(snat, '_base_check')

    snat.check()

    assert snat.p['protocol'] == 'tcp'
    find.assert_called_once_with(match_fields=['description'])

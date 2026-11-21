import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    pytest_mock_http_responses, MockAnsibleModule, AnsibleError
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.gateway_group_testdata import \
    GatewayGroupTestdata
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import AnsibleModuleError

PARAMS = dict(
    name='WAN_FAILOVER', tier1=['LAN_GW'], tier2=['TEST-GW'], tier3=[], tier4=[], tier5=[],
    trigger='down', pool_options='', description='test', state='present', reload=False,
)


def _mock(mocker) -> GatewayGroupTestdata:
    testdata = GatewayGroupTestdata()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)
    return testdata


def _run(params: dict, check_mode: bool = False) -> dict:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.gateway_group import GwGroup

    module = MockAnsibleModule()
    module.params.update(params)
    module.check_mode = check_mode
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(GwGroup(module=module, result=result))
    return result


def test_gateway_group_create_and_rerun(mocker):
    testdata = _mock(mocker)

    result = _run(PARAMS)
    assert result['changed']
    assert len(testdata.mutations()) == 1
    action, request = testdata.mutations()[0]
    assert action == 'add'
    assert request == {
        'name': 'WAN_FAILOVER', 'item': 'LAN_GW', 'item2': 'TEST-GW', 'item3': '', 'item4': '', 'item5': '',
        'trigger': 'down', 'poolopts': '', 'descr': 'test',
    }

    result = _run(PARAMS)
    assert not result['changed']
    assert len(testdata.mutations()) == 1


def test_gateway_group_check_mode(mocker):
    testdata = _mock(mocker)
    result = _run(PARAMS, check_mode=True)
    assert result['changed']
    assert len(testdata.mutations()) == 0


@pytest.mark.parametrize('changed', [
    {'tier1': ['LAN_GW', 'TEST-GW'], 'tier2': []},
    {'tier1': [], 'tier2': ['LAN_GW'], 'tier3': ['TEST-GW']},
    {'tier5': ['WAN_DHCP']},
    {'trigger': 'downlosslatency'},
    {'pool_options': 'round-robin sticky-address'},
    {'description': 'other'},
])
def test_gateway_group_update(mocker, changed: dict):
    testdata = _mock(mocker)
    _run(PARAMS)

    params = {**PARAMS, **changed}
    result = _run(params)
    assert result['changed']
    assert testdata.mutations()[-1][0] == 'set'
    assert len(testdata.state) == 1
    stored = list(testdata.state.values())[0]
    for field, api_field in {
        'tier1': 'item', 'tier2': 'item2', 'tier3': 'item3', 'tier4': 'item4', 'tier5': 'item5',
    }.items():
        assert stored[api_field] == ','.join(params[field])

    assert stored['trigger'] == params['trigger']
    assert stored['poolopts'] == params['pool_options']

    result = _run(params)
    assert not result['changed']


def test_gateway_group_tier_order_and_duplicates_are_ignored(mocker):
    testdata = _mock(mocker)
    _run({**PARAMS, 'tier1': ['TEST-GW', 'LAN_GW'], 'tier2': []})

    result = _run({**PARAMS, 'tier1': ['LAN_GW', 'TEST-GW', 'LAN_GW'], 'tier2': []})
    assert not result['changed']
    assert len(testdata.mutations()) == 1


def test_gateway_group_delete(mocker):
    testdata = _mock(mocker)
    _run(PARAMS)

    result = _run({**PARAMS, 'state': 'absent'})
    assert result['changed']
    assert testdata.mutations()[-1][0] == 'del'
    assert len(testdata.state) == 0

    result = _run({**PARAMS, 'state': 'absent'})
    assert not result['changed']


def test_gateway_group_absent_needs_no_tier(mocker):
    _mock(mocker)
    result = _run({**PARAMS, 'tier1': [], 'tier2': [], 'state': 'absent'})
    assert not result['changed']


def test_gateway_group_needs_a_gateway(mocker):
    testdata = _mock(mocker)
    with pytest.raises(AnsibleError, match='at least one gateway'):
        _run({**PARAMS, 'tier1': [], 'tier2': []})

    assert len(testdata.mutations()) == 0


@pytest.mark.parametrize('name', ['WAN FAILOVER', 'WAN.FAILOVER', 'A' * 33, ''])
def test_gateway_group_invalid_name(mocker, name: str):
    testdata = _mock(mocker)
    with pytest.raises((AnsibleError, AnsibleModuleError)):
        _run({**PARAMS, 'name': name})

    assert len(testdata.mutations()) == 0


def test_gateway_group_unknown_gateway_fails(mocker):
    _mock(mocker)
    with pytest.raises(AnsibleError):
        _run({**PARAMS, 'tier1': ['DOES_NOT_EXIST']})


def test_gateway_group_reload(mocker):
    testdata = _mock(mocker)
    _run({**PARAMS, 'reload': True})
    assert ('reconfigure', None) in testdata.calls


def test_gateway_group_list(mocker):
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.gateway_group import GwGroup

    _mock(mocker)
    _run(PARAMS)
    _run({**PARAMS, 'name': 'WAN_LOADBALANCE', 'tier1': ['LAN_GW', 'TEST-GW'], 'tier2': [],
          'pool_options': 'round-robin'})

    module = MockAnsibleModule()
    group = GwGroup(module=module, result={'changed': False, 'diff': {'before': {}, 'after': {}}})
    entries = {e['name']: e for e in group.get_existing()}

    assert set(entries) == {'WAN_FAILOVER', 'WAN_LOADBALANCE'}
    assert entries['WAN_FAILOVER']['tier1'] == ['LAN_GW']
    assert entries['WAN_FAILOVER']['tier2'] == ['TEST-GW']
    assert entries['WAN_FAILOVER']['tier3'] == []
    assert entries['WAN_FAILOVER']['trigger'] == 'down'
    assert entries['WAN_LOADBALANCE']['tier1'] == ['LAN_GW', 'TEST-GW']
    assert entries['WAN_LOADBALANCE']['pool_options'] == 'round-robin'

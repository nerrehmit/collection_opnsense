from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import \
    pytest_mock_http_responses, MockAnsibleModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.base_testdata import \
    MockOPNsenseController


class UnboundHostTestdata(MockOPNsenseController):
    """
    unbound/settings/get returns host overrides the way OPNsense does: selects as option-dicts,
    and 'addptr' defaults to '1' (model default) when a request does not set it
    """

    def __init__(self):
        super().__init__()
        self.posted = []

    def commands(self) -> dict:
        return {
            'get': self._get,
            'add_host_override': self._add,
            'set_host_override': self._set,
            'del_host_override': self._del,
            'reconfigure': self._reconfigure,
        }

    def route_kwargs(self, method) -> list:
        return {
            self._get: [],
            self._add: ['data'],
            self._set: ['uuid', 'data'],
            self._del: ['uuid'],
            self._reconfigure: [],
        }[method]

    def _get(self) -> dict:
        return {'unbound': {'hosts': {'host': self.state}}}

    def _store(self, data: dict) -> dict:
        host = data['host']
        self.posted.append(host)
        return {
            'enabled': host['enabled'], 'hostname': host['hostname'], 'domain': host['domain'],
            'rr': {rr: {'value': rr, 'selected': int(rr == host['rr'])} for rr in ['A', 'AAAA', 'MX', 'TXT']},
            'mxprio': host.get('mxprio', ''), 'mx': host.get('mx', ''), 'server': host.get('server', ''),
            'description': host['description'], 'addptr': host.get('addptr', '1'),
        }

    def _add(self, data: dict) -> dict:
        self.state[self._new_uuid()] = self._store(data)
        return {'result': 'saved'}

    def _set(self, uuid: str, data: dict) -> dict:
        self.state[uuid] = self._store(data)
        return {'result': 'saved'}


PARAMS = dict(
    hostname='host', domain='opnsense.test.oxlorg.net', record_type='A', value='192.168.0.1', prio=10,
    description='ANSIBLE_TEST', add_ptr=True, enabled=True, match_fields=['description'],
    state='present', reload=False,
)


def _run(params: dict) -> dict:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.unbound_host import Host

    module = MockAnsibleModule()
    module.params.update(params)
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(Host(module=module, result=result))
    return result


def test_unbound_host_add_ptr(mocker):
    testdata = UnboundHostTestdata()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)

    assert _run(PARAMS)['changed']
    assert testdata.posted[-1]['addptr'] == 1
    assert not _run(PARAMS)['changed']

    # upstream issue #473: the 'Add PTR record' option
    assert _run({**PARAMS, 'add_ptr': False})['changed']
    assert testdata.posted[-1]['addptr'] == 0
    assert list(testdata.state.values())[0]['addptr'] == 0
    assert not _run({**PARAMS, 'add_ptr': False})['changed']

    assert _run(PARAMS)['changed']
    assert testdata.posted[-1]['addptr'] == 1
    assert len(testdata.state) == 1


def test_unbound_host_ptr_disabled_in_gui_is_detected(mocker):
    testdata = UnboundHostTestdata()
    pytest_mock_http_responses(mocker=mocker, handler=testdata)
    _run(PARAMS)
    list(testdata.state.values())[0]['addptr'] = '0'

    assert _run(PARAMS)['changed']
    assert testdata.posted[-1]['addptr'] == 1

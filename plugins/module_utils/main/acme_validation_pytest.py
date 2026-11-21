import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import MockAnsibleModule
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_http_pytest import MockHttpClient
from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.base_testdata import \
    MockOPNsenseController

SECRET = 'SELFHOST-SECRET'


class AcmeValidationTestdata(MockOPNsenseController):
    """
    acmeclient/settings/get lists the validations, acmeclient/validations/get returns the defaults of a new one.
    Like OPNsense, add/update only store the fields the model has.
    """

    def __init__(self, apikey_model: bool):
        # pylint: disable=C0415
        from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.acme_validation import Validation

        super().__init__()
        self.fields = ['enabled', 'dns_selfhost_map'] + [
            Validation.FIELDS_TRANSLATE.get(f, f) for f in Validation.FIELDS_ALL
            if not f.startswith('dns_selfhost_')
        ]
        if apikey_model:
            # os-acme-client 4.18
            self.fields.append('dns_selfhost_apikey')

        else:
            self.fields.extend(['dns_selfhost_user', 'dns_selfhost_password'])

        self.urls = []
        self.posted = []

    def commands(self) -> dict:
        return {
            'get': self._get,
            'add': self._add,
            'update': self._set,
            'del': self._del,
            'toggle': self._toggle,
        }

    def route_kwargs(self, method) -> list:
        return {
            self._get: [],
            self._add: ['data'],
            self._set: ['uuid', 'data'],
            self._del: ['uuid'],
            self._toggle: ['uuid'],
        }[method]

    def _template(self) -> dict:
        return {f: '' for f in self.fields}

    def _get(self) -> dict:
        if self.urls[-1].startswith('acmeclient/validations/'):
            return {'validation': self._template()}

        return {'acmeclient': {'validations': {'validation': self.state}}}

    def _store(self, data: dict) -> dict:
        self.posted.append(data['validation'])
        return {**self._template(), **{k: v for k, v in data['validation'].items() if k in self.fields}}

    def _add(self, data: dict) -> dict:
        self.state[self._new_uuid()] = self._store(data)
        return {'result': 'saved'}

    def _set(self, uuid: str, data: dict) -> dict:
        self.state[uuid] = self._store(data)
        return {'result': 'saved'}


class RecordingHttpClient(MockHttpClient):
    def _process(self, method: str, url: str, data: dict = None):
        self._mock_handler.urls.append(url.replace(self.base_url, ''))
        return super()._process(method=method, url=url, data=data)


class WarningModule(MockAnsibleModule):
    def __init__(self):
        super().__init__()
        self.warnings = []

    def warn(self, msg: str):
        self.warnings.append(msg)


def _module_defaults(mocker) -> dict:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.modules import acme_validation as module_file

    class SpecCaptured(Exception):
        pass

    def _capture(argument_spec: dict, **kwargs):
        del kwargs
        raise SpecCaptured(argument_spec)

    mocker.patch.object(module_file, 'AnsibleModule', side_effect=_capture)
    with pytest.raises(SpecCaptured) as captured:
        module_file.run_module()

    mocker.stopall()
    # connection-settings come from the mock module
    return {
        k: v.get('default') for k, v in captured.value.args[0].items()
        if k not in MockAnsibleModule.PARAMS
    }


def _mock(mocker, apikey_model: bool) -> AcmeValidationTestdata:
    testdata = AcmeValidationTestdata(apikey_model=apikey_model)
    mock_client = mocker.patch('httpx.Client', autospec=True)
    mock_client.return_value = RecordingHttpClient(mock_handler=testdata)
    return testdata


def _run(defaults: dict, params: dict) -> WarningModule:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.acme_validation import Validation

    module = WarningModule()
    module.params.update({**defaults, **params})
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    module_wrapper(Validation(module=module, result=result))
    return module


SELFHOST_APIKEY = {'name': 'selfhost', 'dns_service': 'dns_selfhost', 'dns_selfhost_apikey': SECRET}
SELFHOST_USER = {
    'name': 'selfhost', 'dns_service': 'dns_selfhost',
    'dns_selfhost_user': 'user', 'dns_selfhost_password': SECRET,
}


def test_acme_validation_selfhost_apikey_is_sent(mocker):
    defaults = _module_defaults(mocker)
    testdata = _mock(mocker, apikey_model=True)

    module = _run(defaults, SELFHOST_APIKEY)
    assert module.warnings == []
    assert testdata.posted[0]['dns_selfhost_apikey'] == SECRET
    assert list(testdata.state.values())[0]['dns_selfhost_apikey'] == SECRET

    # update of the existing entry
    module = _run(defaults, SELFHOST_APIKEY)
    assert module.warnings == []
    assert len(testdata.state) == 1
    assert testdata.posted[1]['dns_selfhost_apikey'] == SECRET


@pytest.mark.parametrize('apikey_model, params, warns', [
    (True, SELFHOST_APIKEY, None),
    (True, SELFHOST_USER, "needs 'dns_selfhost_apikey'"),
    (False, SELFHOST_USER, None),
    (False, SELFHOST_APIKEY, "older than 4.18"),
    (True, {**SELFHOST_USER, 'dns_service': 'dns_freedns'}, None),
])
def test_acme_validation_selfhost_auth_warning(mocker, apikey_model: bool, params: dict, warns: str):
    defaults = _module_defaults(mocker)

    # without any validation, the field-check needs the defaults of a new one
    testdata = _mock(mocker, apikey_model=apikey_model)
    module = _run(defaults, params)
    # with an existing one, it is answered from the validations that were already read
    urls_before = len(testdata.urls)
    module_rerun = _run(defaults, params)

    for m in [module, module_rerun]:
        if warns is None:
            assert m.warnings == []

        else:
            assert len(m.warnings) == 1
            assert warns in m.warnings[0]

    assert 'acmeclient/validations/get' not in testdata.urls[urls_before:]
    if params['dns_service'] != 'dns_selfhost':
        assert 'acmeclient/validations/get' not in testdata.urls


def test_acme_validation_selfhost_absent_skips_check(mocker):
    defaults = _module_defaults(mocker)
    testdata = _mock(mocker, apikey_model=True)

    module = _run(defaults, {**SELFHOST_USER, 'state': 'absent'})
    assert module.warnings == []
    assert 'acmeclient/validations/get' not in testdata.urls

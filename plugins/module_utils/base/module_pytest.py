import importlib
import inspect
from pathlib import Path

import pytest

from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.mock_pytest import MockAnsibleModule


def test_placeholder():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule, GeneralModule


def _general_module_classes() -> list:
    # pylint: disable=C0415
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import GeneralModule

    classes = []
    main_dir = Path(__file__).parent.parent / 'main'
    for file in sorted(main_dir.glob('*.py')):
        if file.stem.endswith('_pytest'):
            continue

        mod = importlib.import_module(f'ansible_collections.oxlorg.opnsense.plugins.module_utils.main.{file.stem}')
        for _, cls in inspect.getmembers(mod, inspect.isclass):
            if issubclass(cls, GeneralModule) and cls is not GeneralModule and cls.__module__ == mod.__name__:
                classes.append(cls)

    return classes


def test_general_modules_compare_enabled():
    # single-settings APIs have no 'toggle' endpoint, so 'enabled' is only applied if it is compared like any other
    #   setting; otherwise a change of 'enabled' alone is ignored (see issue #511)
    classes = _general_module_classes()
    assert len(classes) > 0

    missing = [
        f'{cls.__module__}.{cls.__name__}'
        for cls in classes
        if 'enabled' in cls.FIELDS_ALL and 'enabled' not in cls.FIELDS_CHANGE
    ]
    assert not missing, f"'enabled' is in FIELDS_ALL but not in FIELDS_CHANGE: {missing}"


def _settings_for(cls) -> dict:
    # an existing settings-entry in the simplified (ansible) format
    settings = {}
    typing = getattr(cls, 'FIELDS_TYPING', {})
    for field in cls.FIELDS_ALL:
        if field in typing.get('bool', []):
            settings[field] = False

        elif field in typing.get('list', []):
            settings[field] = []

        elif field in typing.get('int', []):
            settings[field] = 1

        else:
            settings[field] = ''

    return {**settings, **SETTINGS_OVERRIDE.get(cls.__module__.rsplit('.', 1)[-1], {})}


# values that pass the module's own validation
SETTINGS_OVERRIDE = {
    'acme_general': {
        'challenge_port': 43580, 'tls_challenge_port': 43581, 'restart_timeout': 600, 'log_level': 'normal',
    },
}


def _run(cls, monkeypatch, existing: dict, params: dict, check_mode: bool = False) -> (dict, list):
    module = MockAnsibleModule()
    module.params.update({**existing, **params, 'reload': False})
    module.check_mode = check_mode
    result = {'changed': False, 'diff': {'before': {}, 'after': {}}}
    posts = []

    instance = cls(module=module, result=result)
    monkeypatch.setattr(instance, 'search_call', lambda: dict(existing))
    monkeypatch.setattr(instance, '_api_post', lambda cnf: posts.append(cnf) or {})
    instance.check()
    instance.process()
    return result, posts


def _sent_value(cls, post: dict, field: str):
    data = post['data']
    for key in (getattr(cls, 'API_KEY_PATH_REQ', None) or cls.API_KEY_PATH).split('.'):
        data = data[key]

    return data[cls.FIELDS_TRANSLATE.get(field, field) if hasattr(cls, 'FIELDS_TRANSLATE') else field]


@pytest.mark.parametrize('enabled', [True, False])
@pytest.mark.parametrize('module_name', ['acme_general', 'postfix_general'])
def test_general_enabled_only_change(monkeypatch, module_name: str, enabled: bool):
    # issue #511: a change of 'enabled' alone was ignored; with #510 alone it failed with KeyError 'toggle'
    cls = importlib.import_module(
        f'ansible_collections.oxlorg.opnsense.plugins.module_utils.main.{module_name}'
    ).General
    existing = {**_settings_for(cls), 'enabled': not enabled}

    result, posts = _run(cls, monkeypatch, existing=existing, params={'enabled': enabled})
    assert result['changed']
    assert len(posts) == 1
    assert posts[0]['command'] == cls.CMDS['set']
    assert _sent_value(cls, posts[0], 'enabled') in (int(enabled), str(int(enabled)))

    # rerun once the firewall has the new state
    result, posts = _run(cls, monkeypatch, existing={**existing, 'enabled': enabled}, params={'enabled': enabled})
    assert not result['changed']
    assert len(posts) == 0

    # check mode reports the change but sends nothing
    result, posts = _run(cls, monkeypatch, existing=existing, params={'enabled': enabled}, check_mode=True)
    assert result['changed']
    assert len(posts) == 0

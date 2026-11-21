from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.api import \
    Session
from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.module import BaseModule


class GwGroup(BaseModule):
    # OPNsense manages gateway groups through the API since 26.7 (models/OPNsense/Routing/GatewayGroups.xml)
    FIELD_ID = 'name'
    CMDS = {
        'add': 'add',
        'del': 'del',
        'set': 'set',
        'search': 'search',
        'detail': 'get',
    }
    API_KEY_PATH = 'gateway_group'
    API_MOD = 'routing'
    API_CONT = 'group_settings'
    TIERS = ['tier1', 'tier2', 'tier3', 'tier4', 'tier5']
    FIELDS_CHANGE = [*TIERS, 'trigger', 'pool_options', 'description']
    FIELDS_ALL = [FIELD_ID, *FIELDS_CHANGE]
    FIELDS_TRANSLATE = {
        'tier1': 'item',
        'tier2': 'item2',
        'tier3': 'item3',
        'tier4': 'item4',
        'tier5': 'item5',
        'pool_options': 'poolopts',
        'description': 'descr',
    }
    FIELDS_TYPING = {
        'list': TIERS,
        'select': ['trigger', 'pool_options'],
    }
    STR_VALIDATIONS = {
        'name': r'^[a-zA-Z0-9_\-]{1,32}$',
    }
    EXIST_ATTR = 'group'

    def __init__(self, module: AnsibleModule, result: dict, session: Session = None, fail: dict = None):
        BaseModule.__init__(self=self, m=module, r=result, s=session, f=fail)
        self.group = {}

    def check(self) -> None:
        if self.p['state'] == 'present':
            if not any(len(self.p[tier]) > 0 for tier in self.TIERS):
                self.m.fail_json(
                    'You need to provide at least one gateway in one of the tiers '
                    f"({', '.join(self.TIERS)}) to create a gateway group!"
                )

            for tier in self.TIERS:
                self.p[tier] = sorted(set(self.p[tier]))

        self._base_check()

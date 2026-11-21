from copy import deepcopy
from re import match as regex_match

from ansible_collections.oxlorg.opnsense.plugins.module_utils.test.testdata.base_testdata import MockOPNsenseController

GATEWAYS = {
    'LAN_GW': 'LAN_GW - 172.24.119.1',
    'TEST-GW': 'TEST-GW - 172.29.236.1',
    'WAN_DHCP': 'WAN_DHCP - inet',
}
TIERS = ['item', 'item2', 'item3', 'item4', 'item5']
TRIGGERS = {
    'down': 'Member Down',
    'downloss': 'Packet Loss',
    'downlatency': 'High Latency',
    'downlosslatency': 'Packet Loss and High Latency',
}
POOL_OPTIONS = {
    '': 'Default',
    'round-robin': 'Round Robin',
    'round-robin sticky-address': 'Round Robin with Sticky Address',
}


class GatewayGroupTestdata(MockOPNsenseController):
    """
    Emulates the OPNsense 26.7 gateway-group API (see: OPNsense/Routing/Api/GroupSettingsController.php)
    * the tiers 'item' to 'item5' are multi-selects of the gateway names
    * 'search' returns display values, 'get' returns the selections
    * a group needs at least one gateway and can't be renamed (OPNsense/Routing/GatewayGroups.php)
    """

    def __init__(self):
        super().__init__()
        self.state = {}
        self.calls = []

    def commands(self) -> dict:
        return {
            'search': self._search,
            'get': self._detail,
            'add': self._add,
            'set': self._set,
            'del': self._del,
            'reconfigure': self._reconfigure,
        }

    def route_kwargs(self, method) -> list:
        return {
            self._search: ['data'],
            self._detail: ['params'],
            self._add: ['data'],
            self._set: ['uuid', 'data'],
            self._del: ['uuid'],
            self._reconfigure: [],
        }[method]

    def mutations(self) -> list:
        return [call for call in self.calls if call[0] in ['add', 'set', 'del']]

    @staticmethod
    def _selection(options: dict, selected: list) -> dict:
        return {key: {'value': label, 'selected': int(key in selected)} for key, label in options.items()}

    def _search(self, data: dict = None) -> dict:
        del data
        self.calls.append(('search', None))
        rows = []
        for uuid, entry in self.state.items():
            row = {
                'uuid': uuid,
                'name': entry['name'],
                'trigger': TRIGGERS[entry['trigger']],
                'poolopts': POOL_OPTIONS[entry['poolopts']],
                'descr': entry['descr'],
                'gateways': {},
            }
            for idx, tier in enumerate(TIERS):
                gws = [gw for gw in entry[tier].split(',') if gw != '']
                row[tier] = ', '.join(GATEWAYS[gw] for gw in gws)
                row['gateways'][idx + 1] = [{'name': gw, 'label': 'success'} for gw in gws]

            rows.append(row)

        return {'rows': rows, 'rowCount': len(rows), 'total': len(rows), 'current': 1}

    def _detail(self, params: list, data: dict = None) -> dict:
        del data
        entry = self.state.get(params[0]) if len(params) > 0 else None
        if entry is None:
            entry = {'name': '', 'trigger': 'down', 'poolopts': '', 'descr': '', **{t: '' for t in TIERS}}

        out = {
            'name': entry['name'],
            'trigger': self._selection(TRIGGERS, [entry['trigger']]),
            'poolopts': self._selection(POOL_OPTIONS, [entry['poolopts']]),
            'descr': entry['descr'],
        }
        for tier in TIERS:
            out[tier] = self._selection(GATEWAYS, entry[tier].split(','))

        return {'gateway_group': out}

    def _validate(self, data: dict, uuid: str = None) -> dict:
        errors = {}
        if regex_match(r'^[a-zA-Z0-9_\-]{1,32}$', data.get('name', '')) is None:
            errors['gateway_group.name'] = 'A valid group name must be specified.'

        if uuid is not None and self.state[uuid]['name'] != data.get('name'):
            errors['gateway_group.name'] = 'Changing name on a gateway group is not allowed.'

        if data.get('name') in GATEWAYS:
            errors['gateway_group.name'] = 'A gateway group cannot have the same name with a gateway.'

        gateways = []
        for tier in TIERS:
            for gw in str(data.get(tier, '')).split(','):
                if gw == '':
                    continue

                if gw not in GATEWAYS:
                    errors[f'gateway_group.{tier}'] = 'Option not in list.'

                gateways.append(gw)

        if len(gateways) == 0:
            errors['gateway_group.item'] = 'At least one tier must be set.'

        if data.get('trigger') not in TRIGGERS:
            errors['gateway_group.trigger'] = 'Option not in list.'

        if data.get('poolopts') not in POOL_OPTIONS:
            errors['gateway_group.poolopts'] = 'Option not in list.'

        return errors

    def _store(self, data: dict) -> dict:
        return {
            'name': data['name'],
            'trigger': data['trigger'],
            'poolopts': data['poolopts'],
            'descr': data.get('descr', ''),
            **{tier: str(data.get(tier, '')) for tier in TIERS},
        }

    def _add(self, data: dict) -> dict:
        data = data['gateway_group']
        self.calls.append(('add', deepcopy(data)))
        errors = self._validate(data)
        if len(errors) > 0:
            return {'result': 'failed', 'validations': errors}

        uuid = self._new_uuid()
        self.state[uuid] = self._store(data)
        return {'result': 'saved', 'uuid': uuid}

    def _set(self, uuid: str, data: dict) -> dict:
        data = data['gateway_group']
        self.calls.append(('set', deepcopy(data)))
        if uuid not in self.state:
            return {'result': 'failed'}

        errors = self._validate(data, uuid=uuid)
        if len(errors) > 0:
            return {'result': 'failed', 'validations': errors}

        self.state[uuid] = self._store(data)
        return {'result': 'saved'}

    def _del(self, uuid: str) -> dict:
        self.calls.append(('del', uuid))
        if uuid in self.state:
            self.state.pop(uuid)
            return {'result': 'deleted'}

        return {'result': 'not found'}

    def _reconfigure(self) -> dict:
        self.calls.append(('reconfigure', None))
        return {'status': 'ok'}

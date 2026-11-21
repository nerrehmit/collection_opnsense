#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (C) 2026, nerrehmit
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/core/routing.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.handler import \
    module_dependency_error, MODULE_EXCEPTIONS

try:
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.base.wrapper import module_wrapper
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.main import \
        OPN_MOD_ARGS, STATE_ONLY_MOD_ARG, RELOAD_MOD_ARG
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.gateway_group import GwGroup

except MODULE_EXCEPTIONS:
    module_dependency_error()


# DOCUMENTATION = 'https://ansible-opnsense.oxl.app/modules/route.html'
# EXAMPLES = 'https://ansible-opnsense.oxl.app/modules/route.html'


def _tier_arg(tier: int) -> dict:
    return dict(
        type='list', elements='str', required=False, default=[],
        description=f'Names of the gateways in tier {tier}. '
                    'Lower tiers are preferred, gateways in the same tier share the load',
    )


def run_module():
    module_args = dict(
        name=dict(
            type='str', required=True,
            description="Unique name of the gateway group. Only 'a-zA-Z0-9_-', at most 32 characters. "
                        "OPNsense doesn't allow renaming a gateway group",
        ),
        tier1=_tier_arg(1),
        tier2=_tier_arg(2),
        tier3=_tier_arg(3),
        tier4=_tier_arg(4),
        tier5=_tier_arg(5),
        trigger=dict(
            type='str', required=False, default='down', aliases=['trigger_level'],
            choices=['down', 'downloss', 'downlatency', 'downlosslatency'],
            description="When to switch to the next tier: 'down' (member down), 'downloss' (packet loss), "
                        "'downlatency' (high latency) or 'downlosslatency' (packet loss or high latency)",
        ),
        pool_options=dict(
            type='str', required=False, default='', aliases=['poolopts'],
            choices=['', 'round-robin', 'round-robin sticky-address'],
            description='How to balance the gateways of a tier. Empty for the default',
        ),
        description=dict(type='str', required=False, default='', aliases=['desc']),
        **RELOAD_MOD_ARG,
        **STATE_ONLY_MOD_ARG,
        **OPN_MOD_ARGS,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        }
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    module_wrapper(GwGroup(module=module, result=result))
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

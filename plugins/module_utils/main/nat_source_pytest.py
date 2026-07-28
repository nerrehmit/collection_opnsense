from ansible_collections.oxlorg.opnsense.plugins.module_utils.main.nat_source import SNat


def test_nat_source_uses_rule_endpoints():
    assert SNat.CMDS['search'] == 'search_rule'
    assert SNat.CMDS['detail'] == 'get_rule'
    assert SNat.API_KEY_PATH == 'rule'

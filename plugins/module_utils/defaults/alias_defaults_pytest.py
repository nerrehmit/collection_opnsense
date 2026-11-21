def test_categories_is_exposed():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.alias import ALIAS_MOD_ARGS

    assert 'categories' in ALIAS_MOD_ARGS
    assert ALIAS_MOD_ARGS['categories']['type'] == 'list'


def test_asn_type_is_exposed():
    from ansible_collections.oxlorg.opnsense.plugins.module_utils.defaults.alias import ALIAS_MOD_ARGS

    # OPNsense alias type 'BGP ASN', content is validated by helper.alias.validate_values
    assert 'asn' in ALIAS_MOD_ARGS['type']['choices']

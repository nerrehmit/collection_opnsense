.. _modules_routing:

.. include:: ../_include/head.rst

=======
Routing
=======

**STATE**: stable

Static Routes
=============

**TESTS**: `route <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/route.yml>`_

**API Docs**: `Core - Routes <https://docs.opnsense.org/development/api/core/routes.html>`_

**Service Docs**: `Routes <https://docs.opnsense.org/manual/routes.html>`_

Gateways
========

**TESTS**: `gateway <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/gateway.yml>`_

**API Docs**: `Core - routings <https://docs.opnsense.org/development/api/core/routing.html>`_

**Service Docs**: `routings <https://docs.opnsense.org/manual/gateways.html>`_

Gateway Groups
==============

**STATE**: testing

**TESTS**: `gateway_group <https://github.com/O-X-L/ansible-opnsense/blob/latest/tests/gateway_group.yml>`_

**API Docs**: `Core - routings <https://docs.opnsense.org/development/api/core/routing.html>`_

**Service Docs**: `Gateway groups <https://docs.opnsense.org/manual/how-tos/multiwan.html>`_

Needs OPNsense 26.7 or newer, older releases manage gateway groups outside the API.

Contribution
************

Thanks to `@kdhlab <https://github.com/kdhlab>`_ for developing the :code:`gateway` module!

Thanks to `@Rath <https://github.com/superstes>`_ for developing the :code:`route` module!

----

Definition
**********

.. include:: ../_include/param_basic.rst

oxlorg.opnsense.route
=========================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "gateway","string","true","\-","gw","An existing gateway that should be used as target for the network. The network ip protocol (*IPv4/IPv6*) must be the same! **WARNING**: You need to supply the gateways short-name as can be seen in the WEB-UI menu 'System - Gateways - Single - Name'"
    "network","string","true","\-","nw, net","Network to route. The network ip protocol (*IPv4/IPv6*) must be the same!"
    "description","string","false","\-","desc","Optional description for the route. Could be used as unique-identifier when set as only 'match_field'."
    "match_fields","list of strings","false","['network', 'gateway']","\-","Fields that are used to match configured routes with the running config - if any of those fields are changed, the module will think it's a new route"
    "reload","boolean","false","true","\-", .. include:: ../_include/param_reload.rst

oxlorg.opnsense.gateway
===========================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "name","string","true","\-","\-","Gateway Name"
    "interface","string","true","\-","int, if","Interface belonging to this gateway"
    "ip_protocol","string","false","\-","\-","Internet Protocol this gateway uses. Possible options: ['inet', 'inet6']. Required if no gateway is set."
    "gateway","string","true","\-","gw, ip","Gateway IP"
    "description","string","false","\-","desc","Optional description for the Gateway. Could be used as unique-identifier when set as only 'match_field'."
    "default_gw","string","true","\-","default, internet, inet","This will select the above gateway as a default gateway candidate."
    "far_gw","string","false","\-","far","This will allow the gateway to exist outside of the interface subnet."
    "monitor_disable","boolean","false","false","\-","Disable gateway monitoring"
    "monitor_noroute","boolean","false","false","\-","Do not create a dedicated host route for this monitor."
    "monitor","string","false","\-","\-","IP address to use as a monitor IP for the gateway."
    "force_down","boolean","false","false","down","Force the gateway to be considered as down."
    "priority","integer","false","255","prio","Choose a value between 1 and 255. Influences sort order when selecting a (default) gateway, lower means more important."
    "weight","integer","false","1","\-","Weight for this gateway when used in a gateway group. Specificed as an integer number between 1 and 5."
    "latency_low","integer","false","200","\-","Latency threshold in milliseconds. If the latency is lower than this value, the gateway is considered as up."
    "latency_high","integer","false","500","\-","Latency threshold in milliseconds. If the latency is higher than this value, the gateway is considered as down."
    "loss_low","integer","false","10","\-","Packet loss threshold in percent. If the packet loss is lower than this value, the gateway is considered as up."
    "loss_high","integer","false","20","\-","Packet loss threshold in percent. If the packet loss is higher than this value, the gateway is considered as down."
    "interval","integer","false","1","\-","How often that an ICMP probe will be sent in seconds."
    "time_period","integer","false","60","\-","The time period over which results are averaged."
    "loss_interval","integer","false","4","\-","Time interval before packets are treated as lost."
    "data_length","integer","false","0","\-","Size of ICMP packets to send."
    "match_fields","list of strings","false","['name', 'gateway']","\-","Fields that are used to match configured gateways with the running config - if any of those fields are changed, the module will think it's a new gateway, possible options: ['name', 'gateway', 'description']"
    "reload","boolean","false","true","\-", .. include:: ../_include/param_reload.rst

oxlorg.opnsense.gateway_group
=============================

..  csv-table:: Definition
    :header: "Parameter", "Type", "Required", "Default", "Aliases", "Comment"
    :widths: 15 10 10 10 10 45

    "name","string","true","\-","\-","Unique name of the gateway group. Only letters, digits, '-' and '_', at most 32 characters. It must not be the name of a gateway. OPNsense doesn't allow renaming a gateway group, so a new name creates a new group"
    "tier1","list of strings","false for deletion, else at least one tier","[]","\-","Names of the gateways in tier 1, as shown in 'System - Gateways - Configuration - Name'. Lower tiers are preferred, gateways in the same tier share the load"
    "tier2","list of strings","false","[]","\-","Names of the gateways in tier 2"
    "tier3","list of strings","false","[]","\-","Names of the gateways in tier 3"
    "tier4","list of strings","false","[]","\-","Names of the gateways in tier 4"
    "tier5","list of strings","false","[]","\-","Names of the gateways in tier 5"
    "trigger","string","false","'down'","trigger_level","When to switch to the next tier. One of: 'down' (member down), 'downloss' (packet loss), 'downlatency' (high latency), 'downlosslatency' (packet loss or high latency)"
    "pool_options","string","false","''","poolopts","How to balance the gateways of a tier. One of: '' (default), 'round-robin', 'round-robin sticky-address'"
    "description","string","false","''","desc","Optional description"
    "reload","boolean","false","false","apply", .. include:: ../_include/param_reload.rst

----

Usage
*****

First you will have to know about **route-matching**.

The module somehow needs to link the configured and existing routes to manage them.

You can to set how this matching is done by setting the 'match_fields' parameter!

The default behaviour is that a route is matched by its 'gateway' and 'network'.

However - it is **recommended** to use/set 'description' as **unique identifier** if many routes are used.

----

Examples
********

oxlorg.opnsense.route
=========================

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.route:
          match_fields: ['description']

        oxlorg.opnsense.list:
          target: 'route'

      tasks:
        - name: Example
          oxlorg.opnsense.route:
            description: 'test1'
            network: '172.16.0.0/12'
            gateway: 'LAN_GW'
            # match_fields: ['description']
            # enabled: true
            # debug: false
            # state: 'present'

        - name: Adding route
          oxlorg.opnsense.route:
            description: 'test2'
            network: '10.206.0.0/16'
            gateway: 'VPN_GW'
            # match_fields: ['description']

        - name: Disabling route
          oxlorg.opnsense.route:
            description: 'test3'
            network: '10.55.0.0/16'
            gateway: 'VPN_GW'
            enabled: false
            # match_fields: ['description']

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'route'
          register: existing_entries

        - name: Printing routes
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Removing route 'test3'
          oxlorg.opnsense.route:
            description: 'test3'
            network: '10.55.0.0/16'
            gateway: 'VPN_GW'
            state: 'absent'
            match_fields: ['description']

oxlorg.opnsense.gateway
===========================

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.gateway:
          match_fields: ['description']

        oxlorg.opnsense.list:
          target: 'gateway'

      tasks:
        - name: List Gateways
          oxlorg.opnsense.list:
          register: existing_entries

        - name: Add Gateway
          oxlorg.opnsense.gateway:
            name: 'Test_GW'
            interface: 'wg1'
            gateway: '10.255.255.16'

        - name: Set Gateway Monitor IP
          oxlorg.opnsense.gateway:
            name: 'Test_GW'
            interface: 'wg1'
            gateway: '10.255.255.16'
            monitor: '1.1.1.1'

        - name: Delete Gateway
          oxlorg.opnsense.gateway:
            name: 'Test_GW'
            state: absent

oxlorg.opnsense.gateway_group
=============================

.. code-block:: yaml

    - hosts: firewalls
      connection: local
      gather_facts: false
      module_defaults:
        group/oxlorg.opnsense.all:
          firewall: 'opnsense.template.opnsense.oxl.app'
          api_credential_file: '/home/guy/.secret/opn.key'

        oxlorg.opnsense.list:
          target: 'gateway_group'

      tasks:
        - name: Failover from WAN1 to WAN2
          oxlorg.opnsense.gateway_group:
            name: 'WAN_FAILOVER'
            tier1: ['WAN1_GW']
            tier2: ['WAN2_GW']
            trigger: 'downloss'
            description: 'Use WAN2 when WAN1 is down or loses packets'
            # tier3: []
            # tier4: []
            # tier5: []
            # pool_options: ''
            # reload: false
            # state: 'present'

        - name: Load balancing over WAN1 and WAN2
          oxlorg.opnsense.gateway_group:
            name: 'WAN_LOADBALANCE'
            tier1: ['WAN1_GW', 'WAN2_GW']
            pool_options: 'round-robin sticky-address'
            reload: true

        - name: Listing
          oxlorg.opnsense.list:
          #  target: 'gateway_group'
          register: existing_entries

        - name: Printing gateway groups
          ansible.builtin.debug:
            var: existing_entries.data

        - name: Removing a gateway group
          oxlorg.opnsense.gateway_group:
            name: 'WAN_LOADBALANCE'
            state: 'absent'

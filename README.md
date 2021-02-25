# Ansible Dynamic Inventory for MySQL

This is a [Dynamic Inventory](http://docs.ansible.com/ansible/intro_dynamic_inventory.html) for [Ansible](https://github.com/ansible/ansible) to be used together with MySQL.

It was written because we maintain a lot of servers and static inventory files did not meet our demand, and we like MySQL.

## Usage

Simply call the script like the following

```
ansible-playbook -i mysql.py
# or
ansible -i mysql.py
```

Limitations also work

```
ansible-playbook -i mysql.py --limit foo.bar.com
ansible-playbook -i mysql.py --limit groupFoo
```

## Setup
I won't explain the process of installing a database or creating the tables, see `tables.sql` for the required MySQL structure.

Once setup rename `mysql.ini.dist` to `mysql.ini` to suit your needs, if you don't want to use caching just put it on 0.

### Groups
In the table `group` you create the groups you need and their variables,

### Hosts
In the table `host` under `host` you place the IP/DNS for the system. This will be used as ansible_host fact.

#### Inventory_hostname
Under `hostname` you can fill in a unique hostname, this will typically be used as the host's primary key (==`inventory_hostname`).
You can modify the field to be used as `inventory_hostname` by changing the `inventory_hostname` variable in `mysql.ini`.
Make sure this is a unique key field (e.g. `host` or `hostname`), the default for `inventory_hostname` is `host` (backward compatible).

### Relation between Hosts and Groups
The table `hostgroups` maps the relation between `host` and `group` using two `FOREIGN KEYS`.

#### Children
Groups can have other groups as children, use the table `childgroups`.


#### Inventory_groups
By default only groups from `hostgroups` and groups from `childgroups` having a child group from `hostgroups` will be included into the inventory (i.e. max. two group levels).
You can include all groups from `hostgroups`and `childgroups` by changing the `inventory_groups` variable in `mysql.ini` to `all`.
This allows you to define group hierarchies of any depth and complexity.

### Note on Variables
This applies to `host` and `group` respectively.
If no variables are needed either NULL it (actual MySQL `NULL` not the `string`) or use `{}`.


## LICENSE
```
# Copyright (c) 2015 Productsup GmbH, Yorick Terweijden yt@products-up.de
#
# As it is mostly based on the original Cobbler Dynamic Inventory
# https://github.com/ansible/ansible/blob/devel/contrib/inventory/cobbler.py
# the same license, the GPL-3 applies.
```

The [GPL-3](http://www.gnu.org/licenses/gpl-3.0.en.html) can be found under the link.

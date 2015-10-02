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
In the table `host` under `host` you place the IP/DNS for the system.

#### Facts
Under `hostname` you can fill in a value, this will be presented as a variable `inventory_hostname` during the play.
You can modify the name of this Fact variable by changing the `facts_hostname_var` variable in my `mysql.ini`.

### Relation between Hosts and Groups
The table `hostgroups` maps the relation between `host` and `group` using two `FOREIGN KEYS`.

#### Children
Groups can have other groups as children, use the table `childgroups`.

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

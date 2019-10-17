import logging
import shutil
from typing import Iterator, List, Dict, Optional

import ansible.constants as C
from ansible import context
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.become import Become
from ansible.playbook.play import Play
from ansible.plugins.callback import CallbackBase
from ansible.vars.manager import VariableManager

from ansib.server.common.config import CONF

LOG = logging.getLogger(__name__)


class AnsibleExecutor(object):

    def __init__(self):

        become = Become()
        # Since the API is constructed for CLI it expects certain options to
        # always be set in the context object
        context.CLIARGS = ImmutableDict(
            connection='local',
            module_path=['/to/mymodules'],
            forks=1,
            become=become,
            become_method=None,
            become_user=None,
            check=False,
            diff=False,
        )

        self._loader = None
        self._results_callback = None
        self._inventory = None
        self.__variable_manager = None
        self._play = None

        self._init_data_loader()
        self._init_inventory()
        self._init_variable_manager()

    def _init_data_loader(self) -> None:
        """ Initialize needed objects

        Takes care of finding and reading yaml
        """
        self._loader = DataLoader()

    def _init_inventory(self):
        # create inventory, use path to host config file as source or
        # hosts in a comma separated string
        self._inventory = InventoryManager(
            loader=self._loader,
            sources='localhost,',
        )

    def _init_variable_manager(self):
        """
        Variable manager takes care of merging all the different sources
        to give you a unified view of variables available in each context
        """
        self._variable_manager = VariableManager(
            loader=self._loader,
            inventory=self._inventory,
        )

    def _init_tasks(self, gather_facts: bool, tasks: List[Dict]):
        # Create data structure that represents our play, including tasks,
        # this is basically what our YAML loader does internally.
        # Example:
        # {
        #    'name': 'Get list of files',
        #    'command': 'ls',
        #    'register': 'ls_out'
        # },
        # {
        #    'name': 'Print list of files',
        #    'debug': {
        #        'msg': '{{ls_out.stdout_lines}}',
        #    }
        # },

        play_source = {
            'name': "Ansible Playbook",
            'hosts': CONF.ansible.host or 'localhost',
            'become': CONF.ansible.become or False,
            'gather_facts': gather_facts,
            'tasks': [
                {
                    'name': 'Print playbook dir',
                    'debug': {
                        'msg': 'This path where agent is running: '
                               '{{playbook_dir}}'
                    },
                },
            ]
        }

        if type(tasks) == list:
            play_source['tasks'].extend(tasks)

        # Create play object, playbook objects use .load instead of init
        # or new methods, this will also automatically create the task objects
        # from the info provided in play_source
        self._play = Play().load(
            play_source,
            variable_manager=self._variable_manager,
            loader=self._loader,
        )

    def set_result_callback(self, callback: Optional[CallbackBase]) -> None:
        """
        Instantiate our ResultCallback for handling results as they come in.
        Ansible expects this to be one of its main display outlets
        """
        self._results_callback = callback

    def execute(self, gather_facts: bool, tasks: List[Dict]) -> Iterator:
        """
        Run it - instantiate task queue manager, which takes care of forking
        and setting up all objects to iterate over host list and tasks
        """
        self._init_tasks(gather_facts, tasks)
        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self._inventory,
                variable_manager=self._variable_manager,
                loader=self._loader,
                # passwords=dict(vault_pass='secret'),
                passwords=dict(),
                stdout_callback=self._results_callback,
                # Use our custom callback instead of the
                # ``default`` callback plugin, which prints to stdout
            )
            # most interesting data for a play is actually sent
            # to the callback's methods
            result = tqm.run(self._play)
            return result
        finally:
            # we always need to cleanup child procs and the structures we
            # use to communicate with them
            if tqm is not None:
                tqm.cleanup()

            # Remove ansible tmpdir
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

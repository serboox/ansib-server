import logging

from ansible.plugins.callback import CallbackBase

LOG = logging.getLogger(__name__)


class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    _result_list = None

    def __init__(self, display=None, options=None):
        self._result_list = list()
        super(ResultCallback, self).__init__(display, options)

    def set_results_list(self, res_list):
        self._result_list = res_list

    def get_results_list(self):
        return self._result_list

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self._result_list.append({host: result._result})
        # self.runner_on_ok(host, result._result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self._result_list.append({host: result._result})
        # self.runner_on_failed(host, result._result, ignore_errors)

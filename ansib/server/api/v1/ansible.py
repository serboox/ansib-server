import base64
import http
import logging
import os
import threading
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional

from ansible.executor.task_queue_manager import TaskQueueManager

from ansib.server.ansible.executor import AnsibleExecutor
from ansib.server.ansible.result_callback import ResultCallback
from ansib.server.common import constants
from ansib.server.common import exceptions
from ansib.server.common import rest_plus
from ansib.server.common.config import CONF

LOG = logging.getLogger(__name__)

postBodyLock = threading.Lock()
postBody = ''


class Ansible(rest_plus.Resource):
    collection = constants.ANSIBLE

    # @common.marshal_with(flavor_models.response,
    #                     envelope=constants.ANSIBLE)
    def get(self) -> Tuple[Any, Optional[int], Optional[Dict]]:
        """
        Test method.

        GET /api/v1/ansible/
        """
        res = {
            'message': 'You should use POST method!',
        }
        headers = {
            constants.CONTENT_TYPE: constants.APPLICATION_JSON,
        }
        return res, http.HTTPStatus.FORBIDDEN, headers

    def post(self) -> Tuple[Any, Optional[int], Optional[Dict]]:
        """
        Execute ansible playbook.

        POST /api/v1/ansible/
        """
        global postBodyLock, postBody
        if not postBodyLock.acquire(False):
            # LOG.debug("Not access GET LOCK")
            headers = {
                constants.CONTENT_TYPE: constants.APPLICATION_JSON,
            }
            return postBody, http.HTTPStatus.LOCKED, headers
        else:
            try:
                # LOG.debug("GET LOCK")
                return self._post_activity()
            finally:
                # LOG.debug("RETURN LOCK")
                postBodyLock.release()

    def _post_activity(self) -> Tuple[Any, Optional[int], Optional[Dict]]:
        global postBody
        headers = {
            constants.CONTENT_TYPE: constants.APPLICATION_JSON,
        }
        req_body, err = self.request_body_json()
        # LOG.debug("REQUEST: body:%s err:%s" % (req_body, err))
        if err is not None:
            LOG.error(err)
            return exceptions.ValidationException(
                detail="Unsupported request body",
                exception=err,
            ), None, headers
        postBody = req_body.copy()
        postBody['start_time'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        if 'files' in req_body.keys() and len(req_body['files']) > 0:
            try:
                self._save_files(req_body['files'])
            except Exception as err:
                LOG.error(err)
                return exceptions.SaveFileException(
                    detail="Something went wrong",
                    exception=err,
                ), http.HTTPStatus.INTERNAL_SERVER_ERROR, headers

        res_array = list()
        executor = AnsibleExecutor()
        result_callback = None
        if not bool(CONF.ansible.stdout_result_callback):
            result_callback = ResultCallback()
            result_callback.set_results_list(res_array)

        gather_facts = req_body.get('gather_facts', False)

        executor.set_result_callback(result_callback)
        result_code = executor.execute(
            gather_facts=gather_facts,
            tasks=req_body.get('tasks', []),
        )

        if 'files' in req_body.keys() and len(req_body['files']) > 0:
            try:
                self._remove_files(req_body['files'])
            except Exception as err:
                LOG.error(err)
                return exceptions.RemoveFileException(
                    detail="Something went wrong",
                    exception=err,
                ), http.HTTPStatus.INTERNAL_SERVER_ERROR, headers

        if TaskQueueManager.RUN_OK == result_code:
            return res_array, http.HTTPStatus.OK, headers
        return res_array, http.HTTPStatus.BAD_REQUEST, headers

    @staticmethod
    def _save_files(create_files: List[Dict]) -> Exception:
        for create_file in create_files:
            file_path, base64_str = create_file['path'], create_file['data']
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)
            file = open(file_path, 'bw+')
            err = None
            try:
                data = base64.b64decode(bytes(base64_str, 'utf-8'))
                LOG.debug("Created file '%s'" % file_path)
                file.write(data)
            except Exception as error:
                LOG.error(err)
                err = error
            finally:
                file.close()
            return err

    @staticmethod
    def _remove_files(create_files: List[Dict]) -> Exception:
        for create_file in create_files:
            file_path = create_file['path']
            try:
                os.remove(file_path)
            except Exception as err:
                LOG.error(err)
                return err


class AnsibleAPI(rest_plus.API):
    _name = constants.ANSIBLE
    resources = [Ansible]


APIs = (AnsibleAPI,)

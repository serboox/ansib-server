import abc
import http
import json
import logging
from typing import Any, Tuple, Dict

import flask
import flask_restplus
import six
import yaml
from werkzeug import exceptions as werkzeug_exc

from ansib.server.common import config
from ansib.server.common import constants
from ansib.server.common import exceptions
from ansib.server.db import repositories
from ansib.server.models import error as error_models

CONF = config.CONF

LOG = logging.getLogger(__name__)


def expect(model, **kwargs):
    """
    A decorator to specify the expected input model.

    Used in the same way as Flask-RESTPlus ``namespace.expect`` decorator.
    """

    def _expect(fn):
        fn.expect = (model, kwargs)
        return fn

    return _expect


def marshal_with(fields, **kwargs):
    """
    A decorator specifying the fields to use for serialization.

    Used in the same way as Flask-RESTPlus ``namespace.marshal_with``
    decorator.
    """

    def _marshal_with(fn):
        fn.marshal_with = (fields, kwargs)
        return fn

    return _marshal_with


@six.add_metaclass(abc.ABCMeta)
class API(object):
    ERRORS = [
        http.HTTPStatus.BAD_REQUEST,
        http.HTTPStatus.FORBIDDEN,
        http.HTTPStatus.NOT_FOUND,
    ]

    @property
    @abc.abstractmethod
    def _name(self):
        """Override with an attr consisting of the API Name, 'datastores'."""
        raise NotImplementedError()

    @property
    def namespace(self):
        return self.__namespace

    def __init__(self, version=None):
        self.__namespace = flask_restplus.Namespace(
            name=self._name,
            description=self._name.capitalize(),
            default_mediatype=constants.APPLICATION_JSON)
        self._add_resources()

    def _decorators(self, method, is_member=False):
        responses = {}
        statuses = self.ERRORS.copy()

        if method == 'POST' and not is_member:
            statuses.insert(0, http.HTTPStatus.OK)
        if method == 'DELETE':
            statuses.insert(0, http.HTTPStatus.NO_CONTENT)
        for status in statuses:
            if (status == http.HTTPStatus.NOT_FOUND and
                    (method not in ('GET', 'PUT', 'DELETE') or not is_member)):
                continue
            responses[status.value] = status.phrase
            if status in self.ERRORS:
                responses[status.value] = (
                    responses[status.value],
                    error_models.error(
                        self.namespace, status.value, status.phrase),
                    dict(envelope=constants.ERROR),
                )
        return [self.namespace.doc(responses=responses)]

    @classmethod
    def register_to_api(cls, api, version):
        instance = cls(version=version)
        api.add_namespace(instance.namespace)

    def _expect(self, method_fn):
        if not hasattr(method_fn, 'expect'):
            return method_fn
        model_fn, exp_kwargs = method_fn.expect
        model = model_fn(self.namespace)

        return self.namespace.expect(model, **exp_kwargs)(method_fn)

    def _marshal_with(self, method_fn):
        if not hasattr(method_fn, 'marshal_with'):
            return method_fn
        model_fn, marshal_kwargs = method_fn.marshal_with
        model = model_fn(self.namespace)
        return self.namespace.marshal_with(model, **marshal_kwargs)(method_fn)

    def _add_resources(self):
        def _add_resource(resource, path_prefix=None):
            res, childs = (resource if isinstance(resource, tuple)
                           else (resource, []))
            collection = getattr(res, 'collection', None)
            member = getattr(res, 'member', None)

            path = ''
            if collection and path_prefix is not None:
                path += '/' + collection
            if path_prefix:
                path = path_prefix + path
            if member:
                path = '{}/<string:{}_id>'.format(path, member)

            # Try to apply methods decorators
            for method in res.methods:
                method_fn = getattr(res, method.lower())
                for decorator in (self._expect, self._marshal_with):
                    method_fn = decorator(method_fn)

                for decorator in self._decorators(method, bool(member)):
                    method_fn = decorator(method_fn)

                setattr(res, method.lower(), method_fn)

            self.namespace.add_resource(res, path)

            for child in childs:
                _add_resource(child, path_prefix=path)

        for res in self.resources:
            _add_resource(res)


class Resource(flask_restplus.Resource):

    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.repositories = repositories.Repositories()

    @staticmethod
    def _get_db_object(repo, id, exc=None):
        db_obj = repo.get(id=id)
        if not db_obj:
            resource = repo.model_class.__name__.lower()
            raise exc if exc else exceptions.NotFound(resource=resource, id=id)
        return db_obj

    @property
    def context(self):
        return flask.request.environ.get(constants.REQUEST_CONTEXT_ENV, None)

    @staticmethod
    def request_body_json() -> Tuple[Dict, Any]:
        request_body = flask.request.data
        err = None  # type: Any
        try:
            res = json.loads(request_body.decode('utf-8'))
            if 'tasks' not in res.keys():
                raise ValueError("Key 'tasks' not be found in request.")
        except Exception as err:
            LOG.error(err)
            return {}, err
        return res, err

    @staticmethod
    def request_body_yaml() -> Tuple[Dict, Any]:
        request_body = flask.request.data or {}
        err = None  # type: Any
        try:
            res = yaml.full_load(request_body)
            if 'tasks' not in res.keys():
                raise ValueError("Key 'tasks' not be found in request.")
        except (yaml.YAMLError, ValueError) as err:
            LOG.error(err)
            return {}, err
        return res, err

    def validate_payload(self, *args, **kwargs):
        try:
            super(Resource, self).validate_payload(*args, **kwargs)
        except werkzeug_exc.BadRequest as ex:
            raise exceptions.ValidationException(detail=ex.data['errors'])

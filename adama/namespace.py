from flask import g
from flask.ext import restful

from typing import Dict, Any, List

from .api import APIException, ok, api_url_for
from .namespace_store import namespace_store
from .entity import get_permissions


class Namespace(object):

    def __init__(self, name: str, url: str,
                 description: str,
                 users: Dict[str, List[str]] = None):
        self.name = name
        self.url = url
        self.description = description
        # {user: [methods allowed...]}
        self.users = users or {}

        self.validate_args()

    def validate_args(self):
        if not self.name:
            raise APIException(
                'Namespace cannot be an empty string')

    def to_json(self) -> Dict[str, Any]:
        obj = {
            'name': self.name,
            'url': self.url,
            'users': self.users,
            'description': self.description
            }
        try:
            obj['self'] = api_url_for('namespace', namespace=self.name)
        except RuntimeError:
            # no app context, ignore 'self' field
            pass
        return obj


class NamespaceResource(restful.Resource):

    def get(self, namespace):
        """Get information about a namespace"""

        try:
            ns = namespace_store[namespace]
            return ok({'result': ns.to_json()})
        except KeyError:
            raise APIException(
                "namespace not found: {}'".format(namespace), 404)

    def delete(self, namespace):
        """Delete a namespace"""

        try:
            ns = namespace_store[namespace]
            if 'DELETE' in tuple(get_permissions(ns.users, g.user)):
                del namespace_store[namespace]
            else:
                raise APIException(
                    'user {} does not have permissions for DELETE'
                    .format(g.user))
        except KeyError:
            pass
        return ok({})
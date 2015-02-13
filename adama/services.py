import textwrap

from flask import g
from flask.ext import restful
from werkzeug.datastructures import FileStorage

from .service_store import service_store
from .requestparser import RequestParser
from .tools import namespace_of
from .service import register_code, register_git_repository, post_notifier
from .namespaces import namespace_store
from .api import APIException, ok, api_url_for
from .entity import get_permissions


class ServicesResource(restful.Resource):

    def post(self, namespace):
        """Create new service"""

        if namespace not in namespace_store:
            raise APIException(
                "namespace not found: {}".format(namespace), 404)

        ns = namespace_store[namespace]
        if 'POST' not in get_permissions(ns.users, g.user):
            raise APIException(
                'user {} does not have permissions to POST to '
                'namespace {}'.format(g.user, namespace))

        args = self.validate_post()
        if 'code' in args and 'git_repository' in args:
            raise APIException(
                'cannot have code and git repository at '
                'the same time')

        if 'code' in args or args.get('type') == 'passthrough':
            service = register_code(args, namespace, post_notifier)
        elif 'git_repository' in args:
            service = register_git_repository(args, namespace, post_notifier)
        else:
            raise APIException(
                'no code or git repository specified')

        result = {
            'state_url': api_url_for(
                'service',
                namespace=service.namespace,
                service=service.adapter_name),
            'notification': service.notify
        }
        for endpoint in service.endpoints():
            result[endpoint+'_url'] = api_url_for(
                endpoint,
                namespace=service.namespace,
                service=service.adapter_name)
        return ok({
            'message': 'registration started',
            'result': result
        })

    @staticmethod
    def validate_post():
        parser = RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('type', type=str)
        parser.add_argument('version', type=str)
        parser.add_argument('url', type=str)
        parser.add_argument('whitelist', type=str, action='append')
        parser.add_argument('description', type=str)
        parser.add_argument('requirements', type=str, action='append')
        parser.add_argument('notify', type=str)
        parser.add_argument('json_path', type=str)
        parser.add_argument('main_module', type=str)
        # The following two options are exclusive
        parser.add_argument('code', type=FileStorage, location='files')
        parser.add_argument('git_repository', type=str)
        parser.add_argument('metadata', type=str)

        args = parser.parse_args()

        for key, value in args.items():
            if value is None:
                del args[key]

        return args

    def get(self, namespace):
        """List all services"""

        if namespace not in namespace_store:
            raise APIException(
                "namespace not found: {}".format(namespace), 404)

        result = [srv['service'].to_json()
                  for name, srv in service_store.items()
                  if namespace_of(name) == namespace and
                  srv['service'] is not None]
        return ok({'result': result})

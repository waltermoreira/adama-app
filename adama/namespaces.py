from flask import g
from flask.ext import restful

from typing import Dict, List, Any

from .api import APIException, ok, api_url_for
from .requestparser import RequestParser
from .namespace import Namespace
from .namespace_store import namespace_store


class NamespacesResource(restful.Resource):

    def post(self):
        """Create a new namespace"""

        args = validate_post()
        return ok({'result': register_namespace(args)})

    def get(self):
        """Get list of namespaces"""

        return ok({'result': namespaces()})


def namespaces() -> List[Dict[str, Any]]:
    return [ns.to_json() for (name, ns) in namespace_store.items()]


def validate_post() -> Dict[str, Any]:
    parser = RequestParser()
    parser.add_argument('name', type=str, required=True,
                        help='name of namespace is required')
    parser.add_argument('url', type=str)
    parser.add_argument('description', type=str)
    args = parser.parse_args()
    return args


def register_namespace(args: Dict[str, Any]) -> str:
    name = args['name']
    url = args.get('url', None)
    description = args.get('description', None)

    if name in namespace_store:
        raise APIException("namespace '{}' already exists"
                           .format(name), 400)

    ns = Namespace(name=name, url=url,
                   description=description,
                   users={g.user: ['POST', 'PUT', 'DELETE']})
    namespace_store[name] = ns
    return api_url_for('namespace', namespace=name)


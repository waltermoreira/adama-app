import json

from flask.ext import restful
from typing import Tuple, Dict

from . import __version__
from .api import ok


class StatusResource(restful.Resource):

    def get(self):
        """Return status of the server"""

        return ok(status())


def my_info() -> Tuple[str, str]:
    me = json.load(open('/me.json'))
    return me['Image'], me['Id']


def my_parent() -> Tuple[str, str]:
    parent = json.load(open('/serfnode/parent.json'))
    return parent['Image'], parent['Id']


def status() -> Dict[str, str]:
    my_img, my_cid = my_info()
    parent_img, parent_cid = my_parent()
    return {
        'api': 'Adama v{}'.format(__version__),
        'serfnode_image': parent_img,
        'serfnode_container': parent_cid,
        'adama_image': my_img,
        'adama_container': my_cid
    }
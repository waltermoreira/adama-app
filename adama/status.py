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


def status() -> Dict[str, str]:
    my_img, my_cid = my_info()
    return {
        'api': 'Adama v{}'.format(__version__),
        'image': my_img,
        'container': my_cid
    }
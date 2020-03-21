"""
Handles GitHub statuses
"""
import contextlib

from .deploys import start_deploy, finish_deploy, get_deployment


@contextlib.contextmanager
def deploy_status(deployment_id):
    resp = start_deploy(deployment=deployment_id)
    assert not resp.errors, resp.errors

    try:
        resp = get_deployment(deployment_id)
        assert not resp.errors, resp.errors

        yield resp.data['node']
    except BaseException:
        resp = finish_deploy(deployment=deployment_id, state='ERROR')
        assert not resp.errors, resp.errors
        raise
    else:
        resp = finish_deploy(deployment=deployment_id, state='SUCCESS')
        assert not resp.errors, resp.errors

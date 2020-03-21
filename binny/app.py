import gqlmod
gqlmod.enable_gql_import()  # noqa

import importlib.resources
import logging
import os
import pathlib
import subprocess
import sys

from quart import Quart, request
import quart_github_webhook

from .globals import ghapp
from .checks import get_check_suites

log = logging.getLogger(__name__)


app = Quart(__name__)
app.config.from_object('local_config')


webhook = quart_github_webhook.Webhook(
    app,
    endpoint='/webhook/github',
    secret=app.config['WEBHOOK_SECRET'],
)


@app.route('/status')
async def status():
    """
    Basic status call
    """
    gh_ok = True
    try:
        ghapp.get_this_app()
    except Exception:
        log.exception("Error checking github")
        gh_ok = False

    return (f"""Service: ok
GitHub: {'ok' if gh_ok else 'err'}
""", 200 if gh_ok else 500)


@webhook.hook('check_suite')
async def check_suite(payload):
    """
    https://developer.github.com/v3/activity/events/types/#checksuiteevent
    """
    # Trigger deployment if:
    # * The binny repo
    # * On main branch
    # * All checks have passed
    repo = payload['repository']
    suite = payload['check_suite']
    # Sets up authentication so act as the installation
    async with ghapp.for_installation(payload['installation']['id'], repo_id=repo['id']):
        if repo['full_name'] != 'ppb/binny':
            # Not the repo
            return

        if suite['head_branch'] != repo['default_branch']:
            # Not the branch
            return

        # UGH, doesn't actually send us the node_id of the commit, just the git sha
        commit_sha = suite['head_commit']['id']
        resp = await get_check_suites(repo=repo['node_id'], commit=commit_sha)
        assert not resp.errors, resp.errors
        suites = resp.data['node']['object']['checkSuites']['nodes']
        has_succeeded = all(
            s['status'] == 'COMPLETED' and s['conclusion'] == 'SUCCESS'
            for s in suites
        )
        if not has_succeeded:
            # Not all checks passed
            return

        # OK, now we can deploy
        log = open('/tmp/binny-deploy.log')
        subprocess.Popen(
            [sys.executable, '-m', 'binny.deploy'],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
        )
        # Allow to run in the background


async def entrypoint(scope, receive, send):
    if scope["type"] == "http" and scope["scheme"] == "http":
        # Let's assume we're behind a proxy, adjust based on additional headers
        for k, v in scope['headers']:
            if k.lower() == b'x-forwarded-proto':
                scope['scheme'] = v.decode('ascii')
            elif k.lower() == b'x-forwarded-for':
                scope['client'] = (v.decode('ascii'), 0)

    return await app(scope, receive, send)

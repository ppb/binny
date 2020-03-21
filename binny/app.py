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


@webhook.hook('check_run')
async def check_run(payload):
    """
    https://developer.github.com/v3/activity/events/types/#checkrunevent
    """


async def entrypoint(scope, receive, send):
    if scope["type"] == "http" and scope["scheme"] == "http":
        # Let's assume we're behind a proxy, adjust based on additional headers
        for k, v in scope['headers']:
            if k.lower() == b'x-forwarded-proto':
                scope['scheme'] = v.decode('ascii')
            elif k.lower() == b'x-forwarded-for':
                scope['client'] = (v.decode('ascii'), 0)

    return await app(scope, receive, send)

from quart import current_app
from gqlmod_github.app_async import GithubApp
from quart.local import LocalProxy


@LocalProxy
def ghapp():
    return GithubApp(current_app.config['APP_ID'], current_app.config['APP_PRIVATE_KEY'].encode('ascii'))

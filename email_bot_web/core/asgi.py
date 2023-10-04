import os

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

asgi_app = ASGIStaticFilesHandler(get_asgi_application())


async def on_startup():
    from infrastucture.imap_listener import start_listening_all_emails
    await start_listening_all_emails()


class LifespanApp:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    await on_startup()
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        else:
            await self.app(scope, receive, send)


application = LifespanApp(asgi_app)

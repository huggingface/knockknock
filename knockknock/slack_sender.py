from typing import List
import datetime
import traceback
import functools
import json
import socket
import requests

DATE_FORMAT = "%Y-%m-%d %H:%M:%d"

def slack_sender(webhook_url: str, channel: str, user_mentions: List[str] = []):
    """
    Email sender wrapper: execute func, send an email with the end status
    (sucessfully finished or crashed) at the end. Also send an email before
    executing func.

    `webhook_url`: str
        The webhook URL to access your slack room.
        Visit https://api.slack.com/incoming-webhooks#create_a_webhook for more details.
    `channel`: str
        The slack room to log.
    `user_mentions`: List[str] (default=[])
        Optional users ids to notify.
        Visit https://api.slack.com/methods/users.identity for more details.
    """

    dump = {
        "username": "Knock Knock",
        "channel": channel,
        "icon_emoji": ":clapper:",
    }
    def decorator_sender(func):
        @functools.wraps(func)
        def wrapper_sender(*args, **kwargs):

            start_time = datetime.datetime.now()
            contents = ['Your training has started 🎬',
                        'Machine name: %s' % socket.gethostname(),
                        'Main call: %s' % func.__name__,
                        'Starting date: {start_time.strftime(DATE_FORMAT)}']
            contents.append(' '.join(user_mentions))
            dump['text'] = '\n'.join(contents)
            dump['icon_emoji'] = ':clapper:'
            requests.post(webhook_url, json.dumps(dump))

            try:
                value = func(*args, **kwargs)
                end_time = datetime.datetime.now()
                elapsed_time = end_time - start_time
                contents = ["Your training is complete 🎉",
                            'Machine name: %s' % socket.gethostname(),
                            'Main call: %s' % func.__name__,
                            'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                            'End date: %s' % end_time.strftime(DATE_FORMAT),
                            'Training duration: %s' % str(elapsed_time)]
                contents.append(' '.join(user_mentions))
                dump['text'] = '\n'.join(contents)
                dump['icon_emoji'] = ':tada:'
                requests.post(webhook_url, json.dumps(dump))
                return value

            except Exception as ex:
                end_time = datetime.datetime.now()
                elapsed_time = end_time - start_time
                contents = ["Your training has crashed ☠️",
                            'Machine name: %s' % socket.gethostname(),
                            'Main call: %s' % func.__name__,
                            'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                            'Crash date: %s' % end_time.strftime(DATE_FORMAT),
                            'Crashed training duration: %s\n\n' % str(elapsed_time),
                            "Here's the error:",
                            '%s\n\n' % ex,
                            "Traceback",
                            '%s' % traceback.format_exc()]
                contents.append(' '.join(user_mentions))
                dump['text'] = '\n'.join(contents)
                dump['icon_emoji'] = ':skull_and_crossbones:'
                requests.post(webhook_url, json.dumps(dump))

        return wrapper_sender

    return decorator_sender

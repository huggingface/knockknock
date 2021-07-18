import datetime
import functools
import json
import os
import socket
import traceback
from typing import List

import requests

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def cliq_sender(webhook_url: str, user_mentions: List[str] = []):
    """
    cliq sender wrapper: execute func, send a Cliq message with the end status
    (successfully finished or crashed) at the end. Also send a Cliq message before
    executing func.

    `webhook_url`: str
        The webhook URL to access your channel/bot.
        Visit https://www.zoho.com/cliq/help/platform/webhook-tokens.html for more details.
    `user_mentions`: List[str] (default=[])
        Optional users ids to notify.
    """

    # Visit https://www.zoho.com/cliq/help/restapi/v2/#cliq_rest_api for more api related details
    user_mentions = ['{@' + str(user_mention) + '}' for user_mention in user_mentions]

    dump = {
        "bot": {
            "name": "Knock Knock",
            "image": "https://huggingface.co/front/assets/huggingface_logo.svg",
        }
    }

    def decorator_sender(func):
        @functools.wraps(func)
        def wrapper_sender(*args, **kwargs):
            start_time = datetime.datetime.now()
            host_name = socket.gethostname()
            func_name = func.__name__

            # Handling distributed training edge case.
            # In PyTorch, the launch of `torch.distributed.launch` sets up a RANK environment variable for each process.
            # This can be used to detect the master process.
            # See https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py#L211
            # Except for errors, only the master process will send notifications.
            if 'RANK' in os.environ:
                master_process = (int(os.environ['RANK']) == 0)
                host_name += ' - RANK: %s' % os.environ['RANK']
            else:
                master_process = True

            if master_process:
                contents = ['Your training has started 🎬',
                            'Machine name: %s' % host_name,
                            'Main call: %s' % func_name,
                            'Starting date: %s' % start_time.strftime(DATE_FORMAT)]
                contents.append(' '.join(user_mentions))
                dump['text'] = '\n'.join(contents)
                requests.post(webhook_url, json.dumps(dump))

            try:
                value = func(*args, **kwargs)

                if master_process:
                    end_time = datetime.datetime.now()
                    elapsed_time = end_time - start_time
                    contents = ["Your training is complete 🎉",
                                'Machine name: %s' % host_name,
                                'Main call: %s' % func_name,
                                'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                                'End date: %s' % end_time.strftime(DATE_FORMAT),
                                'Training duration: %s' % str(elapsed_time)]

                    try:
                        str_value = str(value)
                        contents.append('Main call returned value: %s' % str_value)
                    except:
                        contents.append('Main call returned value: %s' % "ERROR - Couldn't str the returned value.")

                    contents.append(' '.join(user_mentions))
                    dump['text'] = '\n'.join(contents)
                    requests.post(webhook_url, json.dumps(dump))

                return value

            except Exception as ex:
                end_time = datetime.datetime.now()
                elapsed_time = end_time - start_time
                contents = ["Your training has crashed ☠️",
                            'Machine name: %s' % host_name,
                            'Main call: %s' % func_name,
                            'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                            'Crash date: %s' % end_time.strftime(DATE_FORMAT),
                            'Crashed training duration: %s\n\n' % str(elapsed_time),
                            "Here's the error:",
                            '%s\n\n' % ex,
                            "Traceback:",
                            '%s' % traceback.format_exc()]
                contents.append(' '.join(user_mentions))
                dump['text'] = '\n'.join(contents)
                requests.post(webhook_url, json.dumps(dump))
                raise ex

        return wrapper_sender

    return decorator_sender

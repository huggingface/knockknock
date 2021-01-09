import os
import datetime
import traceback
import functools
import socket
import requests


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
NOTIFY_API_URL = "https://notify-api.line.me/api/notify"


def line_sender(token: str):
    """
    LINE sender wrapper: execute func, send a LINE notification with the end status
    (sucessfully finished or crashed) at the end. Also send a Line notification before
    executing func.

    `token`: str
        The personal access token required to use the LINE Notify API
        Visit https://engineering.linecorp.com/en/blog/using-line-notify-to-send-messages-to-line-from-the-command-line/
         for more details.
    """
    headers = {"Authorization": f"Bearer {token}",
               "Content-Type": "application/x-www-form-urlencoded"}
    dump = {}

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
                contents = [
                    'Your training has started 🎬',
                    'Machine name: %s' % host_name,
                    'Main call: %s' % func_name,
                    'Starting date: %s' % start_time.strftime(DATE_FORMAT)
                ]
                dump['message'] = '\n'.join(contents)
                requests.post(url=NOTIFY_API_URL, headers=headers, params=dump)

            try:
                value = func(*args, **kwargs)

                if master_process:
                    end_time = datetime.datetime.now()
                    elapsed_time = end_time - start_time
                    contents = [
                        "Your training is complete 🎉",
                        'Machine name: %s' % host_name,
                        'Main call: %s' % func_name,
                        'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                        'End date: %s' % end_time.strftime(DATE_FORMAT),
                        'Training duration: %s' % str(elapsed_time)
                    ]

                    try:
                        str_value = str(value)
                        contents.append('Main call returned value: %s' % str_value)
                    except:
                        contents.append('Main call returned value: %s' %
                                        "ERROR - Couldn't str the returned value.")

                    dump['message'] = '\n'.join(contents)
                    requests.post(url=NOTIFY_API_URL, headers=headers, params=dump)

                return value

            except Exception as ex:
                end_time = datetime.datetime.now()
                elapsed_time = end_time - start_time
                contents = [
                    "Your training has crashed ☠️",
                    'Machine name: %s' % host_name,
                    'Main call: %s' % func_name,
                    'Starting date: %s' % start_time.strftime(DATE_FORMAT),
                    'Crash date: %s' % end_time.strftime(DATE_FORMAT),
                    'Crashed training duration: %s\n\n' % str(elapsed_time),
                    "Here's the error:", '%s\n\n' % ex,
                    "Traceback:", '%s' % traceback.format_exc(),
                ]
                dump['message'] = '\n'.join(contents)
                requests.post(url=NOTIFY_API_URL, headers=headers, params=dump)
                raise ex

        return wrapper_sender

    return decorator_sender

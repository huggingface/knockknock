from typing import List
import os
import datetime
import traceback
import functools
import json
import socket
import requests
import time

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def feishu_sender(webhook_url: str):
    """
    Feishu sender wrapper: execute func, send a Feishu message with the end status
    (sucessfully finished or crashed) at the end. Also send a Feishu message before
    executing func. To obtain the webhook, add a Group Robot in your Feishu Group. Visit
    https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN for more details.

    `webhook_url`: str
        The webhook URL to access your Feishu chatroom.
        Visit https://open.feishu.cn/document/ukTMukTMukTM/ucTM5YjL3ETO24yNxkjN for more details.
    """
    
    msg_template = {
        "msg_type": "text",
        "content" : {"text":""},
        "timestamp" : "",
    }

    def decorator_sender(func):
        @functools.wraps(func)
        def wrapper_sender(*args, **kwargs):

            timestamp = int(datetime.datetime.now().timestamp())
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
                
                msg_template['content']['text'] = '\n'.join(contents)
                msg_template['timestamp'] = timestamp
                resp = requests.post(webhook_url, json=msg_template)
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") and result.get("code") != 0:
                    print(f"error：{result['msg']}")
                    return
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
                        contents.append('Main call returned value: %s'% str_value)
                    except:
                        contents.append('Main call returned value: %s'% "ERROR - Couldn't str the returned value.")
                   
                    msg_template['content']['text'] = '\n'.join(contents)
                    msg_template['timestamp'] = timestamp
                    resp = requests.post(webhook_url, json=msg_template)
                    resp.raise_for_status()
                    result = resp.json()
                    if result.get("code") and result.get("code") != 0:
                        print(f"error：{result['msg']}")
                        return

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
                
                msg_template['content']['text'] = '\n'.join(contents)
                msg_template['timestamp'] = timestamp
                resp = requests.post(webhook_url, json=msg_template)
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") and result.get("code") != 0:
                    print(f"error：{result['msg']}")
                    return

                raise ex

        return wrapper_sender

    return decorator_sender
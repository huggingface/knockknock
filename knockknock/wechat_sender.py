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

def wechat_sender(webhook_url: str,
                  user_mentions: List[str] = [],
                  user_mentions_mobile: List[str] = []):
    """
    WeChat Work sender wrapper: execute func, send a WeChat Work notification with the end status
    (sucessfully finished or crashed) at the end. Also send a WeChat Work notification before
    executing func. To obtain the webhook, add a Group Robot in your WeChat Work Group. Visit
    https://work.weixin.qq.com/api/doc/90000/90136/91770 for more details.

    `webhook_url`: str
        The webhook URL to access your WeChat Work chatroom.
        Visit https://work.weixin.qq.com/api/doc/90000/90136/91770 for more details.
    `user_mentions`: List[str] (default=[])
        Optional userids to notify (use '@all' for all group members).
        Visit https://work.weixin.qq.com/api/doc/90000/90136/91770 for more details.
    `user_mentions_mobile`: List[str] (default=[])
        Optional user's phone numbers to notify (use '@all' for all group members).
        Visit https://work.weixin.qq.com/api/doc/90000/90136/91770 for more details.
    """
    
    msg_template = {
        "msgtype": "text", 
        "text": {
            "content": "",
            "mentioned_list":user_mentions,
            "mentioned_mobile_list":user_mentions_mobile
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
                
                msg_template['text']['content'] = '\n'.join(contents)
                requests.post(webhook_url, json=msg_template)

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

                    
                    msg_template['text']['content'] = '\n'.join(contents)
                    requests.post(webhook_url, json=msg_template)
                    print(msg_template)

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
                
                msg_template['text']['content'] = '\n'.join(contents)
                requests.post(webhook_url, json=msg_template)
                print(msg_template)

                raise ex

        return wrapper_sender

    return decorator_sender

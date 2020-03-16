from urllib.parse import urljoin
from typing import List
import os
import datetime
import traceback
import functools
import json
import socket
import requests

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def rocketchat_sender(rocketchat_server_url: str,
                      rocketchat_user_id: str,
                      rocketchat_auth_token: str,
                      channel: str,
                      user_mentions: List[str] = [],
                      alias: str = ""):
    """
    RocketChat sender wrapper: execute func, post a RocketChat message with the end status
    (sucessfully finished or crashed) at the end. Also send a RocketChat message before
    executing func.

    `rocketchat_server_url`: str
        The RocketChat server URL.
        E.g. rocketchat.yourcompany.com
    `rocketchat_user_id`: str
        The RocketChat user id to post messages with (you'll be able to view your user id when you create a personal access token). 
    `rocketchat_auth_token`: str
        The RocketChat personal access token.
        Visit https://rocket.chat/docs/developer-guides/rest-api/personal-access-tokens/ for more details.
    `channel`: str
        The RocketChat channel to log.
    `user_mentions`: List[str] (default=[])
        Optional list of user names to notify, as comma seperated list.
    `alias`: str (default="")
        Optional alias to use for the notification.
    """

    dump = {
        "alias": alias,
        "channel": channel,
        "emoji": ":bell:"
    }

    headers = {
        "Content-type": "application/json",
        "X-Auth-Token": rocketchat_auth_token,
        "X-User-Id": rocketchat_user_id
    }

    def decorator_sender(func):
        @functools.wraps(func)
        def wrapper_sender(*args, **kwargs):

            webhook_url = urljoin(rocketchat_server_url,
                                  "/api/v1/chat.postMessage")

            start_time = datetime.datetime.now().replace(microsecond=0)
            host_name = socket.gethostname()
            func_name = func.__name__

            # Handling distributed training edge case.
            # In PyTorch, the launch of `torch.distributed.launch` sets up a RANK environment variable for each process.
            # This can be used to detect the master process.
            # See https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py#L211
            # Except for errors, only the master process will send notifications.
            if "RANK" in os.environ:
                master_process = (int(os.environ["RANK"]) == 0)
                host_name += " - RANK: %s" % os.environ["RANK"]
            else:
                master_process = True

            if master_process:
                contents = ["Your training has **started** :clap: %s" % " ".join(["@" + u for u in user_mentions]),
                            "**Machine name:** %s" % host_name,
                            "**Main call:** %s" % func_name,
                            "**Starting date:** %s" % start_time.strftime(
                                DATE_FORMAT)]
                dump["text"] = "\n".join(contents)
                requests.post(
                    url=webhook_url,
                    data=json.dumps(dump),
                    headers=headers)

            try:
                value = func(*args, **kwargs)

                if master_process:
                    end_time = datetime.datetime.now().replace(microsecond=0)
                    elapsed_time = (end_time - start_time)
                    contents = ["Your training is **complete** :tada: %s" % " ".join(["@" + u for u in user_mentions]),
                                "**Machine name:** %s" % host_name,
                                "**Main call:** %s" % func_name,
                                "**Starting date:** %s" % start_time.strftime(
                                    DATE_FORMAT),
                                "**End date:** %s" % end_time.strftime(
                                    DATE_FORMAT),
                                "**Training duration:** %s" % str(elapsed_time)]

                    try:
                        str_value = str(value)
                        contents.append(
                            "**Main call returned value:** %s" % str_value)
                    except:
                        contents.append("**Main call returned value:** %s" %
                                        "ERROR - Couldn't str the returned value.")

                    dump["text"] = "\n".join(contents)
                    requests.post(
                        url=webhook_url,
                        data=json.dumps(dump),
                        headers=headers)

                return value

            except Exception as ex:
                end_time = datetime.datetime.now().replace(microsecond=0)
                elapsed_time = end_time - start_time
                contents = ["Your training has **crashed** :skull_crossbones: %s" % " ".join(["@" + u for u in user_mentions]),
                            "**Machine name:** %s" % host_name,
                            "**Main call:** %s" % func_name,
                            "**Starting date:** %s" % start_time.strftime(
                                DATE_FORMAT),
                            "**Crash date:** %s" % end_time.strftime(
                                DATE_FORMAT),
                            "**Crashed training duration:** %s" % str(
                                elapsed_time),
                            "**Error message:**",
                            "\n%s\n" % ex,
                            "**Traceback:**",
                            "\n%s\n" % traceback.format_exc()]
                dump["text"] = "\n".join(contents)
                requests.post(
                    url=webhook_url,
                    data=json.dumps(dump),
                    headers=headers)
                raise ex

        return wrapper_sender

    return decorator_sender

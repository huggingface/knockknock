from typing import List
import os
import datetime
import traceback
import functools
import json
import socket
import requests

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def slack_sender(webhook_url: str, channel: str, user_mentions: List[str] = []):
    """
    Slack sender wrapper: execute func, send a Slack notification with the end status
    (sucessfully finished or crashed) at the end. Also send a Slack notification before
    executing func.

    `webhook_url`: str
        The webhook URL to access your slack room.
        Visit https://api.slack.com/incoming-webhooks#create_a_webhook for more details.
    `channel`: str
        The slack room to log.
    `user_mentions`: List[str] (default=[])
        Optional usernames to notify.
        Visit https://api.slack.com/methods/users.identity for more details.
    """

    dump = {
        "username": "Knock Knock",
        "channel": channel,
        "icon_emoji": ":clapper:",
    }

    if user_mentions:
        user_mentions = ["@{}".format(user) for user in user_mentions if not user.startswith("@")]

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
                notification = "Your training has started! 🎬"
                if user_mentions:
                    notification = _add_mentions(notification)

                dump["blocks"] = _starting_message(
                    func_name, host_name, notification, start_time
                )
                dump["text"] = notification
                dump["icon_emoji"] = ":clapper:"

                requests.post(webhook_url, json.dumps(dump))

            try:
                value = func(*args, **kwargs)

                if master_process:
                    notification = "Your training is complete 🎉"
                    if user_mentions:
                        notification = _add_mentions(notification)

                    dump["blocks"] = _successful_message(
                        func_name, host_name, notification, start_time, value
                    )
                    dump["text"] = notification
                    dump["icon_emoji"] = ":tada:"
                    requests.post(webhook_url, json.dumps(dump))

                return value

            except Exception as ex:
                notification = "Your training has crashed ☠️"
                if user_mentions:
                    notification = _add_mentions(notification)

                dump["blocks"] = _error_message(
                    ex, func_name, host_name, notification, start_time
                )

                dump["text"] = notification
                dump["icon_emoji"] = ":skull_and_crossbones:"
                requests.post(webhook_url, json.dumps(dump))
                raise ex

        def _error_message(ex, func_name, host_name, notification, start_time):
            """Uses Slack blocks to create a formatted report of exception 'ex'."""
            end_time = datetime.datetime.now()
            training_time = _format_train_time(end_time, start_time)
            return [
                {"type": "section", "text": {"type": "mrkdwn", "text": notification}},
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Machine name:* {}\n"
                            "*Main call:* `{}`\n"
                            "*Starting date:* {}\n"
                            "*Crash date:* {}\n"
                            "*Time elapsed before crash:* {}".format(
                                host_name,
                                func_name,
                                start_time.strftime(DATE_FORMAT),
                                end_time.strftime(DATE_FORMAT),
                                training_time,
                            ),
                        }
                    ],
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Error:* `{}`".format(ex)},
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Traceback:*\n```{}```".format(traceback.format_exc()),
                    },
                },
            ]

        def _starting_message(func_name, host_name, notification, start_time):
            """Uses Slack blocks to create an initial report of training."""
            return [
                {"type": "section", "text": {"type": "mrkdwn", "text": notification}},
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Machine name:* {}\n"
                            "*Main call:* {}\n"
                            "*Starting date:* {}\n".format(
                                host_name, func_name, start_time.strftime(DATE_FORMAT)
                            ),
                        }
                    ],
                },
            ]

        def _successful_message(func_name, host_name, notification, start_time, value):
            """Uses Slack blocks to report a successful training run with statistics."""
            end_time = datetime.datetime.now()
            training_time = _format_train_time(end_time, start_time)
            blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": notification}},
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Machine name:* {}\n"
                            "*Main call:* `{}`\n"
                            "*Starting date:* {}\n"
                            "*End date:* {}\n"
                            "*Training Duration:* {}".format(
                                host_name,
                                func_name,
                                start_time.strftime(DATE_FORMAT),
                                end_time.strftime(DATE_FORMAT),
                                training_time,
                            ),
                        }
                    ],
                },
            ]

            if value is not None:
                blocks.append({"type": "divider"})
                try:
                    str_value = str(value)
                    dump["blocks"].append(
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "*Main call returned value:* `{}`".format(
                                    str_value
                                ),
                            },
                        }
                    )
                except Exception as e:
                    blocks.append(
                        "Couldn't str the returned value due to the following error: \n`{}`".format(
                            e
                        )
                    )

            return blocks

        def _format_train_time(end_time, start_time):
            """Returns a time delta as a string in the format '%d %H:%M:%S'"""
            elapsed_time = end_time - start_time
            days, remainder = divmod(elapsed_time.seconds, 86400)
            hours, remainder = divmod(remainder, 24)
            minutes, seconds = divmod(remainder, 60)
            training_time = "{:2d}:{:02d}:{:02d}".format(hours, minutes, seconds)

            if days:
                training_time = "{}d ".format(days) + training_time
            return training_time

        def _add_mentions(notification):
            notification = notification + " " + " ".join(user_mentions)
            return notification

        return wrapper_sender

    return decorator_sender


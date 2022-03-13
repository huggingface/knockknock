import os
import configparser
import warnings

from knockknock.chime_sender import chime_sender
from knockknock.discord_sender import discord_sender
from knockknock.email_sender import email_sender
from knockknock.slack_sender import slack_sender
from knockknock.sms_sender import sms_sender
from knockknock.telegram_sender import telegram_sender
from knockknock.teams_sender import teams_sender
from knockknock.desktop_sender import desktop_sender
from knockknock.matrix_sender import matrix_sender
from knockknock.dingtalk_sender import dingtalk_sender
from knockknock.wechat_sender import wechat_sender
from knockknock.rocketchat_sender import rocketchat_sender


SENDER_DICT = {
    'chime': chime_sender,
    'discord': discord_sender,
    'email': email_sender,
    'slack': slack_sender,
    'sms': sms_sender,
    'telegram': telegram_sender,
    'teams': teams_sender,
    'desktop': desktop_sender,
    'matrix': matrix_sender,
    'dingtalk': dingtalk_sender,
    'wechat': wechat_sender,
    'rocketchat': rocketchat_sender
}


def knockknock(config_path: str = "./", config_name: str = "knockknock.ini"):
    """
    A general decorator reading the config file and wrapping the function to according sender.

    `config_path`: str
        A config folder contains your knockknock config file.

    `config_name`: str
        A config file with sender keys in `SENDER_DICT` as its section name and set the sender
        parameters as passed values.
    """
    do_notification = False
    config_file = os.path.join(config_path, config_name)
    if os.path.isfile(config_file):
        # read the config file
        sender_config = configparser.ConfigParser()
        sender_config.read(config_file)

        # here we only select the `knockknock` section inside the config file as valid sender setting
        sender_class = None
        sender_param = {}
        if 'knockknock' in sender_config:
            sender_section = dict(sender_config['knockknock'])

            # get sender class
            sender_class_name = sender_section.pop('sender', None)
            if sender_class_name not in SENDER_DICT:
                raise ValueError(
                    f'The sender type `{sender_class_name}` defined in the config file'
                    + f' {config_file} is invalid.'
                    + f' Support sender types: {", ".join(SENDER_DICT.keys())}.'
                )

            # set notification parameters
            do_notification = eval(sender_section.pop('notification', 'True'))
            sender_class = SENDER_DICT[sender_class_name]

            # special keys pop out in above
            sender_param = sender_section
        else:
            warnings.warn(
                f'The config file {config_file} is empty. Knockknock would not send message.'
            )
    else:
        warnings.warn(
            f'The config file {config_file} is not existed. Knockknock would not send message.'
        )

    def wrap_knock(func):
        if do_notification:
            sender_decorator = sender_class(**sender_param)
            return sender_decorator(func)
        else:
            return func
    return wrap_knock

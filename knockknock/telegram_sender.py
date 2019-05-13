import os
import datetime
import traceback
import functools
import socket
import telegram

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def telegram_sender(token: str, chat_id: int):
    """
    Telegram sender wrapper: execute func, send a Telegram message with the end status
    (sucessfully finished or crashed) at the end. Also send a Telegram message before
    executing func.

    `token`: str
        The API access TOKEN required to use the Telegram API.
        Visit https://core.telegram.org/bots#6-botfather to obtain your TOKEN.
    `chat_id`: int
        Your chat room id with your notification BOT.
        Visit https://api.telegram.org/bot<YourBOTToken>/getUpdates to get your chat_id
        (start a conversation with your bot by sending a message and get the `int` under
        message['chat']['id'])
    """

    bot = telegram.Bot(token=token)
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
                text = '\n'.join(contents)
                bot.send_message(chat_id=chat_id, text=text)

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

                    text = '\n'.join(contents)
                    bot.send_message(chat_id=chat_id, text=text)

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
                text = '\n'.join(contents)
                bot.send_message(chat_id=chat_id, text=text)
                raise ex

        return wrapper_sender

    return decorator_sender

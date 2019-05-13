# Knock Knock

A small library to get a notification when your training is complete or when it crashes during the process with two additional lines of code.

When training deep learning models, it is common to use early stopping. Apart from a rough estimate, it is difficult to predict when the training will finish. Thus, it can be interesting to set up automatic notifications for your training. It is also interesting to be notified when your training crashes in the middle of the process for unexpected reasons.

## Installation

Install with `pip` or equivalent.
```bash
pip install knockknock
```

(For conda users, you can use `conda install -c victorsanh knockknock`.)

This code has only been tested with Python 3.6.

## Usage

The library is designed to be used in a seamless way, with minimal code modification: you only need to add a decorator on top your main function call. The return value (if there is one) is also reported in the notification.

There are currently three ways to setup notifications: email, Slack and Telegram.

### Email

The service relies on [Yagmail](https://github.com/kootenpv/yagmail) a GMAIL/SMTP client. You'll need a gmail email address to use it (you can setup one [here](https://accounts.google.com), it's free). I recommend creating a new one (rather than your usual one) since you'll have to modify the account's security settings to allow the Python library to access it by [Turning on less secure apps](https://devanswers.co/allow-less-secure-apps-access-gmail-account/).


#### Python

```python
from knockknock import email_sender

@email_sender(recipient_email="<your_email@address.com>", sender_email="<grandma's_email@gmail.com>")
def train_your_nicest_model(your_nicest_parameters):
    import time
    time.sleep(10000)
    return {'loss': 0.9} # Optional return value
```

#### Command-line

```bash
knockknock email \
    --recipient-email <your_email@address.com> \
    --sender-email <grandma's_email@gmail.com> \
    sleep 10
```

If `sender_email` is not specified, then `recipient_email` will be also used for sending.

Note that launching this will asks you for the sender's email password. It will be safely stored in the system keyring service through the [`keyring` Python library](https://pypi.org/project/keyring/).

### Slack

Similarly, you can also use Slack to get notifications. You'll have to get your Slack room [weebhook URL](https://api.slack.com/incoming-webhooks#create_a_webhook) and optionally your [user id](https://api.slack.com/methods/users.identity) (if you want to tag yourself or someone else).

#### Python

```python
from knockknock import slack_sender

webhook_url = "<webhook_url_to_your_slack_room>"
@slack_sender(webhook_url=webhook_url, channel="<your_favorite_slack_channel>")
def train_your_nicest_model(your_nicest_parameters):
    import time
    time.sleep(10000)
    return {'loss': 0.9} # Optional return value
```

You can also specify an optional argument to tag specific people: `user_mentions=[<your_slack_id>, <grandma's_slack_id>]`.

#### Command-line

```bash
knockknock slack \
    --webhook-url <webhook_url_to_your_slack_room> \
    --channel <your_favorite_slack_channel> \
    sleep 10
```

You can also specify an optional argument to tag specific people: `--user-mentions <your_slack_id>,<grandma's_slack_id>`.

### Telegram

You can also use Telegram Messenger to get notifications. You'll first have to create your own notification bot by following the three steps provided by Telegram [here](https://core.telegram.org/bots#6-botfather) and save your API access `TOKEN`.

Telegram bots are shy and can't send the first message so you'll have to do the first step. By sending the first message, you'll be able to get the `chat_id` required (identification of your messaging room) by visiting `https://api.telegram.org/bot<YourBOTToken>/getUpdates` and get the `int` under the key `message['chat']['id']`.

#### Python

```python
from knockknock import telegram_sender

CHAT_ID: int = <your_messaging_room_id>
@telegram_sender(token="<your_api_token>", chat_id=CHAT_ID)
def train_your_nicest_model(your_nicest_parameters):
    import time
    time.sleep(10000)
    return {'loss': 0.9} # Optional return value
```

#### Command-line

```bash
knockknock telegram \
    --token <your_api_token> \
    --chat-id <your_messaging_room_id> \
    sleep 10
```

## Note on distributed training

When using distributed training, a GPU is bound to its process using the local rank variable. Since knockknock works at the process level, if you are using 8 GPUs, you would get 8 notifications at the beginning and 8 notifications at the end... To circumvent that, except for errors, only the master process is allowed to send notifications so that you receive only one notification at the beginning and one notification at the end.

**Note:** _In PyTorch, the launch of `torch.distributed.launch` sets up a RANK environment variable for each process (see [here](https://github.com/pytorch/pytorch/blob/master/torch/distributed/launch.py#L211)). This is used to detect the master process, and for now, the only simple way I came up with. Unfortunately, this is not intended to be general for all platforms but I would happily discuss smarter/better ways to handle distributed training in an issue/PR._

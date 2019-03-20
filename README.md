# Knock Knock

A small library to get a notification you when your training is complete or when it crashes during the process with two additional lines of code.

When training deep learning models, it is common to use early stopping. Apart from a rough estimate, it is difficult to predict when the training will finish. Then, it can be interesting to set up automatic notifications for your training. It is also interesting to be notified when your training crashes in the middle of the process for unexpected reasons.

## Installation

Install with `pip` or equivalent.
```bash
pip install .
```

This code has only been tested with Python 3.6.

## Usage

The library is designed to be used in a seamless way, with minimal code modification: you only need to add a decorator on top your main function call.

There are currently two ways to setup notifications: email and Slack.

### Email

The service relies on [Yagmail](https://github.com/kootenpv/yagmail) a GMAIL/SMTP client. You'll need a gmail email address to use it (you can setup one [here](https://accounts.google.com), it's free). I recommend creating a new one (rather than your usual one) since you'll have to modify the account's security settings to allow the Python library to access it by [Turning on less secure apps](https://devanswers.co/allow-less-secure-apps-access-gmail-account/).

```python
from knockknock import email_sender

@email_sender(recipient_email: "<your_email@address.com>", sender_email: "<grandma's_email@gmail.com>")
def train_your_nicest_model(your_nicest_parameters):
    import time
    time.sleep(10000)
```

If `sender_email` is not specified, then `recipient_email` will be also used for sending.

Note that launching this will asks you for the sender's email password. It will be safely stored in the system keyring service through the [`keyring` Python library](https://pypi.org/project/keyring/).

### Slack

Similarly, you can also use Slack to get notifications. You'll have to get your Slack room [weebhook URL](https://api.slack.com/incoming-webhooks#create_a_webhook) and optionally your [user id](https://api.slack.com/methods/users.identity) (if you want to tag yourself or someone else).

```python
from knockknock import slack_sender

webhook_url = "<webhook_url_to_your_slack_room>"
@slack_sender(webhook_url=webhook_url, channel="<your_favorite_slack_channel>")
def train_your_nicest_model(your_nicest_parameters):
    import time
    time.sleep(10000)
```

You can also specify an optional argument to tag specific people: `user_mentions=[<your_slack_id>, <grandma's_slack_id>]`.

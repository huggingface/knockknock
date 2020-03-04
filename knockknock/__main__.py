import argparse
import subprocess

from knockknock import (chime_sender,
                        desktop_sender,
                        dingtalk_sender,
                        discord_sender,
                        email_sender,
                        matrix_sender,
                        slack_sender,
                        sms_sender,
                        teams_sender,
                        telegram_sender,)

def main():
    parser = argparse.ArgumentParser(
        description="KnockKnock - Be notified when your training is complete.")
    parser.add_argument("--verbose", required=False, action="store_true",
                        help="Show full command in notification.")
    subparsers = parser.add_subparsers()

    ## Chime
    chime_parser = subparsers.add_parser(
        name="chime", description="Send a Chime message before and after function " +
        "execution, with start and end status (successfully or crashed).")
    chime_parser.add_argument(
        "--webhook-url", type=str, required=True,
        help="The webhook URL to access your chime room.")
    chime_parser.add_argument(
        "--user-mentions", type=lambda s: s.split(","), required=False, default=[],
        help="Optional user alias or full email address to notify, as comma separated list.")
    chime_parser.set_defaults(sender_func=chime_sender)

    ## Desktop
    desktop_parser = subparsers.add_parser(
        name="desktop", description="Send a desktop notification before and after function " +
        "execution, with start and end status (successfully or crashed).")
    desktop_parser.add_argument("--title", type=str, required=False,
        help="The title of the notification, default to knockknock")
    desktop_parser.set_defaults(sender_func=desktop_sender)

    ## Discord
    discord_parser = subparsers.add_parser(
        name="discord", description="Send a Discord message before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    discord_parser.add_argument(
        "--webhook-url", type=str, required=True,
        help="The webhook URL to access your Discord server/channel.")
    discord_parser.set_defaults(sender_func=discord_sender)

    ## Email
    email_parser = subparsers.add_parser(
        name="email", description="Send an email before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    email_parser.add_argument(
        "--recipient-emails", type=lambda s: s.split(","), required=True,
        help="The email addresses to notify, as comma separated list.")
    email_parser.add_argument(
        "--sender-email", type=str, required=False,
        help="The email adress to send the messages." +
        "(default: use the same address as the first email in `recipient-emails`)")
    email_parser.set_defaults(sender_func=email_sender)

    ## Slack
    slack_parser = subparsers.add_parser(
        name="slack", description="Send a Slack message before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    slack_parser.add_argument(
        "--webhook-url", type=str, required=True,
        help="The webhook URL to access your slack room.")
    slack_parser.add_argument(
        "--channel", type=str, required=True, help="The slack room to log.")
    slack_parser.add_argument(
        "--user-mentions", type=lambda s: s.split(","), required=False, default=[],
        help="Optional user ids to notify, as comma seperated list.")
    slack_parser.set_defaults(sender_func=slack_sender)

    ## DingTalk
    dingtalk_parser = subparsers.add_parser(
        name="dingtalk", description="Send a dingtalk message before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    dingtalk_parser.add_argument(
        "--webhook-url", type=str, required=True,
        help="The webhook URL to access your dingtalk chatroom")
    dingtalk_parser.add_argument(
        "--user-mentions", type=lambda s: s.split(","), required=False, default=[],
        help="Optional user's phone number to notify, as comma seperated list.")
    dingtalk_parser.add_argument(
        "--secret", type=str, required=False, default='',
        help="Optional the dingtalk chatroom robot's secret")
    dingtalk_parser.add_argument(
        "--keywords", type=lambda s: s.split(","), required=False, default=[],
        help="Optional accepted keywords set in dingtalk chatroom robot")
    dingtalk_parser.set_defaults(sender_func=dingtalk_sender)

    ## Telegram
    telegram_parser = subparsers.add_parser(
        name="telegram", description="Send a Telegram message before and after " +
        "function execution, with start and end status (sucessfully or crashed).")
    telegram_parser.add_argument(
        "--token", type=str, required=True,
        help="The API access TOKEN required to use the Telegram API.")
    telegram_parser.add_argument(
        "--chat-id", type=int, required=True,
        help="Your chat room id with your notification BOT.")
    telegram_parser.set_defaults(sender_func=telegram_sender)

    ## Teams
    teams_parser = subparsers.add_parser(
        name="teams", description="Send a teams message before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    teams_parser.add_argument(
        "--webhook-url", type=str, required=True,
        help="The webhook URL to access your teams channel.")
    teams_parser.add_argument(
        "--user-mentions", type=lambda s: s.split(","), required=False, default=[],
        help="Optional user ids to notify, as comma seperated list.")
    teams_parser.set_defaults(sender_func=teams_sender)

    ## SMS
    sms_parser = subparsers.add_parser(
        name="sms", description="Send an SMS using the Twilio API")
    sms_parser.add_argument(
        "--account-sid", type=str, required=True,
        help="The account SID to access your Twilio account.")
    sms_parser.add_argument(
        "--auth-token", type=str, required=True,
        help="The authentication token to access your Twilio account.")
    sms_parser.add_argument(
        "--recipient-number", type=str, required=True,
        help="The phone number of the recipient.")
    sms_parser.add_argument(
        "--sender-number", type=str, required=True,
        help="The phone number of the sender (Twilio number).")
    sms_parser.set_defaults(sender_func=sms_sender)

    ## Matrix
    matrix_parser = subparsers.add_parser(
        name="matrix", description="Send a Matrix message before and after " +
        "function execution, with start and end status (sucessfully or crashed).")
    matrix_parser.add_argument(
        "--homeserver", type=str, required=True,
        help="The homeserver address which was used to register the BOT.")
    matrix_parser.add_argument(
        "--token", type=str, required=True,
        help="The access TOKEN of the user that will send the messages.")
    matrix_parser.add_argument(
        "--room", type=str, required=True,
        help="The alias of the room to which messages will be send by the BOT.")
    matrix_parser.set_defaults(sender_func=matrix_sender)

    args, remaining_args = parser.parse_known_args()
    args = vars(args)

    sender_func = args.pop("sender_func", None)

    if sender_func is None:
        parser.print_help()
        exit(1)

    verbose = args.pop("verbose")

    def run_func(): return subprocess.run(remaining_args, check=True)
    run_func.__name__ = " ".join(
        remaining_args) if verbose else remaining_args[0]

    sender_func(**args)(run_func)()


if __name__ == "__main__":
    main()

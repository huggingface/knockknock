import argparse
import subprocess

from knockknock import email_sender, slack_sender, telegram_sender, teams_sender, sms_sender


def main():
    parser = argparse.ArgumentParser(
        description="KnockKnock - Be notified when your training is complete.")
    parser.add_argument("--verbose", required=False, action="store_true",
                        help="Show full command in notification.")
    subparsers = parser.add_subparsers()

    email_parser = subparsers.add_parser(
        name="email", description="Send an email before and after function " +
        "execution, with start and end status (sucessfully or crashed).")
    email_parser.add_argument(
        "--recipient-email", type=str, required=True,
        help="The email address to notify.")
    email_parser.add_argument(
        "--sender-email", type=str, required=False,
        help="The email adress to send the messages." +
        "(default: use the same address as recipient-email)")
    email_parser.set_defaults(sender_func=email_sender)

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

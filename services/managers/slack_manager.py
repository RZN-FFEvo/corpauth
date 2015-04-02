from django.conf import settings
from pyslack import SlackClient


# TODO: none static class
class SlackManager:
    def __init__(self):
        pass

    @staticmethod
    def enabled():
        return settings.SLACK_ENABLED

    @staticmethod
    def send_general(text):
        if settings.SLACK_ENABLED:
            connection = SlackClient(settings.SLACK_TOKEN)
            try:
                connection.chat_post_message(
                    settings.SLACK_TEST_CHANNEL if settings.SLACK_TEST else settings.SLACK_GENERAL_CHANNEL, text,
                    username=settings.SLACK_BOT, parse='full', unfurl_links='true')
                return True
            except:
                pass
        return False

    @staticmethod
    def send_test(text):
        if settings.SLACK_ENABLED:
            connection = SlackClient(settings.SLACK_TOKEN)
            try:
                connection.chat_post_message(settings.SLACK_TEST_CHANNEL, text,
                                             username=settings.SLACK_BOT,
                                             parse='full',
                                             unfurl_links='true')
                return True
            except:
                pass
        return False

    @staticmethod
    def send_director(text):
        if settings.SLACK_ENABLED:
            connection = SlackClient(settings.SLACK_TOKEN)
            try:
                connection.chat_post_message(
                    settings.SLACK_TEST_CHANNEL if settings.SLACK_TEST else settings.SLACK_DIRECTOR_CHANNEL, text,
                    username=settings.SLACK_BOT,
                    parse='full',
                    unfurl_links='true')
                return True
            except:
                pass
        return False

    @staticmethod
    def send_kill(kill_id):
        if settings.SLACK_ENABLED:
            connection = SlackClient(settings.SLACK_TOKEN)
            try:
                connection.chat_post_message(
                    settings.SLACK_TEST_CHANNEL if settings.SLACK_TEST else settings.SLACK_GENERAL_CHANNEL,
                    "https://zkillboard.com/kill/" + str(kill_id) + "/",
                    username=settings.SLACK_BOT,
                    parse='full',
                    unfurl_links='true')
                return True
            except:
                pass
        return False
from django.urls import path
from user_interaction.accountcollective import AccountBaseConfig
from .views import AchievementAccountView


class AchievementConfig(AccountBaseConfig):
    url_keyword = 'achievements'
    name = 'My achievements'
    url_name = 'achievements'

    def get_urls(self):
        """ Builds a list of urls """
        return [
            path('', AchievementAccountView.as_view(config=self), name='achievements'),
        ]

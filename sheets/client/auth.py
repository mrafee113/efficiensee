import gspread

from django.conf import settings

gc = gspread.oauth(
    credentials_filename=str(settings.CREDENTIALS_FILEPATH),
    authorized_user_filename=str(settings.AUTHORIZATION_FILEPATH)
)

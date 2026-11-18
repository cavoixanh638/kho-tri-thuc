import logging


class SkipOAuthCallbackQuery(logging.Filter):
    def filter(self, record):
        return " /api/v1/integrations/drive/callback?" not in record.getMessage()

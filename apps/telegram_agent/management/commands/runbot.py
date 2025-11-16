from django.core.management.base import BaseCommand
from apps.telegram_agent import bot as bot_module

class Command(BaseCommand):
    help = 'Run the telegram bot (use separate process in production)'
    def handle(self, *args, **options):
        bot_module.run_bot()

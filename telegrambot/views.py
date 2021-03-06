import json

from django.http import JsonResponse
from django.views import View

from telegrambot.handlers.dispatcher import dispatch_telegram_update
from telegrambot.models import TelegramBot


class TelegramBotWebhookView(View):
    @staticmethod
    def post(request, *args, **kwargs):
        token = request.GET.get('token', None)
        if not token:
            return JsonResponse({"ok": False, "error": "Bad request"}, status=400)

        try:
            TelegramBot.objects.get(token=token)
        except TelegramBot.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Unauthorized bot token. Nice try, hacker! :)"}, status=403)

        dispatch_telegram_update(json.loads(request.body), token)
        return JsonResponse({"ok": True})

    @staticmethod
    def get(request, *args, **kwargs):
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)

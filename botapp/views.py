from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .bot import bot, start_polling
import threading

@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        json_str = request.body.decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return HttpResponse("")
    return HttpResponse("Hello from Real Estate Bot!")

def start_bot():
    # Remove previous webhook
    bot.remove_webhook()
    
    # Start polling in a separate thread
    t = threading.Thread(target=start_polling)
    t.daemon = True
    t.start()
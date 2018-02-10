from telegram.ext import Updater, CommandHandler
import logging, subprocess, csv, emoji, requests, datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Hi! Use /set <seconds> to set a timer or /info for getting info about')

def info(bot, update):
    
    update.message.reply_text(get_temperature())
    update.message.reply_text(get_zec())
    
def alarm(bot, job):
    """Send the alarm message."""
    bot.send_message(job.context, text=get_temperature())
    bot.send_message(job.context, text=get_zec())


def set_timer(bot, update, args, job_queue, chat_data):
    """Add a job to the queue."""
    chat_id = update.message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(args[0])
        if due < 0:
            update.message.reply_text('Sorry we can not go back to future!')
            return

        # Add job to queue
        job = job_queue.run_repeating(alarm, due, context=chat_id)
        chat_data['job'] = job

        update.message.reply_text('Timer successfully set!')

    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <seconds>')


def unset(bot, update, chat_data):
    """Remove the job if the user changed their mind."""
    if 'job' not in chat_data:
        update.message.reply_text('You have no active timer')
        return

    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']

    update.message.reply_text('Timer successfully unset!')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def get_temperature():
    sp = subprocess.Popen(['C:\\Program Files\\NVIDIA Corporation\\NVSMI\\nvidia-smi', '--query-gpu=index,name,clocks.gr,power.draw,utilization.gpu,fan.speed,temperature.gpu', '--format=csv,noheader'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out_str = sp.communicate()
    string = ''
    wall = 0
    out_list = out_str[0].decode("utf-8").split('\r\n')

    for i in out_list:
        i = i.splitlines()
        reader = csv.reader(i, delimiter=',')
        if not i == 'o':
            for i in reader:
                n, name, freq, w, load, cool, t = i
                wall += float(w.split()[0])
                string += emoji.emojize('GPU{0}:{1}\n:sound:{2}\n:bulb:{3}\n:bar_chart:{4}\n:snowflake:{5}\n:hotsprings:{6}°\n\n'.format(n,name,freq,w,load,cool,t),use_aliases=True)
    string += 'Sum Watt: {}'.format(wall)
    return string
    
def get_zec():

    miner = 'MINER_TOKEN'
    url = 'https://api-zcash.flypool.org/miner/{}/currentStats'.format(miner)

    r = requests.get(url)
    result = r.json()

    # print(json.dumps(result['data'], sort_keys=True, indent=4, separators=(',', ': ')))
    t = int(result['data']['time'])
    t = datetime.datetime.fromtimestamp(int(t)).strftime('%Y-%m-%d, %H:%M:%S')
    cur = round(result['data']['currentHashrate'],1)
    avg = round(result['data']['averageHashrate'],1)
    usd = round(result['data']['usdPerMin'],4)

    string = emoji.emojize('{0}\nActive:{4}\nCur: {1}, Avg:{2}\n:dollar:{3}\n'.format(t,cur, avg,usd,result['data']['activeWorkers']), use_aliases=True)
    return string

    
def main():
    """Run bot."""
    updater = Updater("TOKEN_TELEGRAM")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("set", set_timer,
                                  pass_args=True,
                                  pass_job_queue=True,
                                  pass_chat_data=True))

    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("unset", unset, pass_chat_data=True))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
    # SIGABRT. This should be used most of the time, since start_polling() is
    # non-blocking and will stop the bot gracefully.
    updater.idle()
    


if __name__ == '__main__':
    main()

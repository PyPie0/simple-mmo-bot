import sys
import requests_html
from bots import TravelBot, QuestBot, JobBot, BattleBot
import utils
import logging


# If you step too fast too often, that might be a flag. If you step for too long, too often (no rests), that might be a flag.
# 4k steps on a single day is already hard to do legit (8 hours). Stick with something like 100-2000 steps a day.
# Have rests built in your bot. Start Work. Make the bot come back in a few hours. Claim Work. Start stepping again. Repeat.
# Avoid doing inhuman things. Avoid calling their API too often.
# I used their profile click function for my own use (checking health/energy/etc.). A few times.




# Examples of using:
# 1) Use of travel bot: python main.py -t 300
# 2) Use of quest bot: python main.py -q https://web.simple-mmo.com/quests/view/61?new_page_refresh=true 100
# 3) Use of battle bot: python main.py -b 100
# 4) Use of job bot: python main.py -j https://web.simple-mmo.com/jobs/view/2 100 (out of service)





if __name__ == '__main__':

	session = requests_html.HTMLSession()
	urls = utils.from_json('urls.json')
	logdata = utils.from_json('logdata.json')


	log_level = logging.DEBUG
	logger = logging.getLogger('BOT')
	c_handler = logging.StreamHandler()
	f_handler = logging.FileHandler('Log.log')
	logger.setLevel(log_level)
	c_handler.setLevel(log_level)
	f_handler.setLevel(log_level)
	c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	c_handler.setFormatter(c_format)
	f_handler.setFormatter(f_format)
	logger.addHandler(c_handler)
	logger.addHandler(f_handler)


	cmd_args = sys.argv[1:]

	def get_bot(Class, *args):
		return Class(*args)

	match cmd_args:
		case ['-t', *args]:
			bot = get_bot(TravelBot, session, urls, logdata, 40, logger)
		case ['-q', *args]:
			bot = get_bot(QuestBot, session, urls, logdata, logger)
		case ['-b', *args]:
			bot = get_bot(BattleBot, session, urls, logdata, logger)
		case ['-j', *args]:
			bot = get_bot(JobBot, session, urls, logdata, logger)
		case _:
			print(f'[*] Enter the correct arguments!\n[*] {args}')
#https://web.simple-mmo.com/quests/view/136?new_page_refresh=true
	bot.login()
	bot.run(*args)
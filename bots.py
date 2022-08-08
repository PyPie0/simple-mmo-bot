import re
import time
import json
import requests_html
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import utils
import logging
from tensorflow import keras
import numpy as np



class BadRequestException(Exception):

	def __init__(self, url=None, resp=None):
		self.url = url
		self.resp = resp

	def __str__(self):
		out = f'\nURL: {self.url}\nResponse: {self.resp}'
		return out


class LoginException(Exception):

	def __init__(self, logdata):
		self.logdata = logdata

	def __str__(self):
		out = f'Unsuccessful login\n{self.logdata}'
		return out


class BaseBot:

	def __init__(self, session, urls, logdata, logger):
		self.session = session
		self.urls = urls
		self.logdata = logdata
		self.logger = logger
		self.headers = {
				'authority': 'web.simple-mmo.com',
				'user-agent': UserAgent().random,
				'accept': '*/*',
				'sec-ch-ua-mobile': '?0',
				'sec-ch-ua-platform': '"Windows"',
				'sec-fetch-dest': 'document',
				'sec-fetch-mode': 'navigate',
				'sec-fetch-site': 'same-origin',
				'sec-fetch-user': '?1',
				'upgrade-insecure-requests': '1',
				'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
			}
		self.not_robot_model = keras.models.load_model('model.h5')
		self.class_names = [
			'Banana', 'Book', 'Bread', 'Candy_Cane', 'Candy_Corn', 'Cannon', 
			'Carrot', 'Cheese', 'Cherry', 'Chest_Piece', 'Clock', 'Crown', 
			'Diamond', 'Egg', 'Empty_Bottle', 'Fire', 'Fish', 'Frog', 'Ghost', 
			'Grapes', 'Gun', 'Hat', 'Helmet', 'House', 'Key', 'Lemon', 'Mushroom',
			'Necklace', 'Orange', 'Pear', 'Pepper', 'Pie', 'Piece_of_Meat', 'Pineapple', 
			'Pretzel', 'Pumpkin', 'Rose', 'Strawberry', 'Watermelon'
		]

	
	def get(self, url, headers=None, render=False):
		if headers is None: 
			headers = self.headers 
		resp = self.session.get(url, headers=headers)
		if resp.status_code in range(200, 400):
			if render:
				resp.html.render()
			return resp
		raise BadRequestException(url, resp)


	def post(self, url, form_data, headers=None):
		if headers is None:
			headers = self.headers
		resp = self.session.post(url, data=form_data, headers=headers)
		if resp.status_code in range(200, 400):
			return resp
		raise BadRequestException(url, resp)


	def _get__token(self):
		self.get(self.urls['base_url'])
		resp = self.get(self.urls['login_url'])
		soup = BeautifulSoup(resp.html.html, 'lxml')
		_token = soup.find('input', {'name': '_token'})['value']
		self.logger.debug(f'_TOKEN:{_token}')
		return _token


	def _get_api_token(self):
		pattern = r"api_token=(.{0,})';"
		resp = self.get(self.urls['home_url'])
		api_token = re.search(pattern, resp.html.html).string.split('api_token=')
		api_token = api_token[1].split("';")[0]
		self.logger.debug(f'API_TOKEN:{api_token}')
		return api_token


	def get_player_info(self):
		info = self.get(self.urls['user_info_url']).html.html
		return json.loads(info)

	
	def login(self):
		self._token = self._get__token()
		form_data = {
			'_token': self._token, 
			'email': self.logdata['email'], 
			'password': self.logdata['password'],
			}
		self.post(self.urls['login_url'], form_data)
		try:
			self.api_token = self._get_api_token()
		except AttributeError:
			raise LoginException(form_data)
		self.username = self.get_player_info()['username']
		self.logger.info(f'LOGIN:{self.username} SUCCESSFUL')


	def __parse_correct_value(self, resp):
		soup = BeautifulSoup(resp.html.html, 'lxml')
		parent_tag = soup.find(text='Please press on the following item:').parent
		correct_value = parent_tag.next_element.next_element.next_element.get_text()
		return correct_value


	def __get_img_list(self, img_amount=4):
		img_list = []
		for i in range(img_amount):
			url = self.urls['image_url']+f'uid={i}'
			img = self.get(url).content
			img_list.append(img)
		return img_list


	def __get_item_code_list(self, resp):
		pattern = r"chooseItem\('(.{0,})'\)"
		item_code_list = re.findall(pattern, resp.html.html)
		return item_code_list


	def __predict(self, img_list, correct_value):
		names = []
		for img in img_list:
			names.append(
				self.class_names[
					np.argmax(
						self.not_robot_model.predict(
							np.array([img])
						)
					)
				].replace('_', ' ')
			)
		try:
			index = names.index(correct_value.strip()) 
		except ValueError:
			index = -1
		self.logger.debug(f'IM-NOT-ROBOT:Selected {names[index]} from {names}')
		return index

	
	def human_verification(self):
		resp = self.get(self.urls['iamnotabot_url'])
		correct_value = self.__parse_correct_value(resp)
		self.logger.debug(f'IM-NOT-ROBOT:Correct value - {correct_value}')
		img_list = [utils.prepoc_image(i) for i in self.__get_img_list()]
		item_code_list = self.__get_item_code_list(resp)
		predicted_i = self.__predict(img_list, correct_value)

		form_data = {
					'data': item_code_list[predicted_i],
					'x': 500,
					'y': 500
					}
		self.post(self.urls['bot_verification_url'], form_data)


	def run(self):
		print(self.username)



class AttackNpcBot(BaseBot):

	def __init__(self, session, urls, logdata, logger, _token, api_token, step_response):
		super().__init__(session, urls, logdata, logger)
		self._token = _token
		self.api_token = api_token
		self.step_response = step_response
		self.min_player_hp = 20

	
	def _to_attack_page(self, npc_id):
		url = self.urls['attack_page_url'].format(npc_id)
		return self.get(url)

	
	def _attack(self, npc_id):
		form_data = {
			'_token': self._token,
			'api_token': self.api_token,
			'special_attack': False
		}
		url = self.urls['attack_url'].format(npc_id)
		resp = self.post(url, form_data)
		return json.loads(resp.html.html)
		

	def get_player_hp(self):
		player_info = self.get_player_info()
		current_hp = int(player_info['current_hp'])
		return current_hp	

	
	def run(self):
		self.logger.info(f'BATTLE:Start')
		pattern = r"attack\/(.{0,})\?"
		try:
			npc_id = re.findall(pattern, self.step_response['text'])[0]
		except KeyError:
			npc_id = self.step_response['id']
		self._to_attack_page(npc_id)
		player_hp = self.get_player_hp()
		while True:
			if player_hp < self.min_player_hp:
				self.logger.debug(f'BATTLE:Not completed')
				break
			attack_info = self._attack(npc_id)
			if (attack_info['opponent_hp'] <= 0 and 
						attack_info['type'] == 'success'):
				self.logger.debug(f'BATTLE:Win')
				self.logger.info(f'BATTLE-INFO:{attack_info}')
				break
			if ((attack_info['type'] == 'error') or 
						(attack_info['player_hp'] <= self.min_player_hp) or 
						("You're dead." in attack_info.get('heading', ''))):
				self.logger.debug(f'FIGHT:Not completed')
				self.logger.info(f'FIGHT-INFO:{attack_info}')
				break
			time.sleep(utils.random_delay(2))


class GatheringMaterialBot(BaseBot):

	def __init__(self, session, urls, logdata, logger, _token, api_token, step_response):
		super().__init__(session, urls, logdata, logger)
		self._token = _token
		self.api_token = api_token
		self.step_response = step_response


	def to_gathering_page(self, material_id):
		url = self.urls['gathering_page_url'].format(material_id)
		return self.get(url)


	def _gather(self, material_id):
		url = self.urls['gathering_url'].format(material_id)
		form_data = {
			'_token': self._token
		}
		resp = self.post(url, form_data)
		return json.loads(resp.html.html)

	
	def run(self):
		self.logger.info(f'GATHERING:Start')
		pattern = r"gather\/(.{0,})\?"
		material_id = re.findall(pattern, self.step_response['text'])[0]
		resp = self.to_gathering_page(material_id)
		if 'You do not have the correct item equipped' in resp.html.html:
			self.logger.info(f'GATHERING:You do not have the correct item equipped')
			return
		while True:
			gather_info = self._gather(material_id)
			if gather_info['gatherEnd']:
				self.logger.info(f'GATHERING:Completed')
				break	
			time.sleep(utils.random_delay(2))



class TravelBot(BaseBot):
	
	def __init__(self, session, urls, logdata, min_hp, logger):
		super().__init__(session, urls, logdata, logger)


	def to_travel_page(self):
		resp = self.get(self.urls['travel_url'])
		return resp

	def take_a_step(self):
		form_data = {
			'_token': self._token,
			'api_token': self.api_token,
			'd_1': 310,
			'd_2': 320,
			's': False,
			'travel_id': 0
		}
		step_response = self.post(self.urls['step_url'], form_data=form_data)
		return json.loads(step_response.html.html)

	
	def run(self, step_amount, *args):
		step_amount = int(step_amount)
		self.to_travel_page()
		for step in range(step_amount):
			
			step_response = self.take_a_step()
			next_wait = step_response['nextwait']

			self.logger.info(f'STEP-INFO:{step_response}')

			if 'Please verify yourself before continuing' in step_response['text']:
				self.logger.debug(f'IM-NOT-ROBOT:Verification required')
				self.human_verification()

			action = step_response.get('step_type', 'default')
			match action:
				case 'npc':
					attack_bot = AttackNpcBot(
						self.session, self.urls, self.logdata, 
						self.logger, self._token, self.api_token, step_response
					)
					attack_bot.run()
					self.to_travel_page()
				case 'material':
					gathering_bot = GatheringMaterialBot(
						self.session, self.urls, self.logdata, 
						self.logger, self._token, self.api_token, step_response)
					gathering_bot.run()
					self.to_travel_page()
			time.sleep(utils.random_delay(next_wait/1000 + 1))


class QuestBot(BaseBot):
	
	def __init__(self, session, urls, logdata, logger):
		super().__init__(session, urls, logdata, logger)


	def _to_quest_page(self, quest_ref):
		resp = self.get(quest_ref)
		return resp


	def get_quest_point_amount(self):
		player_info = self.get_player_info()
		quest_point_amount = player_info['quest_points']
		return quest_point_amount


	def make_quest(self, quest_id):
		url = self.urls['make_quest_url']
		form_data = {
			'api_token': self.api_token,
			'x': 370,
			'y': 590,
			's': 0
		}
		resp = self.post(url.format(quest_id), form_data)
		return json.loads(resp.html.html)


	def run(self, quest_ref, quest_amount, *args):
		quest_amount = int(quest_amount)
		self._to_quest_page(quest_ref)
		quest_point_amount = self.get_quest_point_amount()
		quest_id = utils.extract_int_from_str(quest_ref)
		count = 0
		while count < quest_amount:
			if not quest_point_amount:
				self.logger.debug(f'QUEST:You have no more quest points')
				time.sleep(utils.random_delay(300))
				quest_point_amount = self.get_quest_point_amount()
				continue
			time.sleep(utils.random_delay(2))
			quest_info = self.make_quest(quest_id) 
			if 'Please verify that you are a human' in quest_info['resultText']:
				self.human_verification()
				continue
			count += 1
			quest_point_amount = quest_info['quest_points']
			self.logger.info(f'QUEST-INFO:{quest_info}')


class BattleBot(BaseBot):

	def __init__(self, session, urls, logdata, logger):
		super().__init__(session, urls, logdata, logger)


	def get_energy_amount(self):
		player_info = self.get_player_info()
		energy_amount = int(player_info['energy'])
		return energy_amount


	def to_battle_menu_page(self):
		resp = self.get(self.urls['battle_menu_url'])
		return resp

	def generate_enemy(self):
		url = self.urls['generate_enemy_url']
		form_data = {
			'_token': self._token,
			'api_token': self.api_token,
		}
		enemy_info = self.post(url, form_data=form_data)
		return json.loads(enemy_info.html.html)


	def run(self, enemy_amount, *args):
		enemy_amount = int(enemy_amount)
		self.to_battle_menu_page()
		count = 0
		while count < enemy_amount:
			energy_amount = self.get_energy_amount()
			if not energy_amount:
				self.logger.debug(f'BATTLE:You have no more energy')
				time.sleep(utils.random_delay(300))
				continue
			time.sleep(utils.random_delay(2))
			enemy_info = self.generate_enemy()
			self.logger.info(f'BATTLE:{enemy_info} was generated')
			attack_bot = AttackNpcBot(
				self.session, self.urls, self.logdata, 
				self.logger, self._token, self.api_token, 
				enemy_info
			)
			attack_bot.run()
			count += 1
			self.to_battle_menu_page()
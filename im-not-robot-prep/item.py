import pickle
import os


class Item:

	def __init__(self, true_value, img_list, directory_name='train-data'):
		self.true_value = true_value.replace(' ', '_')
		self.img_list = img_list
		self.dirname = os.getcwd() + '\\' + directory_name
		self.right_img = ''


	def save(self, path=None):
		dirname = path if path else self.dirname
		files_list = os.listdir(dirname)
		true_value_amount = ','.join(files_list).count(self.true_value)
		filename = f'\\{self.true_value}' + f'_{true_value_amount}' + '.pickle'
		with open(dirname + filename, 'wb') as f:
			pickle.dump(self, f)
		print(f'{filename} was saved')



if __name__ == '__main__':
	test_item = Item('test', [])
	test_item.save()
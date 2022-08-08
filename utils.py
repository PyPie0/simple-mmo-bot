import json
import random
from PIL import Image
import io
import numpy as np
import re


def from_json(path):
	with open(path) as file:
		data = json.load(file)
	return data


def from_pickle(item_path):
    with open(item_path, 'rb') as f:
        item = pickle.load(f)
    return item


def to_pickle(item, filename):
    with open(filename, 'wb') as f:
        pickle.dump(item, f)
    print(f'{filename} was saved')


def random_delay(start):
	return start + random.random()


def prepoc_image(img):
    width, height = 28, 28
    img = Image.open(io.BytesIO(img)).convert('L').resize((width, height))
    array = np.array(img)
    return array


def extract_int_from_str(string):
	number = re.search(r'\d+', string).group()
	return int(number)
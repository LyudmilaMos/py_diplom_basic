import requests
from tqdm import tqdm
import json
import datetime

class VkUser:

    url = 'https://api.vk.com/method/'
    token_vk = ''
    version = '5.131'
    params = {
        'access_token': token_vk,
        'v': version
    }

    def __init__(self, user_id=None):

        self.info_photo_list = []
        if user_id is not None:
            self.user_id = user_id
        else:
            self.user_id = requests.get(self.url + 'users.get', self.params).json()['response'][0]['id']

    def photos_get(self, count=None):

        photos_get_url = self.url + 'photos.get'
        if count is not None:
            counter = count
        else:
            counter = 5
        photos_get_params = {
            'owner_id': self.user_id,
            'album_id': 'profile',
            'extended': '1',
            'photo_sizes': '1',
            'count': counter,
            'rev': '1'
            }
        res = requests.get(photos_get_url, params={**self.params, **photos_get_params})
        res.raise_for_status()
        info_photos_dict = res.json()

        print(f'Сформирован запрос для выгрузки фотографий с аккаунта vk.com')
        return info_photos_dict

    def conversion_dict_list(self, categories_dict):
        photo_categories = []

        for dict_photo_list_item in categories_dict['response']['items']:
            dict_photo = {}
            dict_photo['date'] = datetime.datetime.fromtimestamp(dict_photo_list_item['date']).strftime('%d.%m.%Y %H.%M.%S')
            dict_photo['likes'] = dict_photo_list_item['likes']['count']
            example = 0

            for var_url in dict_photo_list_item['sizes']:
                size = var_url['height'] * var_url['width']

                if size > example:
                    example = size
                    dict_photo['url'] = var_url['url']
                    dict_photo['size'] = var_url['type']
            photo_categories.append(dict_photo)

        info_photo_list = []
        num = len(photo_categories)

        for i in range(num - 1):
            dict_photo_list_item = photo_categories.pop()

            for string in photo_categories:

                if string['likes'] == dict_photo_list_item['likes']:
                    dict_photo_list_item['file-name'] = '(' + str(dict_photo_list_item['date']) + ')' + str(dict_photo_list_item['likes']) + '.jpg'
                    
                    break

                else:
                    dict_photo_list_item['file-name'] = str(dict_photo_list_item['likes']) + '.jpg'

            info_photo_list.append(dict_photo_list_item)

        final_dict = photo_categories.pop()
        final_dict['file-name'] = str(final_dict['likes']) + '.jpg'
        info_photo_list.append(final_dict)

        print(f'Сформирован список фотографий по категориям')
        return info_photo_list

    def create_list_information(self, count=None):

        self.info_photo_list = self.conversion_dict_list(self.photos_get(count))
        return

    def create_json(self, name=None):

        if name is not None:
            name_file = name
        else:
            name_file = 'data_output'
        information_list = self.info_photo_list

        for string in information_list:
            del string['likes'], string['date'], string['url']

        with open(name_file + '.json', "w") as f:
            json.dump(information_list, f, ensure_ascii=False, indent=4)

        print(f'Информация записана в файл {name_file}')
        return information_list

class YaUser:

    def __init__(self, token: str):

        self.token = token
        self.directory_upload = ''

    def create_folder(self, direct=None):

        if direct is not None:
            directory = direct
        else:
            directory = 'directory_file'
        response = requests.put(
            "https://cloud-api.yandex.net/v1/disk/resources",
            params={
                        "path": directory
            },
            headers={
                    "Authorization": f"OAuth {self.token}"
            }
            )
        self.directory_upload = directory

        if 'message' in response.json():
            print(f'Папка с названием {directory} уже существует на Я.Диске')
        elif 'method' in response.json():
            print(f'Создана папка {directory} на Я.Диске')
        else:
            response.raise_for_status()
        return directory

    def upload(self, user):

        if isinstance(user, VkUser):

            for load in tqdm(user.info_photo_list, desc='Идет загрузка фотографий', leave=False):
                file_name = load['file-name']
                file_url = load['url']
                response = requests.post(
                    "https://cloud-api.yandex.net/v1/disk/resources/upload",
                    params={
                        "path": f'{self.directory_upload}/{file_name}',
                        'url': file_url
                    },
                    headers={
                    "Authorization": f"OAuth {self.token}"
                    }
                )

        print(f'Успех! Фотографии загружены на Я.Диск.')
        return

    def uploading_photos_to_disk(self, user):

        if isinstance(user, VkUser):

            user.create_list_information()
            self.create_folder()
            self.upload(user)
            user.create_json()

            print(f'\nЗагрузка завершена.')
            return

avatar_user_vk = VkUser()
avatar_user_ya = YaUser()

avatar_user_ya.uploading_photos_to_disk(avatar_user_vk)
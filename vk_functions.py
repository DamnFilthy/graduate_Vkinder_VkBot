import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_config import group_token, user_token, V
from random import randrange
from vk_api.exceptions import ApiError
import requests

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)


# Пишет сообщение пользователю
def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })


# Ищет людей по критериям
def search_users(sex, age_at, age_to, city):
    all_persons = []
    link_profile = 'https://vk.com/id'
    vk_ = vk_api.VkApi(token=user_token)
    response = vk_.method('users.search',
                          {'sort': 1,
                           'sex': sex,
                           'status': 1,
                           'age_from': age_at,
                           'age_to': age_to,
                           'has_photo': 1,
                           'count': 5,
                           'online': 1,
                           'hometown': city
                           })
    for element in response['items']:
        person = [
            element['first_name'],
            element['last_name'],
            link_profile + str(element['id']),
            element['id']
        ]
        all_persons.append(person)
    return all_persons


# Находит фото людей
def get_photo(owner_id):
    vk_ = vk_api.VkApi(token=user_token)
    try:
        response = vk_.method('photos.get',
                              {
                                  'access_token': user_token,
                                  'v': V,
                                  'owner_id': owner_id,
                                  'album_id': 'profile',
                                  'count': 3,
                                  'extended': 1,
                                  'photo_sizes': 1,
                              })
        print(response)
    except ApiError:
        return 'нет доступа к фото'
    users_photos = []

    for i in range(3):
        try:
            users_photos.append(str(response['items'][i]['sizes'][-1]['src']))
        except IndexError:
            users_photos.append('нет фото.')
    return users_photos

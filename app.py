import vk_api
from random import randrange
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_config import group_token
from vk_functions import write_msg, search_users, get_photo
import time

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            request = event.text
            if request == "vkinder":
                write_msg(event.user_id,
                          f"Добрый день, мы найдем вам пару."
                          f"введите искомого человека в формате: - девушка 25-30 Сочи или - мужчина 18-30 Москва.")
            elif request:
                # Ищем девушку
                if request[0:7].lower() == 'девушка':
                    sex = 1
                    age_at = request[8:10]
                    age_to = request[11:13]
                    city = request[14:len(request)].lower()
                    result = search_users(sex, int(age_at), int(age_to), city)
                    for i in range(len(result)):
                        user_photo = get_photo(result[i][3])
                        write_msg(event.user_id, f'{result[i][0]}  {result[i][1]}  {result[i][2]} \n')
                        try:
                            write_msg(event.user_id, f'ее фотки \n {user_photo[0]} \n {user_photo[1]} \n '
                                                     f'{user_photo[2]}')
                        except IndexError:
                            write_msg(event.user_id, f'ее фотки \n {user_photo[0]} \n {user_photo[1]}')

                # Ищем мужчину
                elif request[0:7].lower() == 'мужчина':
                    sex = 2
                    age_at = request[8:10]
                    age_to = request[11:13]
                    city = request[14:len(request)].lower()
                    result = search_users(sex, age_at, age_to, city)
                    for i in range(len(result)):
                        user_photo = get_photo(result[i][3])
                        write_msg(event.user_id,
                                  f'{result[i][0]}  {result[i][1]}  {result[i][2]}, ее фотка {user_photo}')

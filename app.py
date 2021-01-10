import vk_api
from random import randrange
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_config import group_token, user_token
import time
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from models import engine, Base, Session, User, DatingUser, Photos, BlackList
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from vk_functions import write_msg, search_users, get_photo, sort_likes, add_user, register_user, add_user_photos, \
    add_to_black_list, json_create

# Для работы с вк_апи
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
# Для работы с БД
session = Session()
connection = engine.connect()

if __name__ == '__main__':
    # Меню бота
    for start_event in longpoll.listen():
        if start_event.type == VkEventType.MESSAGE_NEW:
            if start_event.to_me:
                request = start_event.text
                if request == "vkinder":
                    write_msg(start_event.user_id,
                              f"Вас приветствует бот - Vkinder\n"
                              f"\nЕсли вы используете его первый раз - пройдите регистрацию.\n"
                              f"Для регистрации введите - Да.\n"
                              f"Если вы уже зарегистрированы - начинайте поиск.\n"
                              f"\nДля поиска - девушка 18-25 Москва\n"
                              f"Перейти в избранное нажмите - 2\n"
                              f"Перейти в черный список - 0\n")
                    # Первый цикл диалога
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                if request.lower() == 'да':
                                    user_token = request[3:len(request)]
                                    write_msg(event.user_id, 'Вы прошли регистрацию.')
                                    write_msg(event.user_id,
                                              f"Для поиска - девушка 18-25 Москва\n"
                                              f"Перейти в избранное нажмите - 2\n"
                                              f"Перейти в черный список - 0\n")
                                    register_user(event.user_id)
                                    continue
                                elif len(request) > 1:
                                    # Ищем партнера
                                    sex = 0
                                    if request[0:7].lower() == 'девушка':
                                        sex = 1
                                    elif request[0:7].lower() == 'мужчина':
                                        sex = 2
                                    age_at = request[8:10]
                                    age_to = request[11:13]
                                    city = request[14:len(request)].lower()
                                    # Ищем анкеты
                                    result = search_users(sex, int(age_at), int(age_to), city)
                                    # Создаем json с результатами
                                    json_create(result)
                                    # Получаем данные по юзеру который работает с ботом
                                    vk_id = event.user_id
                                    current_user_id = session.query(User).filter_by(vk_id=vk_id).first()
                                    # Производим отбор анкет
                                    for i in range(len(result)):
                                        # Проверяем есть ли в БД
                                        id_this_dt_user = result[i][3]
                                        this_dt_user = session.query(DatingUser).filter_by(
                                            vk_id=id_this_dt_user).first()
                                        blocked_user = session.query(BlackList).filter_by(
                                            vk_id=id_this_dt_user).first()
                                        # Получаем фото и сортируем по лайкам
                                        user_photo = get_photo(result[i][3])
                                        if user_photo == 'нет доступа к фото' or this_dt_user is not None or blocked_user is not None:
                                            continue
                                        sorted_user_photo = sort_likes(user_photo)
                                        # Выводим отсортированные данные по анкетам
                                        write_msg(event.user_id, f'\n{result[i][0]}  {result[i][1]}  {result[i][2]}', )
                                        try:
                                            write_msg(event.user_id, f'фото:',
                                                      attachment=','.join
                                                      ([sorted_user_photo[-1][1], sorted_user_photo[-2][1],
                                                        sorted_user_photo[-3][1]]))
                                        except IndexError:
                                            for photo in range(len(sorted_user_photo)):
                                                write_msg(event.user_id, f'фото:',
                                                          attachment=sorted_user_photo[photo][1])
                                        # Второй цикл диалога
                                        write_msg(event.user_id, '1 - Добавить, 2 - Заблокировать, 0 - Далее')
                                        for new_event in longpoll.listen():
                                            if new_event.type == VkEventType.MESSAGE_NEW:
                                                if new_event.to_me:
                                                    request = new_event.text
                                                    if request == '0':
                                                        # Проверка на последнюю запись
                                                        if i >= len(result) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в избранное - 2')
                                                            write_msg(event.user_id, f'Перейти в черный список - 0')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                            write_msg(event.user_id, f'Меню бота - Vkinder')
                                                        break
                                                    # Добавляем пользователя в избранное
                                                    elif request == '1':
                                                        # Проверка на последнюю запись
                                                        if i >= len(result) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в избранное - 2')
                                                            write_msg(event.user_id, f'Перейти в черный список - 0')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                            write_msg(event.user_id, f'Меню бота - Vkinder')
                                                        # Пробуем добавить анкету в БД
                                                        add_user(new_event.user_id, result[i][3], result[i][1],
                                                                 result[i][0], city, result[i][2], current_user_id.id)
                                                        # Пробуем добавить фото анкеты в БД
                                                        add_user_photos(new_event.user_id, sorted_user_photo[0][1],
                                                                        sorted_user_photo[0][0], current_user_id.id)
                                                        break
                                                    elif request == '2':
                                                        # Проверка на последнюю запись
                                                        if i >= len(result) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в избранное - 2')
                                                            write_msg(event.user_id, f'Перейти в черный список - 0')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                            write_msg(event.user_id, f'Меню бота - Vkinder')
                                                        # Блокируем
                                                        add_to_black_list(new_event.user_id, result[i][3], result[i][1],
                                                                          result[i][0], city, result[i][2],
                                                                          sorted_user_photo[0][1],
                                                                          sorted_user_photo[0][0], current_user_id.id)
                                                        break

                                # Ищем пользователя в БД
                                elif request == '2':
                                    # Получаем данные по юзеру который работает с ботом
                                    vk_id = event.user_id
                                    current_user_id = session.query(User).filter_by(vk_id=vk_id).first()
                                    # Находим все анкеты из избранного которые добавил данный юзер
                                    all_users = session.query(DatingUser).filter_by(id_user=current_user_id.id).all()
                                    write_msg(event.user_id, f'Избранные анкеты:')
                                    for num, user in enumerate(all_users):
                                        write_msg(event.user_id, f'{user.first_name}, {user.second_name}, {user.link}')
                                        write_msg(event.user_id, '1 - Удалить из избранного, 0 - Далее')
                                        for new_event in longpoll.listen():
                                            if new_event.type == VkEventType.MESSAGE_NEW:
                                                if new_event.to_me:
                                                    request = new_event.text
                                                    if request == '0':
                                                        if num >= len(all_users) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в черный список - 0')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                        break
                                                    elif request == '1':
                                                        session.delete(user)
                                                        write_msg(event.user_id, f'Анкета успешно удалена.')
                                                        if num >= len(all_users) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в черный список - 0')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                        break
                                # Ищем черный список
                                elif request == '0':
                                    # Получаем данные по юзеру который работает с ботом
                                    vk_id = event.user_id
                                    current_user_id = session.query(User).filter_by(vk_id=vk_id).first()
                                    # Находим все анкеты из избранного которые добавил данный юзер
                                    all_users = session.query(BlackList).filter_by(id_user=current_user_id.id).all()
                                    write_msg(event.user_id, f'Анкеты в черном списке:')
                                    for num, user in enumerate(all_users):
                                        write_msg(event.user_id, f'{user.first_name}, {user.second_name}, {user.link}')
                                        write_msg(event.user_id, '1 - Удалить из черного списка, 0 - Далее')
                                        for new_event in longpoll.listen():
                                            if new_event.type == VkEventType.MESSAGE_NEW:
                                                if new_event.to_me:
                                                    request = new_event.text
                                                    if request == '0':
                                                        if num >= len(all_users) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в избранное - 2')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                        break
                                                    elif request == '1':
                                                        session.delete(user)
                                                        write_msg(event.user_id, f'Анкета успешно удалена')
                                                        if num >= len(all_users) - 1:
                                                            write_msg(event.user_id, f'Это была последняя анкета.')
                                                            write_msg(event.user_id, f'Перейти в избранное - 2')
                                                            write_msg(event.user_id, f'Поиск - девушка 18-25 москва')
                                                        break

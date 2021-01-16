import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from models import engine, Session, User, DatingUser, Photos, BlackList
from vk_functions import search_users, get_photo, sort_likes, json_create
from models import write_msg, register_user, add_user, add_user_photos, add_to_black_list
from vk_config import group_token

# Для работы с вк_апи
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
# Для работы с БД
session = Session()
connection = engine.connect()


# Ожидание пользовательского ввода
def loop_bot():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW:
            if this_event.to_me:
                message_text = this_event.text
                return message_text, this_event.user_id


# Menu Bot
def menu_bot(id_num):
    write_msg(id_num,
              f"Вас приветствует бот - Vkinder\n"
              f"\nЕсли вы используете его первый раз - пройдите регистрацию.\n"
              f"Для регистрации введите - Да.\n"
              f"Если вы уже зарегистрированы - начинайте поиск.\n"
              f"\nДля поиска - девушка 18-25 Москва\n"
              f"Перейти в избранное нажмите - 2\n"
              f"Перейти в черный список - 0\n")


# Show info
def show_info():
    write_msg(user_id, f'Это была последняя анкета.'
                       f'Перейти в избранное - 2'
                       f'Перейти в черный список - 0'
                       f'Поиск - девушка 18-25 москва'
                       f'Меню бота - Vkinder')


# Register new user
def reg_new_user(id_num):
    write_msg(id_num, 'Вы прошли регистрацию.')
    write_msg(id_num,
              f"Vkinder - для активации бота\n")
    register_user(id_num)


# Work with favorites in DB
def go_to_favorites(ids):
    # Получаем данные по юзеру который работает с ботом
    vk_ids = ids
    current_users_id = session.query(User).filter_by(vk_id=vk_ids).first()
    # Находим все анкеты из избранного которые добавил данный юзер
    alls_users = session.query(DatingUser).filter_by(id_user=current_users_id.id).all()
    write_msg(ids, f'Избранные анкеты:')
    for nums, users in enumerate(alls_users):
        write_msg(ids, f'{users.first_name}, {users.second_name}, {users.link}')
        write_msg(ids, '1 - Удалить из избранного, 0 - Далее \nq - Выход')
        # Принимает ответ пользователя
        msg_texts, user_ids = loop_bot()
        if msg_text == '0':
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'Vkinder - вернуться в меню\n')
        # Удаляем запись из бд - избранное
        elif msg_texts == '1':
            session.delete(users)
            session.commit()
            write_msg(user_ids, f'Анкета успешно удалена.')
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'Vkinder - вернуться в меню\n')
        # Выход
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'Vkinder - для активации бота.')
            break


# Work with blacklist in DB
def go_to_blacklist(ids):
    # Получаем данные по юзеру который работает с ботом
    vk_ids = ids
    current_users_id = session.query(User).filter_by(vk_id=vk_ids).first()
    # Находим все анкеты из избранного которые добавил данный юзер
    all_users = session.query(BlackList).filter_by(id_user=current_users_id.id).all()
    write_msg(ids, f'Анкеты в черном списке:')
    for num, user in enumerate(all_users):
        write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
        write_msg(ids, '1 - Удалить из черного списка, 0 - Далее \nq - Выход')
        # Получаем ответ пользователя
        msg_texts, user_ids = loop_bot()
        if msg_texts == '0':
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'Vkinder - вернуться в меню\n')
        # Удаляем запись из бд - черный список
        elif msg_texts == '1':
            session.delete(user)
            session.commit()
            write_msg(user_ids, f'Анкета успешно удалена')
            if num >= len(all_users) - 1:
                write_msg(user_ids, f'Это была последняя анкета.\n'
                                    f'Vkinder - вернуться в меню\n')
        # Выход
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'Vkinder - для активации бота.')
            break


if __name__ == '__main__':
    while True:
        # Ждем пользовательский ввод
        msg_text, user_id = loop_bot()
        # Меню бота
        if msg_text == "vkinder":
            menu_bot(user_id)
            # Ждем пользовательский ввод
            msg_text, user_id = loop_bot()
            # Регистрируем пользователя в БД
            if msg_text.lower() == 'да':
                reg_new_user(user_id)
            # Ищем партнера
            elif len(msg_text) > 1:
                sex = 0
                if msg_text[0:7].lower() == 'девушка':
                    sex = 1
                elif msg_text[0:7].lower() == 'мужчина':
                    sex = 2
                age_at = msg_text[8:10]
                if int(age_at) < 18:
                    write_msg(user_id, 'ай ай ай, Выставлен минимальный возраст - 18 лет.')
                    age_to = 18
                age_to = msg_text[11:14]
                if int(age_to) >= 100:
                    write_msg(user_id, 'Некрофил да? выставлено максимальное значение 99 лет.')
                    age_to = 99
                city = msg_text[14:len(msg_text)].lower()
                # Ищем анкеты
                result = search_users(sex, int(age_at), int(age_to), city)
                # Создаем json с результатами
                json_create(result)
                # Получаем данные по юзеру который работает с ботом
                vk_id = user_id
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
                    write_msg(user_id, f'\n{result[i][0]}  {result[i][1]}  {result[i][2]}', )
                    try:
                        write_msg(user_id, f'фото:',
                                  attachment=','.join
                                  ([sorted_user_photo[-1][1], sorted_user_photo[-2][1],
                                    sorted_user_photo[-3][1]]))
                    except IndexError:
                        for photo in range(len(sorted_user_photo)):
                            write_msg(user_id, f'фото:',
                                      attachment=sorted_user_photo[photo][1])
                    # Ждем пользовательский ввод
                    write_msg(user_id, '1 - Добавить, 2 - Заблокировать, 0 - Далее, \nq - выход из поиска')
                    msg_text, user_id = loop_bot()
                    if msg_text == '0':
                        # Проверка на последнюю запись
                        if i >= len(result) - 1:
                            show_info()
                    # Добавляем пользователя в избранное
                    elif msg_text == '1':
                        # Проверка на последнюю запись
                        if i >= len(result) - 1:
                            show_info()
                            break
                        # Пробуем добавить анкету в БД
                        try:
                            add_user(user_id, result[i][3], result[i][1],
                                     result[i][0], city, result[i][2], current_user_id.id)
                            # Пробуем добавить фото анкеты в БД
                            add_user_photos(user_id, sorted_user_photo[0][1],
                                            sorted_user_photo[0][0], current_user_id.id)
                        except AttributeError:
                            write_msg(user_id, 'Вы не зарегистрировались!\n Введите Vkinder для перезагрузки бота')
                            break
                    # Добавляем пользователя в черный список
                    elif msg_text == '2':
                        # Проверка на последнюю запись
                        if i >= len(result) - 1:
                            show_info()
                        # Блокируем
                        add_to_black_list(user_id, result[i][3], result[i][1],
                                          result[i][0], city, result[i][2],
                                          sorted_user_photo[0][1],
                                          sorted_user_photo[0][0], current_user_id.id)
                    elif msg_text.lower() == 'q':
                        write_msg(user_id, 'Введите Vkinder для активации бота')
                        break

            # Переходим в избранное
            elif msg_text == '2':
                go_to_favorites(user_id)

            # Переходим в черный список
            elif msg_text == '0':
                go_to_blacklist(user_id)

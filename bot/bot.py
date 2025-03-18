import logging
import os
import re
import paramiko
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Получение токена бота из переменных окружения
TOKEN = os.getenv('TOKEN')
SSH_HOST = os.getenv('RM_HOST')
SSH_PORT = int(os.getenv('RM_PORT', 22))
SSH_USER = os.getenv('RM_USER')
SSH_PASSWORD = os.getenv('RM_PASSWORD')

# Регулярные выражения для поиска email и номеров телефонов
EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_REGEX = r'(\+7|8)\s*[\(]?(\d{3})[\)]?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'

# Регулярное выражение для проверки сложности пароля
PASSWORD_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#]).{8,}$'

# Функция для выполнения команды на удаленном сервере
def execute_command(command):
    try:
        # Установка SSH-соединения
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        # Выполнение команды
        stdin, stdout, stderr = client.exec_command(command)
        result = stdout.read().decode()
        error = stderr.read().decode()

        # Закрытие соединения
        client.close()

        if error:
            return f"Ошибка: {error}"
        return result
    except Exception as e:
        return f"Ошибка подключения: {str(e)}"

# Функция для выполнения запроса к базе данных
def execute_db_query(query, params=None):
    try:
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cursor = conn.cursor()
        logger.info(f"Executing query: {query} with params: {params}")  # Логирование запроса
        cursor.execute(query, params)

        # Проверяем, является ли запрос SELECT (возвращает данные)
        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            result = None  # Для INSERT, UPDATE, DELETE и т.д.

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Query executed successfully")  # Логирование успешного выполнения
        return result
    except Exception as e:
        logger.error(f"Ошибка выполнения запроса: {str(e)}")  # Логирование ошибки
        return f"Ошибка выполнения запроса: {str(e)}"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu = """
Привет! Вот список доступных команд:

- /find_email: Найти email в тексте.
- /find_phone_number: Найти номер телефона в тексте.
- /verify_password: Проверить сложность пароля.
- /get_release: Информация о релизе системы.
- /get_uname: Информация об архитектуре системы.
- /get_uptime: Время работы системы.
- /get_df: Информация о файловой системе.
- /get_free: Информация об оперативной памяти.
- /get_mpstat: Информация о производительности системы.
- /get_w: Информация о пользователях.
- /get_auths: Последние 10 входов в систему.
- /get_critical: Последние 5 критических событий.
- /get_ps: Информация о запущенных процессах.
- /get_ss: Информация об используемых портах.
- /get_apt_list: Информация об установленных пакетах.
- /get_services: Информация о запущенных сервисах.
- /get_repl_logs: Логи репликации.
- /get_emails: Получить email-адреса из базы данных.
- /get_phone_numbers: Получить номера телефонов из базы данных.
"""
    await update.message.reply_text(menu)
    logger.info("Команда /start была запущена")

# Обработчик команды /find_email
async def find_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска email.')
    context.user_data['next_command'] = 'find_email'

# Обработчик команды /find_phone_number
async def find_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пожалуйста, отправьте текст для поиска номера телефона.')
    context.user_data['next_command'] = 'find_phone_number'

# Обработчик команды /verify_password
async def verify_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Пожалуйста, отправьте пароль для проверки.')
    context.user_data['next_command'] = 'verify_password'

# Обработчик команды /get_release
async def get_release(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('cat /etc/os-release')
    await update.message.reply_text(f"Информация о релизе:\n{result}")

# Обработчик команды /get_uname
async def get_uname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('uname -a')
    await update.message.reply_text(f"Информация об архитектуре:\n{result}")

# Обработчик команды /get_uptime
async def get_uptime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('uptime -p')
    await update.message.reply_text(f"Время работы:\n{result}")

# Обработчик команды /get_df
async def get_df(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('df -h')
    await update.message.reply_text(f"Информация о файловой системе:\n{result}")

# Обработчик команды /get_free
async def get_free(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('free -h')
    await update.message.reply_text(f"Информация об оперативной памяти:\n{result}")

# Обработчик команды /get_mpstat
async def get_mpstat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('mpstat')
    await update.message.reply_text(f"Информация о производительности системы:\n{result}")

# Обработчик команды /get_w
async def get_w(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('w')
    await update.message.reply_text(f"Информация о пользователях:\n{result}")

# Обработчик команды /get_auths
async def get_auths(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('last -i | head -n 10')
    await update.message.reply_text(f"Последние 10 входов в систему:\n{result}")

# Обработчик команды /get_critical
async def get_critical(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('grep -i "critical" /var/log/syslog | tail -n 5')
    await update.message.reply_text(f"Последние 5 критических событий:\n{result}")

# Обработчик команды /get_ps
async def get_ps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('ps aux --sort=-%mem | head -n 20')

    # Разбиваем результат на части по 4000 символов
    max_length = 4000
    for i in range(0, len(result), max_length):
        await update.message.reply_text(f"Информация о запущенных процессах (часть {i//max_length + 1}):\n{result[i:i+max_length]}")

# Обработчик команды /get_ss
async def get_ss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('ss -tuln')
    await update.message.reply_text(f"Информация об используемых портах:\n{result}")

# Обработчик команды /get_apt_list
async def get_apt_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['next_command'] = 'get_apt_list'
    await update.message.reply_text('Введите название пакета для поиска или напишите "все" для вывода всех пакетов.')

# Обработчик команды /get_services
async def get_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('systemctl list-units --type=service --state=active')

    # Разбиваем результат на части по 4000 символов
    max_length = 4000
    for i in range(0, len(result), max_length):
        await update.message.reply_text(f"Информация о запущенных сервисах (часть {i//max_length + 1}):\n{result[i:i+max_length]}")

# Обработчик команды /get_repl_logs
async def get_repl_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = execute_command('tail -n 50 /var/log/postgresql/postgresql-16-main.log | grep -i "replication"')
    await update.message.reply_text(f"Логи репликации:\n{result}")

# Обработчик команды /get_emails
async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        result = execute_db_query("SELECT email FROM emails")
        if result:
            emails = "\n".join([row[0] for row in result])
            await update.message.reply_text(f"Email-адреса:\n{emails}")
        else:
            await update.message.reply_text("Email-адреса не найдены.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении email-адресов: {str(e)}")

# Обработчик команды /get_phone_numbers
async def get_phone_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        result = execute_db_query("SELECT phone_number FROM phone_numbers")
        if result:
            phone_numbers = "\n".join([row[0] for row in result])
            await update.message.reply_text(f"Номера телефонов:\n{phone_numbers}")
        else:
            await update.message.reply_text("Номера телефонов не найдены.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении номеров телефонов: {str(e)}")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    if 'next_command' in user_data:
        command = user_data['next_command']
        text = update.message.text

        if command == 'find_email':
            emails = re.findall(EMAIL_REGEX, text)
            if emails:
                await update.message.reply_text('\n'.join(emails))
                await update.message.reply_text('Хотите сохранить найденные email-адреса в базу данных? (да/нет)')
                user_data['pending_emails'] = emails
                user_data['next_command'] = 'save_emails'
                logger.info(f"Emails found: {emails}")  # Логирование найденных email-адресов
            else:
                await update.message.reply_text('Email-адреса не обнаружены.')

        elif command == 'save_emails':
            logger.info(f"Command: {command}, Text: {text}")  # Логирование текущего состояния
            if text.lower() in ['да', 'yes', 'y', 'д']:
                emails = user_data.get('pending_emails', [])
                if not emails:
                    await update.message.reply_text('Нет ожидающих email-адресов для сохранения.')
                    return

                for email in emails:
                    logger.info(f"Attempting to save email: {email}")  # Логирование попытки сохранения
                    result = execute_db_query("INSERT INTO emails (email) VALUES (%s) ON CONFLICT DO NOTHING", (email,))
                    if isinstance(result, str):  # Проверка на наличие ошибки
                        logger.error(f"Ошибка при сохранении email {email}: {result}")
                        await update.message.reply_text(f"Ошибка при сохранении email {email}: {result}")
                    else:
                        logger.info(f"Email {email} успешно сохранен.")
                await update.message.reply_text('Email-адреса успешно сохранены в базу данных.')

                # Очищаем pending_emails
                if 'pending_emails' in user_data:
                    del user_data['pending_emails']
            else:
                await update.message.reply_text('Сохранение отменено.')

        elif command == 'find_phone_number':
            # Используем re.finditer для получения объектов совпадений
            phones = re.finditer(PHONE_REGEX, text)
            formatted_phones = []
            for phone in phones:
                full_number = phone.group(0)
                # Удаляем все нецифровые символы, кроме '+'
                cleaned_number = re.sub(r'[^\d+]', '', full_number)
                formatted_phones.append(cleaned_number)

            if formatted_phones:
                await update.message.reply_text('\n'.join(formatted_phones))
            else:
                await update.message.reply_text('Телефон не обнаружен.')

        elif command == 'verify_password':
            if re.match(PASSWORD_REGEX, text):
                await update.message.reply_text('Пароль сложный.')
            else:
                await update.message.reply_text('Пароль простой.')

        elif command == 'get_apt_list':
            if text.lower() == 'все':
                result = execute_command('dpkg-query -l')
            else:
                result = execute_command(f'dpkg-query -l | grep -i {text}')
            await update.message.reply_text(f"Информация об установленных пакетах:\n{result}")

        
   
            
            
            
            # Удаляем ключ только после завершения всей логики
            if 'next_command' in user_data:
                del user_data['next_command']

def main() -> None:
    # Создание экземпляра Application и передача токена
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('find_email', find_email))
    application.add_handler(CommandHandler('find_phone_number', find_phone_number))
    application.add_handler(CommandHandler('verify_password', verify_password))
    application.add_handler(CommandHandler('get_release', get_release))
    application.add_handler(CommandHandler('get_uname', get_uname))
    application.add_handler(CommandHandler('get_uptime', get_uptime))
    application.add_handler(CommandHandler('get_df', get_df))
    application.add_handler(CommandHandler('get_free', get_free))
    application.add_handler(CommandHandler('get_mpstat', get_mpstat))
    application.add_handler(CommandHandler('get_w', get_w))
    application.add_handler(CommandHandler('get_auths', get_auths))
    application.add_handler(CommandHandler('get_critical', get_critical))
    application.add_handler(CommandHandler('get_ps', get_ps))
    application.add_handler(CommandHandler('get_ss', get_ss))
    application.add_handler(CommandHandler('get_apt_list', get_apt_list))
    application.add_handler(CommandHandler('get_services', get_services))
    application.add_handler(CommandHandler('get_repl_logs', get_repl_logs))
    application.add_handler(CommandHandler('get_emails', get_emails))
    application.add_handler(CommandHandler('get_phone_numbers', get_phone_numbers))

    # Добавление обработчика текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
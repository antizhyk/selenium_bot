import re
import os
import time
import random
import pyperclip
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException


def get_local_path():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return current_dir


def get_file_path(filename):
    current_dir = get_local_path()
    current_file_path = os.path.join(current_dir, filename)
    if os.path.exists(current_file_path):
        return current_file_path
    else:
        return ('file path does not exist')


class MessagesClass:
    def __init__(self, driver, logger):
        self.driver = driver
        self.logger = logger
        self.chat_count = 0

    def init_chat(self, chat_id, messages):
        try:
            self.logger.log(f"Инициализация чата {chat_id}")
            self.chat_count = self.init_data(self.driver, chat_id)
            if self.chat_count == 0:
                return False

            if self.chat_count > 5:
                self.chat_count = 5

            self.logger.log(f"Количество сообщений в чате: {self.chat_count}")

            is_set_messages = self.check_messages()
            if not is_set_messages:
                return False

            accounts_link = self.get_accounts_link()

            accounts_link = list(filter(None, accounts_link))
            if len(accounts_link) == 0:
                return False


            print('accounts_link', accounts_link)
            time.sleep(random.randint(5, 9))
            self.logger.log(f"Чат {chat_id} инициализирован")

            self.post_message(messages)
            # return accounts_link
        except Exception as e:
            self.logger.log(f"Произошла ошибка в init_chat: {e}")
            return False

    def init_data(self, driver, chat_id):
        try:
            self.logger.log(f"Инициализация чата {chat_id}")
            # got ot https://twitter.com/messages/{chat_id}
            driver.get(f'https://twitter.com/messages/{chat_id}')
            # Случайная задержка перед нажатием кнопки сообщений
            time.sleep(random.randint(1, 3))

            # Случайная задержка перед получением заголовка чата
            h2_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[@data-testid="DMGroupConversationTitle"]')))
            h2_title = h2_element.text

            self.logger.log(f'Chat title: {h2_title}')
            if h2_title == 'Direct Messages':
                return None

            regex = r'(\d+)(\\|\/)(\d+)'
            match = re.search(regex, h2_title)
            if not match or not match.group(3):
                return 0
            return int(match.group(3))
        except Exception as e:
            self.logger.log(f"Произошла ошибка в init_data: {e}")
            return False

    def check_messages(self):
        try:
            message = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '(//div[@data-testid="messageEntry"])[position() = last() - 2]')))
            print(message.text)
            if message:
                return True
        except Exception as e:
            self.logger.log(f"Произошла ошибка в check_messages: {e}")
            return False

    def get_accounts_link(self):
        try:
            scroll_container = self.driver.find_element(By.XPATH, '//div[@data-testid="DmActivityViewport"]')
            # Прокрутка контейнера вниз
            self.driver.execute_script("arguments[0].scrollBy(0, 1000);", scroll_container)
            self.logger.log(f"Прокрутка контейнера вниз")
            time.sleep(random.randint(2, 3))
            accounts_link = []
            messages = self.driver.find_elements(By.XPATH,
                                                 '//div[@data-testid="DmScrollerContainer"]//div[@data-testid="messageEntry"]')
            # get elements by chat_count
            last_messages = messages[-self.chat_count:]
            for message in last_messages:
                # set background color red
                self.driver.execute_script("arguments[0].style.backgroundColor = 'red';", message)
                message_style = message.value_of_css_property("align-items")
                print('message_style', message_style)

                if message_style != 'flex-start':
                    self.logger.log(f"Найдено отправленное сообщение, выходим из чата")
                    return []

                time.sleep(random.randint(2, 3))
                self.logger.log(f"Прокрутка к сообщению для получения ссылки")
                # Прокрутка контейнера к сообщению
                self.driver.execute_script("arguments[0].scrollIntoView();", message)
                text = message.find_element(By.XPATH, "..").text

                # Проверка наличия ключевых слов
                keywords = ['bot', 'Bot', 'BOT', 'robot', 'Robot', 'ROBOT']
                if any(keyword in text for keyword in keywords):
                    print('continue', text)
                    continue
                # get all links in messages and output
                links_elements = message.find_elements(By.TAG_NAME, 'a')
                links = [link.get_attribute("href") for link in links_elements]
                is_add = False
                for link in links_elements:
                    print('link', link.text)
                    matches = re.findall(r'@(\w+)', link.text)
                    if matches:
                        print('matches', matches)
                        accounts_link.append(link.get_attribute("href"))
                        is_add = True
                        break

                if is_add:
                    continue

                filtered_links = [
                    link for link in links
                    if urlparse(link).netloc == 'twitter.com' and len(urlparse(link).path.split('/')) == 2
                ]

                accounts_link.append(filtered_links[0] if filtered_links else None)

                # Логирование количества найденных ссылок
                print(f'Find account link: {len(accounts_link)} of {self.chat_count}')

                # Получение высоты сообщения
                message_height = message.size['height']

                # Прокрутка контейнера назад на высоту сообщения
                container = self.driver.find_element(By.XPATH, '//div[@data-testid="DmActivityViewport"]')
                self.driver.execute_script("arguments[0].scrollBy(0, -arguments[1]);", container, message_height)
            return accounts_link
        except Exception as e:
            self.logger.log(f"Произошла ошибка в get_accounts_link: {e}")
            return False

    def post_message(self, messages):
        try:
            # Выбираем случайное сообщение из массива
            message = random.choice(messages)

            file_path = message.get('media')
            image_uri = message.get('imageUri')

            file_exists = os.path.exists(file_path)
            if not file_exists:
                folder = f'./media/{message["_id"]}'
                if not os.path.exists(folder):
                    os.mkdir(folder)

            path = file_path

            writer = open(path, 'wb')

            response = requests.get(image_uri, stream=True)
            if response.status_code == 200:
                writer.write(response.content)
            writer.close()

            # Отправка сообщения
    #         const fileBtn = await page.waitForXPath('//span[@class="message-new-media-btn"]');
    #       await this.cursor.click((fileBtn as ElementHandle<Element>));
    #       const fileInput = await page.waitForSelector('input[type="file"]');
    #       await fileInput.uploadFile(filePath);
            print('path', os.path.abspath(path))
            # file_btn = self.driver.find_element(By.XPATH, '//aside/div[2]/div[1]/div[1]')
            # file_btn.click()

            # self.driver.file_detector = LocalFileDetector()

            file_input = self.driver.find_element(By.XPATH, '//input[@type="file"]')
            print('file_input', file_input)
            file_input.send_keys(os.path.abspath(path))

            action = ActionChains(self.driver)

            text = message.get('message')
            print('text', text)

            label = self.driver.find_element(By.CLASS_NAME, 'DraftEditor-root')
            print('label', label)
            label.click()
            time.sleep(random.randint(1, 2))
            self.driver.execute_script("navigator.clipboard.writeText(arguments[0])", text)
            # Нажимаем и удерживаем клавишу Control, затем нажимаем клавишу V, и отпускаем Control
            action.key_down(Keys.CONTROL)
            action.send_keys('v')
            action.key_up(Keys.CONTROL)

            # Выполняем цепочку действий
            action.perform()

            time.sleep(random.randint(2, 3))

            # //div[@data-testid="dmComposerSendButton"]
            send_button = self.driver.find_element(By.XPATH, '//div[@data-testid="dmComposerSendButton"]')
            send_button.click()

            time.sleep(random.randint(60, 90))
            return True
        except Exception as e:
            self.logger.log(f"Произошла ошибка в post_message: {e}")
            return False


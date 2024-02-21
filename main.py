import certifi
import requests
import hashlib
import time

from bson import ObjectId

import logs
from messages import MessagesClass
from accounts import AccountsClass

from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions

uri = "mongodb+srv://01antizykit:9qUH8jrZkYUQb7vZ@cluster0.xxtchg2.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
tlsCAFile = certifi.where()
dbClient = MongoClient(uri, tlsCAFile=tlsCAFile)
# Send a ping to confirm a successful connection
try:
    dbClient.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = dbClient['app']

MLX_BASE = "https://api.multilogin.com"
MLX_LAUNCHER = "https://launcher.mlx.yt:45001/api/v1"
LOCALHOST = "http://127.0.0.1"
HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# TODO: Insert your account information in both variables below.
USERNAME = "01antizyk.it@gmail.com"
PASSWORD = "20022024Azura!"

# TODO: Insert the Folder ID and the Profile ID below
FOLDER_ID = "0682a151-2a92-423e-9d3d-a5a5c3f499f2"
PROFILE_ID = "04d3801a-f9af-483c-bae8-4ef686e1a08a"


def signin() -> str:
    payload = {
        'email': USERNAME,
        'password': hashlib.md5(PASSWORD.encode()).hexdigest()
    }

    r = requests.post(f'{MLX_BASE}/user/signin', json=payload)

    if (r.status_code != 200):
        print(f'\nError during login: {r.text}\n')
    else:
        response = r.json()['data']
    token = response['token']

    return token


def start_profile() -> webdriver:
    r = requests.get(f'{MLX_LAUNCHER}/profile/f/{FOLDER_ID}/p/{PROFILE_ID}/start?automation_type=selenium',
                     headers=HEADERS)

    response = r.json()

    if (r.status_code != 200):
        print(f'\nError while starting profile: {r.text}\n')
    else:
        print(f'\nProfile {PROFILE_ID} started.\n')

    selenium_port = response.get('status').get('message')
    options = ChromiumOptions()
    options.add_argument("--headless=new")

    driver = webdriver.Remote(command_executor=f'{LOCALHOST}:{selenium_port}', options=options)

    return driver


def stop_profile() -> None:
    r = requests.get(f'{MLX_LAUNCHER}/profile/stop/p/{PROFILE_ID}', headers=HEADERS)

    if (r.status_code != 200):
        print(f'\nError while stopping profile: {r.text}\n')
    else:
        print(f'\nProfile {PROFILE_ID} stopped.\n')


token = signin()
HEADERS.update({"Authorization": f'Bearer {token}'})

driver = start_profile()

# todo - место для напсиания кода

logger = logs.setup_logging("65c7aef468882d0aec09d74a")
logger_with_emit = logs.LoggerWithEmit(logger, "65c7aef468882d0aec09d74a")
logger_with_emit.log("Starting main process for account: 65c7aef468882d0aec09d74a")

messagesClient = MessagesClass(driver, logger_with_emit)
accountsClient = AccountsClass(driver, logger_with_emit)

chats = list(db['chats'].find({'account': ObjectId("65c7aef468882d0aec09d74a")}, sort=[("position", 1)]))
accountConfig = db['accountconfigs'].find_one({'account': ObjectId("65c7aef468882d0aec09d74a")})
print("accountConfig", accountConfig['_id'])
messages = list(db['accountmessages'].find({'accountConfig': ObjectId(accountConfig['_id'])}))


for chat in chats:
    messagesClient.init_chat(chat['twitterId'], messages)

# driver.get('https://multilogin.com/')
time.sleep(60)
# stop_profile()

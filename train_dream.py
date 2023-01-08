# -*- coding: utf-8 -*-
"""
Created on Mon May 23 02:01:02 2022

@author: 88698
"""
from flask import Flask
from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import time
import requests
from bs4 import BeautifulSoup
import os
app = Flask(__name__)
# token
line_bot_api = LineBotApi('LINE 金鑰 or TOKEN')
# secret
handler = WebhookHandler('LINE 金鑰 or TOKEN')
# uerid
line_bot_api.push_message('', TextSendMessage(text='歡迎搭乘無限列車'))


url = 'https://www.railway.gov.tw/tra-tip-web/tip'
staDic = {}
today = time.strftime('%Y/%m/%d')


def getTrip():
    global url, staDic, today, sTime, eTime, start, data
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')
    stations = soup.find(id='cityHot').ul.find_all('li')
    for station in stations:
        stationName = station.button.text
        stationId = station.button['title']
        staDic[stationName] = stationId
    csrf = soup.find(id='queryForm').input['value']
    formData = {
        'trainTypeList': 'ALL',
        'transfer': 'ONE',
        'startOrEndTime': 'true',
        'startStation': staDic[data[0]],
        'endStation': staDic[data[1]],
        'rideDate': today,
        'startTime': data[2],
        'endTime': data[3],
        '_csrf': csrf
    }
    query_url = 'https://www.railway.gov.tw' + \
        soup.find(id="queryForm")['action']
    print(query_url)
    query_response = requests.post(query_url, data=formData)
    qsoup = BeautifulSoup(query_response.text, 'html5lib')
    trains = qsoup.find_all('tr', 'trip-column')
    content = ''
    for train in trains:
        tds = train.find_all('td')
        name = tds[0].ul.li.a.text
        start_time = tds[1].text
        arrive_time = tds[2].text
        spend_time = tds[3].text
        content += f'車種:{name},出發時間:{start_time},抵達時間:{arrive_time},搭乘時間:{spend_time}\n'
    return content


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-LINE-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global data
    message = event.message.text
    if message == '如何使用':
        content = '輸入起訖站跟時間區間 範例:查詢桃園到臺中九點到十點發車的車次請輸入 桃園 臺中 09:00 10:00'
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=content))
        return
    else:
        data = message.split()
        print(data)
        content = getTrip()
        print(content)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=content))
        return


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

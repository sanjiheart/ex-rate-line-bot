from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerMessage, StickerSendMessage,
    ImageMessage, VideoMessage, AudioMessage, LocationMessage
)

import requests

app = Flask(__name__)

line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')
# user options
user_options = ["bank", "ccy", "help"]
# struct: {bank_code: bank_name}
bank_options = {"004": "台灣銀行", "017": "兆豐商銀", "812": "台新銀行", "012": "台北富邦", "807": "永豐銀行"}
# struct: {currency_abbreviation: currency_name}
ccy_options = {"JPY": "日圓", "USD": "美金", "CNY": "人民幣", "AUD": "澳幣"} 
# struct: {user_id: {bank: bank_name, currency: currency_abbreviation}}
user_preferences = {}

@app.route("/", methods=['GET'])
def hello():
    return "ex-rate-line-bot is working:-P";

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if not handle_swear_word(event.source.user_id, event.message.text):
        if event.source.user_id not in user_preferences:
            user_preferences[event.source.user_id] = {"bank": "台新銀行", "ccy": "JPY"}
        # split to option and option value
        user_input = event.message.text.split(" ")
        if user_input[0] not in user_options:
            ex_rate, last_updated = get_ex_rate(
                user_preferences[event.source.user_id].get("bank"),
                user_preferences[event.source.user_id].get("ccy"))
            reply_message = "### {bank_name} {ccy_abbre} ###\n即期匯率：{ex_rate}\n最後更新：{last_updated}".format(
                bank_name=user_preferences[event.source.user_id].get("bank"), 
                ccy_abbre=user_preferences[event.source.user_id].get("ccy"), 
                ex_rate=ex_rate, 
                last_updated=last_updated)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_message))
        else:
            if user_input[0] == "bank":
                user_preferences[event.source.user_id]["bank"] = bank_options.get(user_input[1], "台新銀行")
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="預設銀行已變更為{}".format(user_preferences[event.source.user_id]["bank"])))
            elif user_input[0] == "ccy":
                user_preferences[event.source.user_id]["ccy"] = user_input[1] if user_input[1] in ccy_options else "JPY"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="預設外幣已變更為{}".format(user_preferences[event.source.user_id]["ccy"])))
            else:
                bank_options_repr = ""
                for code in sorted(bank_options):
                    bank_options_repr += "{name} {code}\n".format(name=bank_options[code], code=code)
                ccy_options_repr = ""
                for abbre in sorted(ccy_options):
                    ccy_options_repr += "{name} {abbre}\n".format(name=ccy_options[abbre], abbre=abbre)
                reply_message = """輸入【help】顯示所有選項
輸入【bank 銀行代碼】變更預設銀行
輸入【ccy 外幣縮寫】變更預設外幣
其餘任何輸入皆顯示目前匯率

### 支援銀行選項 ###
{bank_options_repr}範例：bank 004

### 支援外幣選項 ###
{ccy_options_repr}範例：ccy USD""".format(
                    bank_options_repr=bank_options_repr,
                    ccy_options_repr=ccy_options_repr
                )
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_message))

def handle_swear_word(user_id, swear_word):
    if swear_word == "幹":
        reply_text_and_sticker(user_id, "幹屁幹？硍！", 52114135)
    elif swear_word == "嫩":
        reply_text_and_sticker(user_id, "你才嫩！你全家都嫩！", 52114135)
    elif swear_word == "靠":
        reply_text_and_sticker(user_id, "無薪還得挨罵，還不能罷工QQ", 52114126)
    elif "肏" in swear_word  or swear_word == "操":
        reply_text_and_sticker(user_id, "別這樣嘛～人家會害羞>///<", 52114132)
    else:
        return False
    return True

@handler.add(MessageEvent, message=(StickerMessage, ImageMessage, VideoMessage, AudioMessage, LocationMessage))
def handle_other_messages(event):
    reply_text_and_sticker(event.source.user_id, "需要協助請輸入【help】哦～", 52114118)

# ref: https://developers.line.biz/media/messaging-api/sticker_list.pdf
def reply_text_and_sticker(user_id, text, sticker_id):
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=text))
    line_bot_api.push_message(
        user_id,
        StickerSendMessage(package_id=11539, sticker_id=sticker_id))

def get_ex_rate(bank_name, ccy_abbre):
    api_uri = "https://tw.rter.info/json.php?t=currency&q=check&iso={ccy_abbre}".format(ccy_abbre=ccy_abbre)
    json_resp = requests.get(api_uri).json()
    for details in json_resp['data']:
        if bank_name in details[0]:
            return details[2], details[3]

if __name__ == "__main__":
    app.run()
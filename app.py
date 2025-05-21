from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

user_states = {}

QUESTIONS = [
    "こんにちは！今日は夫との会話ワークを一緒にやってみましょう。まずは、最近気になっている出来事について教えてください。",
    "そのとき、具体的にどんな状況でしたか？（時間・場所・相手の言動など）",
    "そのとき、自分はどう感じましたか？どんな感情がありましたか？",
    "体にはどんな反応がありましたか？（例えば、緊張した、胸が苦しかったなど）",
    "それを『私メッセージ』で伝えるとどうなりそうか、一緒に考えてみましょう。以下のテンプレートに当てはめてみてください。\n「あなたが ◯◯ しているとき、私は ◯◯ と感じました。だから、◯◯ してくれると嬉しいです」",
    "最後に、相手への感謝や思いやりの言葉を添えてみるのも効果的です。何か伝えたいことはありますか？",
    "会話を始める前に、以下の点をチェックしてみましょう：\n- 話すタイミングは落ち着いている？\n- 感情的になりすぎていない？\n- 責める言い方になっていない？\n- 『変わってほしい』ではなく『つながりたい』気持ちを伝えている？\n\n以上を確認できたら「完了」と送ってください。"
]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    if user_id not in user_states:
        user_states[user_id] = {'step': 0, 'answers': []}
    state = user_states[user_id]
    step = state['step']
    user_text = event.message.text.strip()
    if step < len(QUESTIONS):
        if step == 0:
            reply_text = QUESTIONS[step]
            state['step'] += 1
        else:
            state['answers'].append(user_text)
            if step == len(QUESTIONS) - 1:
                if user_text == "完了":
                    reply_text = "お疲れさまでした！またいつでも話したくなったら声をかけてくださいね。"
                    user_states[user_id] = {'step': 0, 'answers': []}
                else:
                    reply_text = "「完了」と入力するとワークが終了します。引き続きチェックしてくださいね。"
            else:
                reply_text = QUESTIONS[step]
                state['step'] += 1
    else:
        reply_text = "何か聞きたいことがあれば教えてください。最初からやる場合は「開始」と送ってください。"
        if user_text == "開始":
            user_states[user_id] = {'step': 0, 'answers': []}
            reply_text = QUESTIONS[0]
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

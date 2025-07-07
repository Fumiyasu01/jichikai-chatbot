import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = Flask(__name__)

# 環境変数から設定を読み込み（本番用）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# PDFの内容（後で実際の内容に置き換え）
pdf_content = """
ここに実際のPDFマニュアルの内容を貼り付けてください
"""

# チャットボットの応答機能
def get_chatbot_response(user_message):
    try:
        system_prompt = f"""
あなたは自治会の住民サポートチャットボットです。
以下の自治会マニュアルの内容に基づいて、住民の質問に親切に回答してください。

【自治会マニュアル】
{pdf_content}

回答の際は：
1. マニュアルの内容に基づいて回答
2. 分からない場合は「マニュアルに記載がないため、自治会長に直接お問い合わせください」と回答
3. 丁寧で分かりやすい言葉で回答
"""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"申し訳ございません。システムエラーが発生しました。"

# Webhook処理
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
    user_message = event.message.text
    bot_response = get_chatbot_response(user_message)
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=bot_response)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

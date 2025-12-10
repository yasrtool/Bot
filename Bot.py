import os
import logging
import asyncio
from flask import Flask
from threading import Thread
import google.generativeai as genai
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- إعدادات البوت ---

# المتغيرات البيئية (سنقوم بضبطها في موقع الاستضافة لاحقاً للحماية)
TELEGRAM_TOKEN = os.getenv("8320355728:AAGYY2wEInbnII_67P7DaZGDVwgnrHo43j0")
GEMINI_API_KEY = os.getenv("AIzaSyBIu7JSvKoNCkfzb8Yra_9k19osr-cAOzo")

# الآيدي المسموح له فقط (الآيدي الخاص بك)
ALLOWED_USER_ID = 7692968376

# إعداد السجل (Logging) لمعرفة الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- إعداد Gemini AI ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    # نستخدم موديل gemini-1.5-flash لأنه سريع وممتاز للمحادثات
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Gemini: {e}")

# --- دوال البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ عذراً، هذا البوت خاص ولا يمكنك استخدامه.")
        return
    
    await update.message.reply_text("👋 أهلاً بك! أنا جاهز للعمل. أنا مرتبط بـ Gemini AI مباشرة.")

async def chat_with_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # 1. التحقق من المستخدم (الحماية)
    if user_id != ALLOWED_USER_ID:
        await update.message.reply_text("⛔ عذراً، هذا البوت خاص.")
        return

    # إرسال رسالة "جاري الكتابة..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # 2. إرسال النص إلى Gemini
        response = model.generate_content(user_text)
        reply_text = response.text

        # 3. إرسال الرد إلى تلجرام
        # (نقوم بتقسيم الرسالة إذا كانت طويلة جداً لأن تلجرام يقبل 4096 حرف فقط)
        if len(reply_text) > 4096:
            for x in range(0, len(reply_text), 4096):
                await update.message.reply_text(reply_text[x:x+4096], parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}")

# --- خادم ويب بسيط لإبقاء البوت يعمل (Keep-Alive) ---
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=7860)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- التشغيل الرئيسي ---
if __name__ == '__main__':
    # تشغيل خادم الويب في الخلفية
    keep_alive()
    
    # تشغيل البوت
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN is missing!")
    else:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        gemini_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), chat_with_gemini)
        
        application.add_handler(start_handler)
        application.add_handler(gemini_handler)
        
        print("Bot is running...")
        application.run_polling()

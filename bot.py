#!/usr/bin/env python3
"""
ПРОСТОЙ Telegram бот для генерации сертификатов
Запускается на твоем компьютере!
"""

import io
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ================ НАСТРОЙКИ ================
# ВПИШИ СЮДА СВОЙ ТОКЕН от @BotFather
BOT_TOKEN = "ТВОЙ_ТОКЕН_ЗДЕСЬ"  # <-- ЗАМЕНИ ЭТУ СТРОКУ!

# Координаты (из твоего script.js)
POS = {
    "amount": {"x": 504, "y": 233},
    "name": {"x": 52, "y": 347},
    "congrats": {"x": 52, "y": 441},
    "code": {"x": 52, "y": 671}
}

# ================ СОСТОЯНИЯ ================
NAME, AMOUNT, CODE, CONGRATS = range(4)

# ================ ГЕНЕРАЦИЯ PDF ================
def make_pdf(name, code, congrats="", amount=""):
    """Создает PDF сертификат"""
    try:
        # 1. Открываем шаблон
        template = PdfReader("assets/sert.pdf")
        
        # 2. Создаем новый PDF
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        
        # 3. Добавляем текст
        
        # Имя (белое) - на позицию amount
        can.setFillColorRGB(1, 1, 1)  # белый
        can.setFont("Helvetica-Bold", 36)
        can.drawString(POS["amount"]["x"], 842 - POS["amount"]["y"], name)
        
        # Сумма (черная) - выше имени
        if amount:
            can.setFillColorRGB(0, 0, 0)  # черный
            can.setFont("Helvetica-Bold", 32)
            can.drawString(POS["name"]["x"], 842 - (POS["name"]["y"] - 50), amount)
        
        # Поздравление (черное) - на позицию name
        if congrats:
            can.setFillColorRGB(0, 0, 0)
            can.setFont("Helvetica", 18)
            # Разбиваем на строки
            words = congrats.split()
            lines = []
            line = ""
            for word in words:
                if len(line + " " + word) < 50:
                    line += " " + word if line else word
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)
            
            # Рисуем строки
            y = 842 - POS["name"]["y"]
            for i, text_line in enumerate(lines):
                can.drawString(POS["name"]["x"], y - (i * 25), text_line)
        
        # Код (черный) - на позицию congrats
        can.setFillColorRGB(0, 0, 0)
        can.setFont("Helvetica-Bold", 24)
        can.drawString(POS["code"]["x"], 842 - POS["congrats"]["y"], code)
        
        can.save()
        
        # 4. Объединяем с шаблоном
        packet.seek(0)
        new_pdf = PdfReader(packet)
        output = PdfWriter()
        
        page = template.pages[0]
        page.merge_page(new_pdf.pages[0])
        output.add_page(page)
        
        # 5. Сохраняем в байты
        result = io.BytesIO()
        output.write(result)
        result.seek(0)
        return result
        
    except Exception as e:
        print(f"Ошибка создания PDF: {e}")
        return None

# ================ КОМАНДЫ БОТА ================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    await update.message.reply_text(
        "Привет! Я создаю PDF сертификаты.\n"
        "Напиши /new чтобы начать."
    )

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /new"""
    await update.message.reply_text("Введи имя получателя:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем имя"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Введи сумму подарка (или /skip):")
    return AMOUNT

async def skip_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропускаем сумму"""
    context.user_data['amount'] = ""
    await update.message.reply_text("Введи код сертификата:")
    return CODE

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем сумму"""
    context.user_data['amount'] = update.message.text
    await update.message.reply_text("Введи код сертификата:")
    return CODE

async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем код"""
    context.user_data['code'] = update.message.text
    await update.message.reply_text("Введи поздравление (или /skip):")
    return CONGRATS

async def skip_congrats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропускаем поздравление"""
    context.user_data['congrats'] = "Поздравляем!"
    return await generate(update, context)

async def get_congrats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем поздравление"""
    context.user_data['congrats'] = update.message.text
    return await generate(update, context)

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерируем и отправляем PDF"""
    data = context.user_data
    
    await update.message.reply_text("⏳ Создаю сертификат...")
    
    # Создаем PDF
    pdf = make_pdf(
        name=data.get('name', ''),
        code=data.get('code', ''),
        congrats=data.get('congrats', ''),
        amount=data.get('amount', '')
    )
    
    if pdf:
        # Отправляем файл
        await update.message.reply_document(
            document=pdf,
            filename=f"Сертификат_{data['name']}.pdf",
            caption=f"✅ Готово! Для: {data['name']}"
        )
    else:
        await update.message.reply_text("❌ Ошибка создания PDF")
    
    # Очищаем данные
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена"""
    context.user_data.clear()
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

# ================ ЗАПУСК БОТА ================
def main():
    """Запускаем бота"""
    # Проверяем токен
    if BOT_TOKEN == "ТВОЙ_ТОКЕН_ЗДЕСЬ":
        print("❌ ОШИБКА: Не указан токен бота!")
        print("1. Получи токен у @BotFather в Telegram")
        print("2. Впиши его в файл bot.py (строка 15)")
        print("3. Запусти бота снова")
        return
    
    # Проверяем шаблон
    if not os.path.exists("assets/sert.pdf"):
        print("⚠️  ВНИМАНИЕ: Файл шаблона не найден!")
        print("Создай папку 'assets' и положи туда sert.pdf")
        os.makedirs("assets", exist_ok=True)
    
    # Создаем бота
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Настройка диалога
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount),
                CommandHandler('skip', skip_amount)
            ],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_code)],
            CONGRATS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_congrats),
                CommandHandler('skip', skip_congrats)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    
    # Запускаем
    print("🤖 Бот запускается...")
    print("📁 Проверь папку 'assets' - там должен быть sert.pdf")
    print("✅ Открой Telegram и напиши боту /start")
    print("🛑 Чтобы остановить бота: Ctrl+C")
    
    app.run_polling()

if __name__ == "__main__":
    main()
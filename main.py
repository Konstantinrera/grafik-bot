import logging
import datetime
import gspread
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from oauth2client.service_account import ServiceAccountCredentials

# === Настройки ===
TELEGRAM_TOKEN = "8483629759:AAHn4v5OzflQQ57qV1gblW4XMa1uACzPAFI"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/14j3toMy4boNzDxA1eCe2fuxpsrFN8PraM2oHBgCowy8/edit?usp=sharing"

# === Авторизация Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

# === Telegram Bot ===
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def send_schedule(message: types.Message):
    today = datetime.datetime.now().strftime("%d.%m")  # например 26.07
    date_row = sheet.row_values(2)  # вторая строка таблицы (даты)
    col_index = None

    # Поиск колонки по сегодняшней дате
    for i, val in enumerate(date_row):
        if today in val:
            col_index = i
            break

    if col_index is None:
        await message.answer("❌ Дата не знайдена в таблиці")
        return

    data = sheet.get_all_values()
    response = f"📅 Сьогодні — {today}\n\n"

    for row in data[3:]:  # пропускаем заголовки
        if len(row) <= col_index:
            continue

        shift_type = row[0].strip().lower()
        name = row[1].strip()
        cell = row[col_index].strip().lower()

        if not name:
            continue

        # Проверка на статус
        if "лік" in cell:
            response += f" {name} — лікарняний🌡️\n"
        elif "тренінг" in cell:
            response += f" {name} — тренінг\n"
        elif "відпустка" in cell or "власний" in cell:
            response += f" {name} — відпустка☀️\n"
        elif "інше" in cell:
            response += f" {name} — інше\n"
        elif "вих" in cell or "немає" in cell:
            response += f" {name} — вихідний\n"
        else:
            try:
                # Нормализация времени
                clean_cell = cell.replace("-", ":").strip()
                start = datetime.datetime.strptime(clean_cell, "%H:%M")

                # Определение длительности смены
                hours = 4
                if "4" in shift_type:
                    hours = 4
                    display_hours = "4"
                if "6" in shift_type:
                    hours = 6
                    display_hours = "6"
                elif "8" in shift_type:
                    hours = 9
                    display_hours = "8"

                end = (start + datetime.timedelta(hours=hours)).strftime("%H:%M")
                response += f" ✅[{display_hours} год] {name} — з {start.strftime('%H:%M')} до {end}\n"
            except:
                response += f" {name} — ❗️невідомий формат «{cell}»\n"

    await message.answer(response)

# === Запуск бота ===
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
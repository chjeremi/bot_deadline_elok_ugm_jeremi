import os
import requests
from datetime import datetime, timezone
from icalendar import Calendar

# Ambil credential dari Environment Variables
ICAL_URL = os.environ.get("ELOK_ICAL_URL")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    return response.ok

def main():
    if not all([ICAL_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Error: Missing environment variables.")
        return

    # Download file iCal dari eLOK
    response = requests.get(ICAL_URL)
    if response.status_code != 200:
        print("Gagal mengambil data dari eLOK.")
        return

    cal = Calendar.from_ical(response.content)
    now = datetime.now(timezone.utc)
    
    upcoming_tasks = []

    for component in cal.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary'))
            dtend = component.get('dtend') or component.get('dtstart')
            
            if not dtend:
                continue

            event_time = dtend.dt
            
            # Konversi jika event_time berupa date biasa tanpa jam/timezone
            if not isinstance(event_time, datetime):
                event_time = datetime.combine(event_time, datetime.min.time()).replace(tzinfo=timezone.utc)
            elif event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)

            # Hitung selisih waktu menuju deadline
            diff = event_time - now
            days_left = diff.total_seconds() / 86400

            # Cek tugas yang tenggatnya antara 0 sampai 5 hari lagi
            if 0 <= days_left <= 60:
                # Konversi waktu ke jam lokal (WIB = UTC+7)
                local_time = datetime.fromtimestamp(event_time.timestamp(), tz=timezone.utc)
                formatted_time = event_time.strftime("%d %b %Y, %H:%M UTC")
                
                upcoming_tasks.append({
                    "title": summary,
                    "deadline": formatted_time,
                    "days_left": int(days_left)
                })

    if upcoming_tasks:
        msg = "🚨 *PENGINGAT TUGAS ELOK UGM* 🚨\n\n"
        for task in upcoming_tasks:
            msg += f"📌 *{task['title']}*\n"
            msg += f"⏳ Deadline: `{task['deadline']}` ({task['days_left']} hari lagi)\n\n"
        
        send_telegram_message(msg)
        print("Notifikasi berhasil dikirim ke Telegram.")
    else:
        print("Tidak ada tugas mendekati deadline dalam 5 hari ke depan.")

if __name__ == "__main__":
    main()

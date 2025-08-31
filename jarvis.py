import asyncio
import sqlite3
from datetime import datetime
import logging
from contextlib import contextmanager
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatMemberUpdated,
    FSInputFile,
    ChatPermissions,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
import os
import re
import uuid
import json
import random
import time
import hashlib
import base64
from typing import Optional, List, Dict, Any
import requests  # Qo'shimcha: ob-havo va news uchun
import feedparser  # Qo'shimcha: RSS news uchun

# ================= CONFIG =================
BOT_TOKEN = "6335576043:AAG9s9vmorxeHakm-uZ5-Jb3SRZGqRX2e7I"  # Replace with your actual bot token
SECRET_CHANNEL = -2315371580 # Replace with your secret channel ID
GROUP_ID = -2112963124      # Replace with your group ID
GROUP_LINK = "https://t.me/jasurbek_jolanboyev"  # Group link
CHANNEL_LINK = "https://t.me/vscoderr"  # Channel link
DB_PATH = "users.db"
ADMIN_USERNAME = "serinaqu"
LOG_LEVEL = logging.DEBUG
MAX_AGE = 100
MIN_AGE = 13
PHONE_REGEX = r"^\+998\d{9}$"
USERNAME_REGEX = r"^@\w+$|^\d+$"
MOD_CATEGORIES = ["Games", "Utilities", "Entertainment", "Productivity"]
EXPORT_FORMATS = ["TXT", "JSON", "CSV"]
BROADCAST_DELAY = 0.05  # Delay between broadcasts to avoid rate limits
RATE_LIMIT_RETRY = 5  # Max retries for rate limits
SESSION_TIMEOUT = 3600  # Session timeout in seconds
OPENWEATHER_API_KEY = "your_openweather_api_key_here"  # Qo'shimcha: OpenWeatherMap API key (o'zingiz ro'yxatdan o'ting: https://openweathermap.org/api)

# ================= LANGUAGE SUPPORT =================
LANGUAGES = {
    'uz': {
        'welcome': "👋 Salom!\n\nBu bot guruh va kanalga qo‘shilishdan oldin sizni xavfsizlik tekshiruvidan o‘tkazadi.\n\nSizdan quyidagilar so‘raladi:\n1) 👤 To‘liq ism va familiya (kamida 2 so‘z, masalan: Aliyev Valijon)\n2) 📱 Telefon raqam (faqat 'Telefon raqamini ulashish' tugmasi orqali)\n3) 🎂 Yosh (13–100 yosh oralig‘ida raqam)\n4) 🆔 Telegram username yoki ID (@username yoki raqam, masalan: @Aliyev123 yoki 123456789)\n\n✅ Ma‘lumotlaringiz maxfiy saqlanadi va faqat adminlar ko‘rishi mumkin.\n🔒 Davom etish maxfiylik siyosatiga rozilik bildirish demakdir.",
        'private_only': "Iltimos, bot bilan shaxsiy (private) chatda /start buyrug‘ini yuboring.",
        'verification_needed': "👋 Salom! Guruhda xabar yozish uchun qisqa verifikatsiyadan o‘tishingiz kerak.\n\nIltimos, bot bilan shaxsiy chatda ma‘lumotlarni yuboring va guruh/kanalda a’zo bo‘ling.\nAgar botga shaxsiy xabar yozolmasangiz, guruh adminlari bilan bog‘laning (@serinaqu).",
        'full_name_prompt': "👤 To‘liq ism va familiyangizni yuboring (kamida 2 so‘z, masalan: Aliyev Valijon):",
        'full_name_invalid': "❌ Iltimos, to‘liq ism va familiya kiriting (kamida 2 so‘z, masalan: Aliyev Valijon).",
        'phone_prompt': "📱 Telefon raqamingizni faqat quyidagi tugma orqali yuboring:",
        'phone_invalid': "❌ Telefon raqami noto‘g‘ri. Iltimos, faqat 'Telefon raqamini ulashish' tugmasi orqali raqamni yuboring.",
        'age_prompt': "🎂 Yoshngizni raqam bilan kiriting (13–100 yosh oralig‘ida):",
        'age_invalid': "❌ Yosh 13 dan kichik yoki 100 dan katta bo‘lmasligi kerak. Iltimos, to‘g‘ri yosh kiriting.",
        'username_prompt': "🆔 Telegram username yoki ID raqamingizni yuboring (masalan: @Aliyev123 yoki 123456789):",
        'username_invalid': "❌ Username yoki ID noto‘g‘ri. Iltimos, @ bilan boshlanadigan username (masalan: @Aliyev123) yoki raqamli ID kiriting.",
        'verification_complete': "✅ Tabriklaymiz! Siz muvaffaqiyatli tekshiruvdan o‘tdingiz.\n\nEndi guruhda xabar yozish va mod dasturlarni ko‘rish uchun quyidagi guruh va kanalga a’zo bo‘ling:",
        'error': "❌ Xatolik yuz berdi: {}. Iltimos, qayta urinib ko‘ring yoki admin bilan bog‘laning (@serinaqu).",
        'bot_blocked': "❌ Bot bloklangan. Iltimos, botni blokdan chiqaring va qayta urinib ko‘ring.",
        'group_notice': "🔒 Kechirasiz, {user}, bu guruhda yozish uchun avval @Vscoder_bot orqali ro‘yxatdan o‘tishingiz va guruh/kanalda a’zo bo‘lishingiz kerak.",
        'stats': "📊 Statistikalar:\nJami foydalanuvchilar: {}\nTasdiqlangan foydalanuvchilar: {}\nJami modlar: {}\nSo‘nggi 10 foydalanuvchi:\n{}\nAktiv sessiyalar: {}\nBanned users: {}",
        'broadcast_prompt': "📢 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        'broadcast_success': "✅ Xabar {} foydalanuvchiga muvaffaqiyatli yuborildi!",
        'broadcast_failed': "❌ Xabar yuborishda xato: {}",
        'no_users': "❌ Foydalanuvchilar topilmadi.",
        'start_verify': "📤 Boshlash — ma‘lumot yuborish",
        'admin_panel': "🔐 Admin Panel\nIltimos, kerakli amalni tanlang:",
        'admin_stats': "📊 Statistikalar",
        'admin_broadcast': "📢 Xabar yuborish",
        'admin_export': "📄 Eksport",
        'admin_ban_user': "🚫 Foydalanuvchini ban qilish",
        'admin_unban_user': "✅ Ban olish",
        'admin_view_logs': "📜 Loglarni ko'rish",
        'admin_manage_mods': "🛠 Modlarni boshqarish",
        'export_prompt': "📄 Ma'lumotlar bazasi formatini tanlang:",
        'export_txt': "TXT",
        'export_json': "JSON",
        'export_csv': "CSV",
        'export_success': "✅ Ma'lumotlar bazasi muvaffaqiyatli eksport qilindi!",
        'export_failed': "❌ Eksport qilishda xato yuz berdi: {}",
        'not_in_group_or_channel': "❌ Siz guruh yoki kanalda a’zo emassiz. Iltimos, quyidagi havolalar orqali a’zo bo‘ling va qayta urinib ko‘ring:",
        'mods_menu': "📦 Mod Dasturlari\nQuyidagi modlardan birini tanlang:",
        'no_mods': "❌ Hozircha mod dasturlari mavjud emas.",
        'admin_add_mod': "➕ Mod qo'shish",
        'admin_remove_mod': "🗑 Mod o'chirish",
        'admin_list_mods': "📋 Modlar ro'yxati",
        'admin_edit_mod': "✏ Modni tahrirlash",
        'add_mod_prompt': "📦 Yangi mod qo'shish uchun quyidagi ma'lumotlarni kiriting:\n1) Mod nomi (masalan: Mod1)\n2) Tavsif\n3) Fayl havolasi (Telegram fayl havolasi yoki tashqi URL)\n4) Kategoriya (masalan: Games)\n\nMa'lumotlarni quyidagi formatda yuboring:\nMod nomi: <nom>\nTavsif: <tavsif>\nHavola: <URL>\nKategoriya: <kategoriya>",
        'add_mod_success': "✅ Mod muvaffaqiyatli qo'shildi: {}",
        'add_mod_failed': "❌ Mod qo'shishda xato: {}",
        'remove_mod_prompt': "🗑 O'chiriladigan mod nomini yuboring:",
        'remove_mod_success': "✅ Mod muvaffaqiyatli o'chirildi: {}",
        'remove_mod_failed': "❌ Mod o'chirishda xato: {}",
        'mod_list': "📋 Modlar ro'yxati:\n{}",
        'mod_list_empty': "❌ Modlar ro'yxati bo'sh.",
        'invalid_mod_format': "❌ Noto'g'ri format. Iltimos, quyidagi formatda yuboring:\nMod nomi: <nom>\nTavsif: <tavsif>\nHavola: <URL>\nKategoriya: <kategoriya>",
        'ban_prompt': "🚫 Ban qilmoqchi bo'lgan foydalanuvchi ID ni kiriting:",
        'ban_success': "✅ Foydalanuvchi {} muvaffaqiyatli ban qilindi!",
        'ban_failed': "❌ Ban qilishda xato: {}",
        'unban_prompt': "✅ Ban olmoqchi bo'lgan foydalanuvchi ID ni kiriting:",
        'unban_success': "✅ Foydalanuvchi {} ban dan chiqarildi!",
        'unban_failed': "❌ Ban olishda xato: {}",
        'logs_prompt': "📜 Log faylini yuborish uchun 'Loglarni yuborish' tugmasini bosing:",
        'logs_send': "Loglarni yuborish",
        'logs_success': "✅ Loglar muvaffaqiyatli yuborildi!",
        'logs_failed': "❌ Log yuborishda xato: {}",
        'edit_mod_prompt': "✏ Tahrirlamoqchi bo'lgan mod nomini va yangi ma'lumotlarni kiriting:\nFormat: Mod nomi: <eski nom>\nYangi nomi: <yangi nom>\nTavsif: <yangi tavsif>\nHavola: <yangi URL>\nKategoriya: <yangi kategoriya>",
        'edit_mod_success': "✅ Mod muvaffaqiyatli tahrirlandi: {}",
        'edit_mod_failed': "❌ Mod tahrirlashda xato: {}",
        'profile_prompt': "👤 Profilingizni ko'rish uchun 'Profilni ko'rish' tugmasini bosing:",
        'profile_view': "Profilni ko'rish",
        'profile': "👤 Profilingiz:\nIsm: {}\nTelefon: {}\nYosh: {}\nUsername: {}\nRo'yxatdan o'tgan sana: {}\nStatus: {}",
        'help': "❓ Yordam:\n/start - Boshlash\n/mods - Modlarni ko'rish\n/profile - Profilingizni ko'rish\n/help - Ushbu yordam\n/weather - Ob-havo\n/calculator - Hisob-kitob\n/news - Yangiliklar",
        'feedback_prompt': "📝 Fikringizni yuboring:",
        'feedback_success': "✅ Fikringiz qabul qilindi!",
        'admin_view_feedback': "📝 Fikrlarni ko'rish",
        'no_feedback': "❌ Hozircha fikrlar mavjud emas.",
        'feedback_list': "📝 Fikrlar ro'yxati:\n{}",
        'category_prompt': "📂 Kategoriyani tanlang:",
        'search_mods': "🔍 Modlarni qidirish",
        'search_prompt': "🔍 Qidiruv so'zini kiriting:",
        'search_results': "🔍 Natijalar:\n{}",
        'no_results': "❌ Natijalar topilmadi.",
        'rate_mod': "⭐ Modni baholash",
        'rate_prompt': "⭐ Mod nomini va bahoni (1-5) kiriting:\nFormat: Mod nomi: <nom>\nBaho: <1-5>",
        'rate_success': "✅ Baho qo'shildi!",
        'rate_failed': "❌ Baho qo'shishda xato: {}",
        'mod_ratings': "⭐ Mod baholari: {}",
        'admin_backup_db': "💾 DB backup",
        'backup_success': "✅ Backup muvaffaqiyatli yaratildi!",
        'backup_failed': "❌ Backupda xato: {}",
        'admin_restore_db': "🔄 DB restore",
        'restore_prompt': "🔄 Restore uchun fayl yuboring.",
        'restore_success': "✅ DB restore qilindi!",
        'restore_failed': "❌ Restoreda xato: {}",
        'session_expired': "⏰ Sessiya muddati tugadi. Qayta boshlang.",
        'welcome_back': "👋 Qaytganingiz bilan! Verifikatsiyangiz hali ham amal qiladi.",
        'update_profile': "🔄 Profilingizni yangilash",
        'update_prompt': "🔄 Yangilamoqchi bo'lgan maydonni tanlang:",
        'update_full_name': "👤 Ismni yangilash",
        'update_phone': "📱 Telefonni yangilash",
        'update_age': "🎂 Yoshni yangilash",
        'update_username': "🆔 Usernameni yangilash",
        'update_success': "✅ Profil yangilandi!",
        'update_failed': "❌ Yangilashda xato: {}",
        'admin_user_search': "🔍 Foydalanuvchini qidirish",
        'search_user_prompt': "🔍 Qidiruv: ID yoki username kiriting:",
        'user_info': "👤 Foydalanuvchi ma'lumotlari:\n{}",
        'no_user_found': "❌ Foydalanuvchi topilmadi.",
        'admin_announce': "📣 E'lon yuborish",
        'announce_prompt': "📣 E'lon matnini kiriting:",
        'announce_success': "✅ E'lon yuborildi!",
        'poll_create': "📊 So'rovnoma yaratish",
        'poll_prompt': "📊 So'rovnoma savolini va variantlarni kiriting:\nFormat: Savol: <savol>\nVariant1\nVariant2\n...",
        'poll_success': "✅ So'rovnoma yaratildi va yuborildi!",
        'poll_failed': "❌ So'rovnoma yaratishda xato: {}",
        'event_schedule': "🗓 Tadbir rejalashtirish",
        'event_prompt': "🗓 Tadbir nomi, vaqti va tavsifini kiriting:",
        'event_success': "✅ Tadbir rejalashtirildi!",
        'event_list': "🗓 Tadbirlar ro'yxati:\n{}",
        'no_events': "❌ Tadbirlar mavjud emas.",
        'reminder_set': "⏰ Eslatma o'rnatish",
        'reminder_prompt': "⏰ Eslatma matni va vaqtini kiriting (sekundlarda):",
        'reminder_success': "✅ Eslatma o'rnatildi!",
        'captcha_prompt': "🤖 Captcha: {} = ? (Raqam bilan javob bering)",
        'captcha_invalid': "❌ Noto'g'ri captcha. Qayta urining.",
        'captcha_success': "✅ Captcha to'g'ri!",
        'multi_lang_support': "🌍 Tilni o'zgartirish",
        'lang_uz': "🇺🇿 O'zbekcha",
        'lang_ru': "🇷🇺 Русский",
        'lang_en': "🇬🇧 English",
        # Qo'shimcha so'zlar uchun
        'weather_prompt': "🏙 Shahar nomini kiriting (masalan: Toshkent):",
        'weather_info': "🏙 {} shahridagi ob-havo:\nHarorat: {}°C\nHolati: {}\nNamlik: {}%",
        'weather_error': "❌ Ob-havo ma'lumoti topilmadi. Shaharni to'g'ri kiriting.",
        'calculator_prompt': "Hisobni kiriting (masalan: 2+3*4):",
        'calculator_result': "Natija: {}",
        'calculator_error': "❌ Noto'g'ri hisob. Qayta urinib ko'ring.",
        'news_prompt': "So'nggi yangiliklar:",
        'news_error': "❌ Yangiliklar topilmadi.",
    },
    'ru': {
        # Russian translations
        'welcome': "👋 Привет!\n\nЭтот бот проверит вас на безопасность перед вступлением в группу и канал.\n\nОт вас потребуется:\n1) 👤 Полное имя и фамилия (минимум 2 слова, например: Алиев Валижон)\n2) 📱 Номер телефона (только через кнопку 'Поделиться номером телефона')\n3) 🎂 Возраст (число от 13 до 100)\n4) 🆔 Telegram username или ID (@username или число, например: @Aliyev123 или 123456789)\n\n✅ Ваши данные конфиденциальны и видимы только админам.\n🔒 Продолжение означает согласие с политикой конфиденциальности.",
        'private_only': "Пожалуйста, отправьте команду /start в личном чате с ботом.",
        'verification_needed': "👋 Привет! Для написания сообщений в группе вам нужно пройти короткую верификацию.\n\nПожалуйста, отправьте данные в личном чате с ботом и вступите в группу/канал.\nЕсли вы не можете написать боту, свяжитесь с админами группы (@serinaqu).",
        'full_name_prompt': "👤 Введите полное имя и фамилию (минимум 2 слова, например: Алиев Валижон):",
        'full_name_invalid': "❌ Пожалуйста, введите полное имя и фамилию (минимум 2 слова, например: Алиев Валижон).",
        'phone_prompt': "📱 Отправьте номер телефона только через кнопку ниже:",
        'phone_invalid': "❌ Неверный номер телефона. Пожалуйста, используйте кнопку 'Поделиться номером телефона'.",
        'age_prompt': "🎂 Введите возраст числом (от 13 до 100):",
        'age_invalid': "❌ Возраст должен быть от 13 до 100. Пожалуйста, введите правильный возраст.",
        'username_prompt': "🆔 Введите Telegram username или ID (@username или число, например: @Aliyev123 или 123456789):",
        'username_invalid': "❌ Неверный username или ID. Пожалуйста, введите username начиная с @ (например: @Aliyev123) или числовой ID.",
        'verification_complete': "✅ Поздравляем! Вы успешно прошли проверку.\n\nТеперь вступите в группу и канал ниже, чтобы писать сообщения и просматривать моды:",
        'error': "❌ Произошла ошибка: {}. Пожалуйста, попробуйте снова или свяжитесь с админом (@serinaqu).",
        'bot_blocked': "❌ Бот заблокирован. Пожалуйста, разблокируйте бота и попробуйте снова.",
        'group_notice': "🔒 Извините, @{user}, для написания в этой группе вам нужно сначала зарегистрироваться через @YourBot и вступить в группу/канал.",
        'stats': "📊 Статистика:\nВсего пользователей: {}\nПодтвержденных пользователей: {}\nВсего модов: {}\nПоследние 10 пользователей:\n{}\nАктивные сессии: {}\nЗабаненные пользователи: {}",
        'broadcast_prompt': "📢 Введите сообщение для рассылки всем пользователям:",
        'broadcast_success': "✅ Сообщение успешно отправлено {} пользователям!",
        'broadcast_failed': "❌ Ошибка отправки сообщения: {}",
        'no_users': "❌ Пользователи не найдены.",
        'start_verify': "📤 Начать — отправить данные",
        'admin_panel': "🔐 Админ-панель\nПожалуйста, выберите действие:",
        'admin_stats': "📊 Статистика",
        'admin_broadcast': "📢 Рассылка сообщений",
        'admin_export': "📄 Экспорт",
        'admin_ban_user': "🚫 Забанить пользователя",
        'admin_unban_user': "✅ Разбанить",
        'admin_view_logs': "📜 Просмотр логов",
        'admin_manage_mods': "🛠 Управление модами",
        'export_prompt': "📄 Выберите формат базы данных:",
        'export_txt': "TXT",
        'export_json': "JSON",
        'export_csv': "CSV",
        'export_success': "✅ База данных успешно экспортирована!",
        'export_failed': "❌ Ошибка экспорта: {}",
        'not_in_group_or_channel': "❌ Вы не член группы или канала. Пожалуйста, вступите по ссылкам ниже и попробуйте снова:",
        'mods_menu': "📦 Моды\nВыберите один из модов ниже:",
        'no_mods': "❌ Модов пока нет.",
        'admin_add_mod': "➕ Добавить мод",
        'admin_remove_mod': "🗑 Удалить мод",
        'admin_list_mods': "📋 Список модов",
        'admin_edit_mod': "✏ Редактировать мод",
        'add_mod_prompt': "📦 Для добавления нового мода введите:\n1) Название мода (например: Mod1)\n2) Описание\n3) Ссылка на файл (Telegram или внешний URL)\n4) Категория (например: Games)\n\nОтправьте в формате:\nНазвание мода: <название>\nОписание: <описание>\nСсылка: <URL>\nКатегория: <категория>",
        'add_mod_success': "✅ Мод успешно добавлен: {}",
        'add_mod_failed': "❌ Ошибка добавления мода: {}",
        'remove_mod_prompt': "🗑 Введите название мода для удаления:",
        'remove_mod_success': "✅ Мод успешно удален: {}",
        'remove_mod_failed': "❌ Ошибка удаления мода: {}",
        'mod_list': "📋 Список модов:\n{}",
        'mod_list_empty': "❌ Список модов пуст.",
        'invalid_mod_format': "❌ Неправильный формат. Пожалуйста, отправьте в формате:\nНазвание мода: <название>\nОписание: <описание>\nСсылка: <URL>\nКатегория: <категория>",
        'ban_prompt': "🚫 Введите ID пользователя для бана:",
        'ban_success': "✅ Пользователь {} успешно забанен!",
        'ban_failed': "❌ Ошибка бана: {}",
        'unban_prompt': "✅ Введите ID пользователя для разбана:",
        'unban_success': "✅ Пользователь {} разбанен!",
        'unban_failed': "❌ Ошибка разбана: {}",
        'logs_prompt': "📜 Для отправки лог-файла нажмите кнопку 'Отправить логи':",
        'logs_send': "Отправить логи",
        'logs_success': "✅ Логи успешно отправлены!",
        'logs_failed': "❌ Ошибка отправки логов: {}",
        'edit_mod_prompt': "✏ Введите название мода и новые данные:\nФормат: Название мода: <старое название>\nНовое название: <новое название>\nОписание: <новое описание>\nСсылка: <новый URL>\nКатегория: <новая категория>",
        'edit_mod_success': "✅ Мод успешно отредактирован: {}",
        'edit_mod_failed': "❌ Ошибка редактирования мода: {}",
        'profile_prompt': "👤 Для просмотра профиля нажмите кнопку 'Просмотреть профиль':",
        'profile_view': "Просмотреть профиль",
        'profile': "👤 Ваш профиль:\nИмя: {}\nТелефон: {}\nВозраст: {}\nUsername: {}\nДата регистрации: {}\nСтатус: {}",
        'help': "❓ Помощь:\n/start - Начать\n/mods - Просмотреть моды\n/profile - Просмотреть профиль\n/help - Эта помощь\n/weather - Погода\n/calculator - Расчет\n/news - Новости",
        'feedback_prompt': "📝 Отправьте свой отзыв:",
        'feedback_success': "✅ Отзыв принят!",
        'admin_view_feedback': "📝 Просмотреть отзывы",
        'no_feedback': "❌ Отзывов пока нет.",
        'feedback_list': "📝 Список отзывов:\n{}",
        'category_prompt': "📂 Выберите категорию:",
        'search_mods': "🔍 Поиск модов",
        'search_prompt': "🔍 Введите поисковый запрос:",
        'search_results': "🔍 Результаты:\n{}",
        'no_results': "❌ Результатов не найдено.",
        'rate_mod': "⭐ Оценить мод",
        'rate_prompt': "⭐ Введите название мода и оценку (1-5):\nФормат: Название мода: <название>\nОценка: <1-5>",
        'rate_success': "✅ Оценка добавлена!",
        'rate_failed': "❌ Ошибка добавления оценки: {}",
        'mod_ratings': "⭐ Оценки мода: {}",
        'admin_backup_db': "💾 Бэкап БД",
        'backup_success': "✅ Бэкап успешно создан!",
        'backup_failed': "❌ Ошибка бэкапа: {}",
        'admin_restore_db': "🔄 Восстановление БД",
        'restore_prompt': "🔄 Отправьте файл для восстановления.",
        'restore_success': "✅ БД восстановлена!",
        'restore_failed': "❌ Ошибка восстановления: {}",
        'session_expired': "⏰ Сессия истекла. Начните заново.",
        'welcome_back': "👋 С возвращением! Ваша верификация все еще действительна.",
        'update_profile': "🔄 Обновить профиль",
        'update_prompt': "🔄 Выберите поле для обновления:",
        'update_full_name': "👤 Обновить имя",
        'update_phone': "📱 Обновить телефон",
        'update_age': "🎂 Обновить возраст",
        'update_username': "🆔 Обновить username",
        'update_success': "✅ Профиль обновлен!",
        'update_failed': "❌ Ошибка обновления: {}",
        'admin_user_search': "🔍 Поиск пользователя",
        'search_user_prompt': "🔍 Поиск: Введите ID или username:",
        'user_info': "👤 Информация о пользователе:\n{}",
        'no_user_found': "❌ Пользователь не найден.",
        'admin_announce': "📣 Отправить объявление",
        'announce_prompt': "📣 Введите текст объявления:",
        'announce_success': "✅ Объявление отправлено!",
        'poll_create': "📊 Создать опрос",
        'poll_prompt': "📊 Введите вопрос опроса и варианты:\nФормат: Вопрос: <вопрос>\nВариант1\nВариант2\n...",
        'poll_success': "✅ Опрос создан и отправлен!",
        'poll_failed': "❌ Ошибка создания опроса: {}",
        'event_schedule': "🗓 Запланировать событие",
        'event_prompt': "🗓 Введите название события, время и описание:",
        'event_success': "✅ Событие запланировано!",
        'event_list': "🗓 Список событий:\n{}",
        'no_events': "❌ Событий нет.",
        'reminder_set': "⏰ Установить напоминание",
        'reminder_prompt': "⏰ Введите текст напоминания и время (в секундах):",
        'reminder_success': "✅ Напоминание установлено!",
        'captcha_prompt': "🤖 Captcha: {} = ? (Ответьте числом)",
        'captcha_invalid': "❌ Неправильная captcha. Попробуйте снова.",
        'captcha_success': "✅ Captcha правильная!",
        'multi_lang_support': "🌍 Изменить язык",
        'lang_uz': "🇺🇿 O'zbekcha",
        'lang_ru': "🇷🇺 Русский",
        'lang_en': "🇬🇧 English",
        # Qo'shimcha so'zlar uchun
        'weather_prompt': "🏙 Введите название города (например: Ташкент):",
        'weather_info': "🏙 Погода в {}:\nТемпература: {}°C\nСостояние: {}\nВлажность: {}%",
        'weather_error': "❌ Погода не найдена. Введите город правильно.",
        'calculator_prompt': "Введите расчет (например: 2+3*4):",
        'calculator_result': "Результат: {}",
        'calculator_error': "❌ Неправильный расчет. Попробуйте снова.",
        'news_prompt': "Последние новости:",
        'news_error': "❌ Новости не найдены.",
    },
    'en': {
        # English translations
        'welcome': "👋 Hello!\n\nThis bot will verify you for security before joining the group and channel.\n\nYou will be asked for:\n1) 👤 Full name (at least 2 words, e.g., Aliyev Valijon)\n2) 📱 Phone number (only via 'Share Phone Number' button)\n3) 🎂 Age (number between 13-100)\n4) 🆔 Telegram username or ID (@username or number, e.g., @Aliyev123 or 123456789)\n\n✅ Your data is confidential and only visible to admins.\n🔒 Continuing means you agree to the privacy policy.",
        'private_only': "Please send /start in a private chat with the bot.",
        'verification_needed': "👋 Hello! To write messages in the group, you need to pass a short verification.\n\nPlease send data in private chat with the bot and join the group/channel.\nIf you can't message the bot, contact group admins (@serinaqu).",
        'full_name_prompt': "👤 Enter your full name (at least 2 words, e.g., Aliyev Valijon):",
        'full_name_invalid': "❌ Please enter full name (at least 2 words, e.g., Aliyev Valijon).",
        'phone_prompt': "📱 Send your phone number only via the button below:",
        'phone_invalid': "❌ Invalid phone number. Please use the 'Share Phone Number' button.",
        'age_prompt': "🎂 Enter your age as a number (13-100):",
        'age_invalid': "❌ Age must be between 13 and 100. Please enter a valid age.",
        'username_prompt': "🆔 Enter your Telegram username or ID (@username or number, e.g., @Aliyev123 or 123456789):",
        'username_invalid': "❌ Invalid username or ID. Please enter username starting with @ (e.g., @Aliyev123) or numeric ID.",
        'verification_complete': "✅ Congratulations! You have successfully passed verification.\n\nNow join the group and channel below to write messages and view mods:",
        'error': "❌ An error occurred: {}. Please try again or contact admin (@serinaqu).",
        'bot_blocked': "❌ Bot is blocked. Please unblock the bot and try again.",
        'group_notice': "🔒 Sorry, @{user}, to write in this group, you need to register via @YourBot and join the group/channel first.",
        'stats': "📊 Statistics:\nTotal users: {}\nVerified users: {}\nTotal mods: {}\nLast 10 users:\n{}\nActive sessions: {}\nBanned users: {}",
        'broadcast_prompt': "📢 Enter the message to broadcast to all users:",
        'broadcast_success': "✅ Message successfully sent to {} users!",
        'broadcast_failed': "❌ Message sending error: {}",
        'no_users': "❌ No users found.",
        'start_verify': "📤 Start — send data",
        'admin_panel': "🔐 Admin Panel\nPlease select an action:",
        'admin_stats': "📊 Statistics",
        'admin_broadcast': "📢 Broadcast messages",
        'admin_export': "📄 Export",
        'admin_ban_user': "🚫 Ban user",
        'admin_unban_user': "✅ Unban",
        'admin_view_logs': "📜 View logs",
        'admin_manage_mods': "🛠 Manage mods",
        'export_prompt': "📄 Select database format:",
        'export_txt': "TXT",
        'export_json': "JSON",
        'export_csv': "CSV",
        'export_success': "✅ Database successfully exported!",
        'export_failed': "❌ Export error: {}",
        'not_in_group_or_channel': "❌ You are not a member of the group or channel. Please join via the links below and try again:",
        'mods_menu': "📦 Mods\nSelect one of the mods below:",
        'no_mods': "❌ No mods available yet.",
        'admin_add_mod': "➕ Add mod",
        'admin_remove_mod': "🗑 Remove mod",
        'admin_list_mods': "📋 Mod list",
        'admin_edit_mod': "✏ Edit mod",
        'add_mod_prompt': "📦 To add a new mod, enter:\n1) Mod name (e.g., Mod1)\n2) Description\n3) File link (Telegram or external URL)\n4) Category (e.g., Games)\n\nSend in format:\nMod name: <name>\nDescription: <description>\nLink: <URL>\nCategory: <category>",
        'add_mod_success': "✅ Mod successfully added: {}",
        'add_mod_failed': "❌ Mod adding error: {}",
        'remove_mod_prompt': "🗑 Enter mod name to remove:",
        'remove_mod_success': "✅ Mod successfully removed: {}",
        'remove_mod_failed': "❌ Mod removal error: {}",
        'mod_list': "📋 Mod list:\n{}",
        'mod_list_empty': "❌ Mod list is empty.",
        'invalid_mod_format': "❌ Invalid format. Please send in format:\nMod name: <name>\nDescription: <description>\nLink: <URL>\nCategory: <category>",
        'ban_prompt': "🚫 Enter user ID to ban:",
        'ban_success': "✅ User {} successfully banned!",
        'ban_failed': "❌ Ban error: {}",
        'unban_prompt': "✅ Enter user ID to unban:",
        'unban_success': "✅ User {} unbanned!",
        'unban_failed': "❌ Unban error: {}",
        'logs_prompt': "📜 To send log file, press 'Send logs' button:",
        'logs_send': "Send logs",
        'logs_success': "✅ Logs successfully sent!",
        'logs_failed': "❌ Logs sending error: {}",
        'edit_mod_prompt': "✏ Enter mod name and new data:\nFormat: Mod name: <old name>\nNew name: <new name>\nDescription: <new description>\nLink: <new URL>\nCategory: <new category>",
        'edit_mod_success': "✅ Mod successfully edited: {}",
        'edit_mod_failed': "❌ Mod editing error: {}",
        'profile_prompt': "👤 To view your profile, press 'View profile' button:",
        'profile_view': "View profile",
        'profile': "👤 Your profile:\nName: {}\nPhone: {}\nAge: {}\nUsername: {}\nRegistration date: {}\nStatus: {}",
        'help': "❓ Help:\n/start - Start\n/mods - View mods\n/profile - View profile\n/help - This help\n/weather - Weather\n/calculator - Calculation\n/news - News",
        'feedback_prompt': "📝 Send your feedback:",
        'feedback_success': "✅ Feedback accepted!",
        'admin_view_feedback': "📝 View feedback",
        'no_feedback': "❌ No feedback yet.",
        'feedback_list': "📝 Feedback list:\n{}",
        'category_prompt': "📂 Select category:",
        'search_mods': "🔍 Search mods",
        'search_prompt': "🔍 Enter search query:",
        'search_results': "🔍 Results:\n{}",
        'no_results': "❌ No results found.",
        'rate_mod': "⭐ Rate mod",
        'rate_prompt': "⭐ Enter mod name and rating (1-5):\nFormat: Mod name: <name>\nRating: <1-5>",
        'rate_success': "✅ Rating added!",
        'rate_failed': "❌ Rating adding error: {}",
        'mod_ratings': "⭐ Mod ratings: {}",
        'admin_backup_db': "💾 DB backup",
        'backup_success': "✅ Backup successfully created!",
        'backup_failed': "❌ Backup error: {}",
        'admin_restore_db': "🔄 DB restore",
        'restore_prompt': "🔄 Send file for restore.",
        'restore_success': "✅ DB restored!",
        'restore_failed': "❌ Restore error: {}",
        'session_expired': "⏰ Session expired. Start over.",
        'welcome_back': "👋 Welcome back! Your verification is still valid.",
        'update_profile': "🔄 Update profile",
        'update_prompt': "🔄 Select field to update:",
        'update_full_name': "👤 Update name",
        'update_phone': "📱 Update phone",
        'update_age': "🎂 Update age",
        'update_username': "🆔 Update username",
        'update_success': "✅ Profile updated!",
        'update_failed': "❌ Update error: {}",
        'admin_user_search': "🔍 Search user",
        'search_user_prompt': "🔍 Search: Enter ID or username:",
        'user_info': "👤 User info:\n{}",
        'no_user_found': "❌ User not found.",
        'admin_announce': "📣 Send announcement",
        'announce_prompt': "📣 Enter announcement text:",
        'announce_success': "✅ Announcement sent!",
        'poll_create': "📊 Create poll",
        'poll_prompt': "📊 Enter poll question and options:\nFormat: Question: <question>\nOption1\nOption2\n...",
        'poll_success': "✅ Poll created and sent!",
        'poll_failed': "❌ Poll creation error: {}",
        'event_schedule': "🗓 Schedule event",
        'event_prompt': "🗓 Enter event name, time and description:",
        'event_success': "✅ Event scheduled!",
        'event_list': "🗓 Event list:\n{}",
        'no_events': "❌ No events.",
        'reminder_set': "⏰ Set reminder",
        'reminder_prompt': "⏰ Enter reminder text and time (in seconds):",
        'reminder_success': "✅ Reminder set!",
        'captcha_prompt': "🤖 Captcha: {} = ? (Answer with number)",
        'captcha_invalid': "❌ Incorrect captcha. Try again.",
        'captcha_success': "✅ Captcha correct!",
        'multi_lang_support': "🌍 Change language",
        'lang_uz': "🇺🇿 O'zbekcha",
        'lang_ru': "🇷🇺 Русский",
        'lang_en': "🇬🇧 English",
        # Qo'shimcha so'zlar uchun
        'weather_prompt': "🏙 Enter city name (e.g., Tashkent):",
        'weather_info': "🏙 Weather in {}:\nTemperature: {}°C\nCondition: {}\nHumidity: {}%",
        'weather_error': "❌ Weather not found. Enter city correctly.",
        'calculator_prompt': "Enter calculation (e.g., 2+3*4):",
        'calculator_result': "Result: {}",
        'calculator_error': "❌ Invalid calculation. Try again.",
        'news_prompt': "Latest news:",
        'news_error': "❌ No news found.",
    },
}

# ================= LOGGING =================
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    filename="bot.log",
    encoding="utf-8"
)
logger = logging.getLogger(__name__)

# ================= DATABASE =================
@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation error: {str(e)}")
        raise
    else:
        conn.commit()
    finally:
        conn.close()

def init_db():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                full_name TEXT,
                phone TEXT,
                age INTEGER,
                username TEXT,
                join_date TEXT,
                verified BOOLEAN DEFAULT 0,
                banned BOOLEAN DEFAULT 0,
                language TEXT DEFAULT 'uz',
                last_activity TEXT,
                profile_photo_url TEXT,
                bio TEXT,
                points INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS mods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_id TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                file_url TEXT NOT NULL,
                added_date TEXT,
                category TEXT,
                average_rating REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_text TEXT,
                feedback_date TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                event_date TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_id TEXT,
                user_id INTEGER,
                rating INTEGER,
                UNIQUE(mod_id, user_id)
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER UNIQUE,
                session_start TEXT,
                session_token TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER UNIQUE,
                ban_reason TEXT,
                ban_date TEXT
            )
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS internal_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                message TEXT
            )
            """)
            logger.info("Database initialized with extended tables")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        print(f"Error: Database initialization failed: {str(e)}")

def save_user(user_id: int, full_name: Optional[str] = None, phone: Optional[str] = None, age: Optional[int] = None, 
              username: Optional[str] = None, join_date: Optional[str] = None, verified: bool = False, 
              banned: bool = False, language: str = 'uz', last_activity: Optional[str] = None, 
              profile_photo_url: Optional[str] = None, bio: Optional[str] = None, points: int = 0, level: int = 1):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO users 
                (user_id, full_name, phone, age, username, join_date, verified, banned, language, last_activity, profile_photo_url, bio, points, level) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, full_name, phone, age, username, join_date, verified, banned, language, last_activity, profile_photo_url, bio, points, level)
            )
        logger.info(f"User {user_id} saved/updated in database")
    except Exception as e:
        logger.error(f"User save error for {user_id}: {str(e)}")
        raise

def update_user_field(user_id: int, field: str, value: Any):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            if cur.rowcount == 0:
                logger.warning(f"No user found to update {field} for {user_id}")
                return False
        logger.info(f"Updated {field} for user {user_id} to {value}")
        return True
    except Exception as e:
        logger.error(f"Update user field error for {user_id}: {str(e)}")
        return False

def ban_user(user_id: int, reason: Optional[str] = None):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
            if reason:
                ban_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("INSERT OR REPLACE INTO bans (user_id, ban_reason, ban_date) VALUES (?, ?, ?)", (user_id, reason, ban_date))
            if cur.rowcount == 0:
                logger.warning(f"No user found to ban {user_id}")
                return False
        logger.info(f"User {user_id} banned with reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Ban user error for {user_id}: {str(e)}")
        return False

def unban_user(user_id: int):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
            if cur.rowcount == 0:
                logger.warning(f"No user found to unban {user_id}")
                return False
        logger.info(f"User {user_id} unbanned")
        return True
    except Exception as e:
        logger.error(f"Unban user error for {user_id}: {str(e)}")
        return False

def is_user_banned(user_id: int) -> bool:
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            return result and result[0] == 1
    except Exception as e:
        logger.error(f"Check banned error for {user_id}: {str(e)}")
        return False

def save_mod(name: str, description: str, file_url: str, category: str = "Uncategorized"):
    try:
        mod_id = str(uuid.uuid4())
        added_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO mods (mod_id, name, description, file_url, added_date, category) VALUES (?, ?, ?, ?, ?, ?)",
                (mod_id, name, description, file_url, added_date, category)
            )
        logger.info(f"Mod {name} saved with ID {mod_id} in category {category}")
        return True
    except Exception as e:
        logger.error(f"Mod save error: {str(e)}")
        return False

def edit_mod(old_name: str, new_name: Optional[str] = None, description: Optional[str] = None, file_url: Optional[str] = None, category: Optional[str] = None):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            updates = []
            params = []
            if new_name:
                updates.append("name = ?")
                params.append(new_name)
            if description:
                updates.append("description = ?")
                params.append(description)
            if file_url:
                updates.append("file_url = ?")
                params.append(file_url)
            if category:
                updates.append("category = ?")
                params.append(category)
            if not updates:
                return False
            query = f"UPDATE mods SET {', '.join(updates)} WHERE name = ?"
            params.append(old_name)
            cur.execute(query, params)
            if cur.rowcount > 0:
                logger.info(f"Mod {old_name} edited")
                return True
            logger.warning(f"Mod {old_name} not found for edit")
            return False
    except Exception as e:
        logger.error(f"Mod edit error: {str(e)}")
        return False

def remove_mod(name: str):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT mod_id FROM mods WHERE name = ?", (name,))
            result = cur.fetchone()
            if result:
                mod_id = result[0]
                cur.execute("DELETE FROM ratings WHERE mod_id = ?", (mod_id,))
                cur.execute("DELETE FROM mods WHERE name = ?", (name,))
                logger.info(f"Mod {name} and its ratings removed")
                return True
            logger.warning(f"Mod {name} not found")
            return False
    except Exception as e:
        logger.error(f"Mod remove error: {str(e)}")
        return False

def get_mods(category: Optional[str] = None):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            if category:
                cur.execute("SELECT name, description, file_url, category, average_rating FROM mods WHERE category = ? ORDER BY added_date DESC", (category,))
            else:
                cur.execute("SELECT name, description, file_url, category, average_rating FROM mods ORDER BY added_date DESC")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Get mods error: {str(e)}")
        return []

def search_mods(query: str):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            search_term = f"%{query}%"
            cur.execute("SELECT name, description, file_url, category FROM mods WHERE name LIKE ? OR description LIKE ? ORDER BY added_date DESC", (search_term, search_term))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Search mods error: {str(e)}")
        return []

def add_rating(mod_name: str, user_id: int, rating: int):
    if not 1 <= rating <= 5:
        return False
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT mod_id FROM mods WHERE name = ?", (mod_name,))
            result = cur.fetchone()
            if not result:
                return False
            mod_id = result[0]
            cur.execute("INSERT OR REPLACE INTO ratings (mod_id, user_id, rating) VALUES (?, ?, ?)", (mod_id, user_id, rating))
            cur.execute("SELECT AVG(rating), COUNT(rating) FROM ratings WHERE mod_id = ?", (mod_id,))
            avg, count = cur.fetchone()
            cur.execute("UPDATE mods SET average_rating = ?, rating_count = ? WHERE mod_id = ?", (avg or 0.0, count or 0, mod_id))
            logger.info(f"Rating {rating} added for mod {mod_name} by user {user_id}")
            return True
    except Exception as e:
        logger.error(f"Add rating error: {str(e)}")
        return False

def get_mod_ratings(mod_name: str) -> str:
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT average_rating, rating_count FROM mods WHERE name = ?", (mod_name,))
            result = cur.fetchone()
            if result:
                return f"Average: {result[0]:.1f} ({result[1]} ratings)"
            return "No ratings yet"
    except Exception as e:
        logger.error(f"Get mod ratings error: {str(e)}")
        return "Error"

def save_feedback(user_id: int, feedback_text: str):
    try:
        feedback_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO feedback (user_id, feedback_text, feedback_date) VALUES (?, ?, ?)", (user_id, feedback_text, feedback_date))
        logger.info(f"Feedback saved from user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Save feedback error: {str(e)}")
        return False

def get_feedback():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id, feedback_text, feedback_date FROM feedback ORDER BY feedback_date DESC")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Get feedback error: {str(e)}")
        return []

def save_event(name: str, description: str, event_date: str):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO events (name, description, event_date) VALUES (?, ?, ?)", (name, description, event_date))
        logger.info(f"Event {name} saved")
        return True
    except Exception as e:
        logger.error(f"Save event error: {str(e)}")
        return False

def get_events():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, description, event_date FROM events ORDER BY event_date ASC")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Get events error: {str(e)}")
        return []

def start_session(user_id: int):
    try:
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_token = base64.b64encode(hashlib.sha256(str(user_id + time.time()).encode()).digest()).decode()
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO sessions (user_id, session_start, session_token) VALUES (?, ?, ?)", (user_id, session_start, session_token))
        logger.info(f"Session started for user {user_id}")
        return session_token
    except Exception as e:
        logger.error(f"Start session error for {user_id}: {str(e)}")
        return None

def check_session(user_id: int) -> bool:
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT session_start FROM sessions WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            if result:
                session_start = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - session_start).total_seconds() < SESSION_TIMEOUT:
                    return True
                else:
                    cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
                    logger.info(f"Session expired for user {user_id}")
                    return False
            return False
    except Exception as e:
        logger.error(f"Check session error for {user_id}: {str(e)}")
        return False

def log_internal(level: str, message: str):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO internal_logs (timestamp, level, message) VALUES (?, ?, ?)", (timestamp, level, message))
        logger.log(getattr(logging, level.upper()), message)
    except Exception as e:
        logger.error(f"Internal log error: {str(e)}")

def get_user_data(user_id: int) -> Optional[Dict]:
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            if result:
                return dict(result)
            return None
    except Exception as e:
        logger.error(f"Get user data error for {user_id}: {str(e)}")
        return None

def search_user(query: str) -> List[Dict]:
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            search_term = f"%{query}%"
            cur.execute("SELECT * FROM users WHERE user_id LIKE ? OR username LIKE ?", (search_term, search_term))
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Search user error: {str(e)}")
        return []

def backup_db() -> Optional[str]:
    try:
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        with sqlite3.connect(DB_PATH) as src, sqlite3.connect(backup_path) as dst:
            src.backup(dst)
        logger.info(f"DB backed up to {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"DB backup error: {str(e)}")
        return None

def restore_db(backup_path: str) -> bool:
    try:
        if not os.path.exists(backup_path):
            return False
        os.replace(backup_path, DB_PATH)
        logger.info(f"DB restored from {backup_path}")
        return True
    except Exception as e:
        logger.error(f"DB restore error: {str(e)}")
        return False

async def is_user_verified(user_id: int):
    if is_user_banned(user_id):
        logger.info(f"User {user_id} is banned")
        return False
    if not check_session(user_id):
        logger.info(f"Session expired for user {user_id}")
        return False
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT verified, language FROM users WHERE user_id = ?", (user_id,))
            result = cur.fetchone()
            if not result or result[0] != 1:
                logger.info(f"User {user_id} not verified in DB")
                return False
            lang = result[1]
        try:
            group_member = await bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
            if group_member.status in ['left', 'kicked']:
                logger.info(f"User {user_id} not in group")
                return False
        except Exception as e:
            logger.error(f"Group membership check error for {user_id}: {str(e)}")
            return False
        try:
            channel_member = await bot.get_chat_member(chat_id=SECRET_CHANNEL, user_id=user_id)
            if channel_member.status in ['left', 'kicked']:
                logger.info(f"User {user_id} not in channel")
                return False
        except Exception as e:
            logger.error(f"Channel membership check error for {user_id}: {str(e)}")
            return False
        update_user_field(user_id, "last_activity", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info(f"User {user_id} verified and active")
        return True
    except Exception as e:
        logger.error(f"Verification check error for {user_id}: {str(e)}")
        return False

def get_stats():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE verified = 1")
            verified_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
            banned_users = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM mods")
            total_mods = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM sessions")
            active_sessions = cur.fetchone()[0]
            cur.execute("SELECT user_id, full_name, username, join_date FROM users WHERE verified = 1 ORDER BY join_date DESC LIMIT 10")
            recent_users = cur.fetchall()
            recent_list = "\n".join([f"ID: {u[0]}, Name: {u[1]}, Username: {u[2]}, Date: {u[3]}" for u in recent_users]) or "No recent users"
            return {
                'total_users': total_users,
                'verified_users': verified_users,
                'banned_users': banned_users,
                'total_mods': total_mods,
                'active_sessions': active_sessions,
                'recent_users': recent_list
            }
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return None

def get_all_users(verified_only: bool = True):
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            if verified_only:
                cur.execute("SELECT user_id FROM users WHERE verified = 1 AND banned = 0")
            else:
                cur.execute("SELECT user_id FROM users")
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Get all users error: {str(e)}")
        return []

def get_all_users_data():
    try:
        with db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users ORDER BY join_date DESC")
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Get all users data error: {str(e)}")
        return []

def generate_export(format_type: str = "TXT") -> Optional[str]:
    try:
        users = get_all_users_data()
        mods = get_mods()
        feedback = get_feedback()
        events = get_events()
        if not (users or mods or feedback or events):
            return None
        file_path = f"export_{format_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type.lower()}"
        if format_type == "TXT":
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("Users:\n")
                for user in users:
                    f.write(f"ID: {user['user_id']}, Name: {user['full_name']}, Phone: {user['phone']}, Age: {user['age']}, Username: {user['username']}, Verified: {user['verified']}, Banned: {user['banned']}\n")
                f.write("\nMods:\n")
                for mod in mods:
                    f.write(f"Name: {mod['name']}, Description: {mod['description']}, URL: {mod['file_url']}, Category: {mod['category']}\n")
                f.write("\nFeedback:\n")
                for fb in feedback:
                    f.write(f"User: {fb['user_id']}, Text: {fb['feedback_text']}, Date: {fb['feedback_date']}\n")
                f.write("\nEvents:\n")
                for ev in events:
                    f.write(f"Name: {ev['name']}, Description: {ev['description']}, Date: {ev['event_date']}\n")
        elif format_type == "JSON":
            data = {
                "users": users,
                "mods": mods,
                "feedback": feedback,
                "events": events
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        elif format_type == "CSV":
            import csv
            with open(file_path, "w", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "ID", "Name", "Description/Details"])
                for u in users:
                    writer.writerow(["User", u['user_id'], u['full_name'], f"Phone: {u['phone']}, Age: {u['age']}"])
                for m in mods:
                    writer.writerow(["Mod", m['name'], m['description'], m['file_url']])
                # Add feedback and events similarly
        logger.info(f"Export generated: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Generate export error: {str(e)}")
        return None

# ================= BOT =================
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

# ================= FSM STATES =================
class Register(StatesGroup):
    full_name = State()
    phone = State()
    age = State()
    username = State()
    broadcast = State()
    export = State()
    add_mod = State()
    remove_mod = State()
    ban_user = State()
    unban_user = State()
    feedback = State()
    search_mods = State()
    rate_mod = State()
    edit_mod = State()
    update_profile_field = State()
    search_user = State()
    announce = State()
    poll = State()
    event = State()
    reminder = State()
    captcha = State()
    lang = State()
    restore = State()
    weather = State()  # Qo'shimcha: ob-havo state
    calculator = State()  # Qo'shimcha: calculator state

# ================= HELPERS =================
def get_lang(user_id: int) -> str:
    user_data = get_user_data(user_id)
    return user_data.get('language', 'uz') if user_data else 'uz'

def is_private_chat(obj: Any) -> bool:
    chat = getattr(obj, "chat", None)
    return chat and chat.type == "private"

def clean_phone_number(phone: str) -> Optional[str]:
    cleaned = re.sub(r"[^\d+]", "", phone)
    if re.match(PHONE_REGEX, cleaned):
        return cleaned
    return None

async def send_message_safe(chat_id: int, text: str, reply_markup: Any = None, retry_count: int = 0):
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        return True
    except TelegramRetryAfter as e:
        if retry_count >= RATE_LIMIT_RETRY:
            return False
        await asyncio.sleep(e.retry_after)
        return await send_message_safe(chat_id, text, reply_markup, retry_count + 1)
    except TelegramForbiddenError:
        logger.warning(f"Blocked by user {chat_id}")
        return False
    except Exception as e:
        logger.error(f"Send message error to {chat_id}: {str(e)}")
        return False

async def send_dm_or_group_notice(user_id: int, text: str, group_id: int, username: Optional[str] = None, first_name: Optional[str] = None, lang: str = 'uz'):
    if await send_message_safe(user_id, text):
        return True
    user_display = f"@{username}" if username else first_name or "user"
    notice_text = LANGUAGES[lang]['group_notice'].format(user=user_display)
    await send_message_safe(group_id, notice_text)
    return False

async def send_membership_notice(user_id: int, lang: str = 'uz'):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Join Group")],
            [KeyboardButton(text="📢 Join Channel")]
        ],
        resize_keyboard=True
    )
    await send_message_safe(user_id, LANGUAGES[lang]['not_in_group_or_channel'], kb)

async def generate_captcha() -> tuple:
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    return f"{a} + {b}", a + b

# Qo'shimcha funksiyalar
async def get_weather(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['main']['temp'], data['weather'][0]['description'], data['main']['humidity']
    return None

def calculate_expression(expr: str):
    try:
        return eval(expr, {"__builtins__": {}}, {})
    except:
        return None

async def get_news():
    rss_url = "http://feeds.bbci.co.uk/news/rss.xml"  # BBC News RSS
    feed = feedparser.parse(rss_url)
    news_list = []
    for entry in feed.entries[:5]:  # So'nggi 5 yangilik
        news_list.append(f"{entry.title}: {entry.link}")
    return "\n".join(news_list) if news_list else None

# ================= STARTUP CHECKS =================
async def on_startup(_):
    logger.info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info(f"Bot: @{me.username}")
    try:
        group_status = await bot.get_chat_member(GROUP_ID, me.id)
        if group_status.status not in ['administrator', 'creator'] or not (group_status.can_delete_messages and group_status.can_restrict_members):
            print("Warning: Bot not admin or lacks permissions in group.")
    except Exception as e:
        print(f"Error checking group: {str(e)}")
    try:
        channel_status = await bot.get_chat_member(SECRET_CHANNEL, me.id)
        if channel_status.status not in ['administrator', 'creator']:
            print("Warning: Bot not admin in channel.")
    except Exception as e:
        print(f"Error checking channel: {str(e)}")
    init_db()

# ================= MIDDLEWARE =================
class RateLimitMiddleware:
    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Middleware error: {str(e)}")
            return

# ================= HANDLERS =================
@dp.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    if not is_private_chat(message):
        lang = 'uz'  # Default
        await message.answer(LANGUAGES[lang]['private_only'])
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    if get_user_data(user_id):
        await message.answer(LANGUAGES[lang]['welcome_back'])
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['start_verify'])],
            [KeyboardButton(text=LANGUAGES[lang]['mods_menu'])],
            [KeyboardButton(text=LANGUAGES[lang]['profile_view'])],
            [KeyboardButton(text=LANGUAGES[lang]['help'])],
            [KeyboardButton(text=LANGUAGES[lang]['feedback_prompt'])],
            [KeyboardButton(text=LANGUAGES[lang]['multi_lang_support'])],
        ],
        resize_keyboard=True
    )
    if message.from_user.username == ADMIN_USERNAME:
        kb.keyboard.append([KeyboardButton(text=LANGUAGES[lang]['admin_panel'])])
    await message.answer(LANGUAGES[lang]['welcome'], reply_markup=kb)
    start_session(user_id)
    await state.clear()
    log_internal("INFO", f"Start by {user_id}")

@dp.message(F.text.in_([
    LANGUAGES['uz']['multi_lang_support'],
    LANGUAGES['ru']['multi_lang_support'],
    LANGUAGES['en']['multi_lang_support'],
]))
async def change_lang(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['lang_uz'])],
            [KeyboardButton(text=LANGUAGES[lang]['lang_ru'])],
            [KeyboardButton(text=LANGUAGES[lang]['lang_en'])],
        ],
        resize_keyboard=True
    )
    await message.answer("Select language / Tilni tanlang / Выберите язык:", reply_markup=kb)
    await state.set_state(Register.lang)

@dp.message(Register.lang)
async def process_lang(message: Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    lang = get_lang(user_id)
    if text in [LANGUAGES[lang]['lang_uz'], LANGUAGES['ru']['lang_uz'], LANGUAGES['en']['lang_uz']]:
        new_lang = 'uz'
    elif text in [LANGUAGES[lang]['lang_ru'], LANGUAGES['uz']['lang_ru'], LANGUAGES['en']['lang_ru']]:
        new_lang = 'ru'
    elif text in [LANGUAGES[lang]['lang_en'], LANGUAGES['uz']['lang_en'], LANGUAGES['ru']['lang_en']]:
        new_lang = 'en'
    else:
        await message.reply("Invalid choice / Noto'g'ri tanlov / Неправильный выбор.")
        return
    update_user_field(user_id, "language", new_lang)
    await message.answer(f"Language changed to {new_lang}", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_panel'], LANGUAGES['ru']['admin_panel'], LANGUAGES['en']['admin_panel']]))
async def admin_panel(message: Message, state: FSMContext):
    if not is_private_chat(message) or message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['admin_stats'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_broadcast'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_export'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_ban_user'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_unban_user'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_view_logs'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_manage_mods'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_view_feedback'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_backup_db'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_restore_db'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_user_search'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_announce'])],
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['admin_panel'], reply_markup=kb)

@dp.message(F.text.in_([LANGUAGES['uz']['admin_stats'], LANGUAGES['ru']['admin_stats'], LANGUAGES['en']['admin_stats']]))
async def admin_stats(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    stats = get_stats()
    if stats:
        text = LANGUAGES[lang]['stats'].format(
            stats['total_users'], stats['verified_users'], stats['total_mods'], stats['recent_users'],
            stats['active_sessions'], stats['banned_users']
        )
        await message.answer(text)
    else:
        await message.answer(LANGUAGES[lang]['error'].format("Stats"))

@dp.message(F.text.in_([LANGUAGES['uz']['admin_broadcast'], LANGUAGES['ru']['admin_broadcast'], LANGUAGES['en']['admin_broadcast']]))
async def admin_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['broadcast_prompt'])
    await state.set_state(Register.broadcast)

@dp.message(Register.broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    text = message.text
    users = get_all_users()
    success_count = 0
    for user in users:
        if await send_message_safe(user, text):
            success_count += 1
        await asyncio.sleep(BROADCAST_DELAY)
    await message.answer(LANGUAGES[lang]['broadcast_success'].format(success_count))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_export'], LANGUAGES['ru']['admin_export'], LANGUAGES['en']['admin_export']]))
async def admin_export(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=fmt)] for fmt in EXPORT_FORMATS],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['export_prompt'], reply_markup=kb)
    await state.set_state(Register.export)
@dp.message(Register.export)
async def process_export(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    format_type = message.text.upper()
    if format_type not in EXPORT_FORMATS:
        await message.reply("Invalid format.")
        return
    file_path = generate_export(format_type)
    if file_path:
        await message.answer("Export muvaffaqiyatli! Fayl saqlandi, lekin yuborilmaydi.")
    else:
        await message.answer(LANGUAGES[lang]['export_failed'].format("No data"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_ban_user'], LANGUAGES['ru']['admin_ban_user'], LANGUAGES['en']['admin_ban_user']]))
async def admin_ban(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['ban_prompt'])
    await state.set_state(Register.ban_user)

@dp.message(Register.ban_user)
async def process_ban(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    try:
        user_id = int(message.text)
        if ban_user(user_id, "Admin ban"):
            await message.answer(LANGUAGES[lang]['ban_success'].format(user_id))
        else:
            await message.answer(LANGUAGES[lang]['ban_failed'].format("Not found"))
    except ValueError:
        await message.answer(LANGUAGES[lang]['ban_failed'].format("Invalid ID"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_unban_user'], LANGUAGES['ru']['admin_unban_user'], LANGUAGES['en']['admin_unban_user']]))
async def admin_unban(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['unban_prompt'])
    await state.set_state(Register.unban_user)

@dp.message(Register.unban_user)
async def process_unban(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    try:
        user_id = int(message.text)
        if unban_user(user_id):
            await message.answer(LANGUAGES[lang]['unban_success'].format(user_id))
        else:
            await message.answer(LANGUAGES[lang]['unban_failed'].format("Not found"))
    except ValueError:
        await message.answer(LANGUAGES[lang]['unban_failed'].format("Invalid ID"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_view_logs'], LANGUAGES['ru']['admin_view_logs'], LANGUAGES['en']['admin_view_logs']]))
async def admin_view_logs(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    if os.path.exists("bot.log"):
        await message.answer_document(FSInputFile("bot.log"), caption=LANGUAGES[lang]['logs_success'])
    else:
        await message.answer(LANGUAGES[lang]['logs_failed'].format("No log file"))

@dp.message(F.text.in_([LANGUAGES['uz']['admin_manage_mods'], LANGUAGES['ru']['admin_manage_mods'], LANGUAGES['en']['admin_manage_mods']]))
async def admin_manage_mods(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['admin_add_mod'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_remove_mod'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_edit_mod'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_list_mods'])],
        ],
        resize_keyboard=True
    )
    await message.answer("Manage mods / Modlarni boshqarish / Управление модами:", reply_markup=kb)

@dp.message(F.text.in_([LANGUAGES['uz']['admin_add_mod'], LANGUAGES['ru']['admin_add_mod'], LANGUAGES['en']['admin_add_mod']]))
async def admin_add_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['add_mod_prompt'])
    await state.set_state(Register.add_mod)

@dp.message(Register.add_mod)
async def process_add_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    text = message.text
    pattern = r"Mod nomi: (.+)\nTavsif: (.+)\nHavola: (.+)\nKategoriya: (.+)" if lang == 'uz' else r"Название мода: (.+)\nОписание: (.+)\nСсылка: (.+)\nКатегория: (.+)" if lang == 'ru' else r"Mod name: (.+)\nDescription: (.+)\nLink: (.+)\nCategory: (.+)"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        await message.reply(LANGUAGES[lang]['invalid_mod_format'])
        return
    name, description, file_url, category = [s.strip() for s in match.groups()]
    if category not in MOD_CATEGORIES:
        category = "Uncategorized"
    if save_mod(name, description, file_url, category):
        await message.answer(LANGUAGES[lang]['add_mod_success'].format(name))
    else:
        await message.answer(LANGUAGES[lang]['add_mod_failed'].format("DB error"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_remove_mod'], LANGUAGES['ru']['admin_remove_mod'], LANGUAGES['en']['admin_remove_mod']]))
async def admin_remove_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['remove_mod_prompt'])
    await state.set_state(Register.remove_mod)

@dp.message(Register.remove_mod)
async def process_remove_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    name = message.text.strip()
    if remove_mod(name):
        await message.answer(LANGUAGES[lang]['remove_mod_success'].format(name))
    else:
        await message.answer(LANGUAGES[lang]['remove_mod_failed'].format("Not found"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_edit_mod'], LANGUAGES['ru']['admin_edit_mod'], LANGUAGES['en']['admin_edit_mod']]))
async def admin_edit_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['edit_mod_prompt'])
    await state.set_state(Register.edit_mod)

@dp.message(Register.edit_mod)
async def process_edit_mod(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    text = message.text
    pattern = r"Mod nomi: (.+)\nYangi nomi: (.+)\nTavsif: (.+)\nHavola: (.+)\nKategoriya: (.+)" if lang == 'uz' else r"Название мода: (.+)\nНовое название: (.+)\nОписание: (.+)\nСсылка: (.+)\nКатегория: (.+)" if lang == 'ru' else r"Mod name: (.+)\nNew name: (.+)\nDescription: (.+)\nLink: (.+)\nCategory: (.+)"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        await message.reply(LANGUAGES[lang]['invalid_mod_format'])
        return
    old_name, new_name, description, file_url, category = [s.strip() for s in match.groups()]
    if edit_mod(old_name, new_name, description, file_url, category):
        await message.answer(LANGUAGES[lang]['edit_mod_success'].format(new_name or old_name))
    else:
        await message.answer(LANGUAGES[lang]['edit_mod_failed'].format("Not found"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_list_mods'], LANGUAGES['ru']['admin_list_mods'], LANGUAGES['en']['admin_list_mods']]))
async def admin_list_mods(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    mods = get_mods()
    if not mods:
        await message.answer(LANGUAGES[lang]['mod_list_empty'])
    else:
        mod_list = "\n".join([f"{mod['name']} ({mod['category']}): {mod['description']} - {mod['file_url']} Rating: {mod['average_rating']}" for mod in mods])
        await message.answer(LANGUAGES[lang]['mod_list'].format(mod_list))

@dp.message(F.text.in_([LANGUAGES['uz']['mods_menu'], LANGUAGES['ru']['mods_menu'], LANGUAGES['en']['mods_menu']]))
async def show_mods(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        lang = get_lang(user_id)
        await message.answer(LANGUAGES[lang]['verification_needed'])
        return
    lang = get_lang(user_id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=cat)] for cat in MOD_CATEGORIES
        ] + [
            [KeyboardButton(text=LANGUAGES[lang]['search_mods'])],
            [KeyboardButton(text=LANGUAGES[lang]['rate_mod'])],
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['category_prompt'], reply_markup=kb)

@dp.message(F.text.in_(MOD_CATEGORIES))
async def show_mods_category(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    category = message.text
    lang = get_lang(user_id)
    mods = get_mods(category)
    if not mods:
        await message.answer(LANGUAGES[lang]['no_mods'])
        return
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=mod['name'])] for mod in mods
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['mods_menu'], reply_markup=kb)

@dp.message(F.text.in_([LANGUAGES['uz']['search_mods'], LANGUAGES['ru']['search_mods'], LANGUAGES['en']['search_mods']]))
async def search_mods_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['search_prompt'])
    await state.set_state(Register.search_mods)

@dp.message(Register.search_mods)
async def process_search_mods(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    query = message.text.strip()
    mods = search_mods(query)
    if not mods:
        await message.answer(LANGUAGES[lang]['no_results'])
    else:
        results = "\n".join([f"{mod['name']}: {mod['description']} - {mod['file_url']}" for mod in mods])
        await message.answer(LANGUAGES[lang]['search_results'].format(results))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['rate_mod'], LANGUAGES['ru']['rate_mod'], LANGUAGES['en']['rate_mod']]))
async def rate_mod_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['rate_prompt'])
    await state.set_state(Register.rate_mod)

@dp.message(Register.rate_mod)
async def process_rate_mod(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    text = message.text
    pattern = r"Mod nomi: (.+)\nBaho: (\d+)" if lang == 'uz' else r"Название мода: (.+)\nОценка: (\d+)" if lang == 'ru' else r"Mod name: (.+)\nRating: (\d+)"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        await message.reply(LANGUAGES[lang]['invalid_mod_format'])
        return
    name, rating_str = match.groups()
    try:
        rating = int(rating_str)
        if add_rating(name.strip(), user_id, rating):
            await message.answer(LANGUAGES[lang]['rate_success'])
        else:
            await message.answer(LANGUAGES[lang]['rate_failed'].format("Invalid"))
    except ValueError:
        await message.answer(LANGUAGES[lang]['rate_failed'].format("Invalid rating"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['profile_view'], LANGUAGES['ru']['profile_view'], LANGUAGES['en']['profile_view']]))
async def view_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    data = get_user_data(user_id)
    if data:
        status = "Verified" if data['verified'] else "Not verified"
        text = LANGUAGES[lang]['profile'].format(
            data['full_name'], data['phone'], data['age'], data['username'], data['join_date'], status
        )
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=LANGUAGES[lang]['update_profile'])],
            ],
            resize_keyboard=True
        )
        await message.answer(text, reply_markup=kb)
    else:
        await message.answer("Profile not found.")

@dp.message(F.text.in_([LANGUAGES['uz']['update_profile'], LANGUAGES['ru']['update_profile'], LANGUAGES['en']['update_profile']]))
async def update_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['update_full_name'])],
            [KeyboardButton(text=LANGUAGES[lang]['update_phone'])],
            [KeyboardButton(text=LANGUAGES[lang]['update_age'])],
            [KeyboardButton(text=LANGUAGES[lang]['update_username'])],
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['update_prompt'], reply_markup=kb)
    await state.set_state(Register.update_profile_field)

@dp.message(Register.update_profile_field)
async def process_update_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    text = message.text
    if text in [LANGUAGES[lang]['update_full_name'] for lang in LANGUAGES]:
        await message.answer(LANGUAGES[lang]['full_name_prompt'])
        await state.update_data(update_field="full_name")
    elif text in [LANGUAGES[lang]['update_phone'] for lang in LANGUAGES]:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
        await message.answer(LANGUAGES[lang]['phone_prompt'], reply_markup=kb)
        await state.update_data(update_field="phone")
    elif text in [LANGUAGES[lang]['update_age'] for lang in LANGUAGES]:
        await message.answer(LANGUAGES[lang]['age_prompt'])
        await state.update_data(update_field="age")
    elif text in [LANGUAGES[lang]['update_username'] for lang in LANGUAGES]:
        await message.answer(LANGUAGES[lang]['username_prompt'])
        await state.update_data(update_field="username")
    else:
        await message.reply("Invalid choice.")
        await state.clear()
        return

@dp.message(Register.update_profile_field, F.contact)
async def update_phone_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("update_field") != "phone":
        return
    lang = get_lang(message.from_user.id)
    phone = clean_phone_number(message.contact.phone_number)
    if phone:
        if update_user_field(message.from_user.id, "phone", phone):
            await message.answer(LANGUAGES[lang]['update_success'])
        else:
            await message.answer(LANGUAGES[lang]['update_failed'].format("DB"))
    else:
        await message.reply(LANGUAGES[lang]['phone_invalid'])
    await state.clear()

@dp.message(Register.update_profile_field)
async def process_update_input(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data.get("update_field")
    lang = get_lang(message.from_user.id)
    text = message.text.strip()
    if field == "full_name":
        if len(text.split()) < 2:
            await message.reply(LANGUAGES[lang]['full_name_invalid'])
            return
        value = text
    elif field == "age":
        try:
            value = int(text)
            if not MIN_AGE <= value <= MAX_AGE:
                await message.reply(LANGUAGES[lang]['age_invalid'])
                return
        except ValueError:
            await message.reply(LANGUAGES[lang]['age_invalid'])
            return
    elif field == "username":
        if not re.match(USERNAME_REGEX, text):
            await message.reply(LANGUAGES[lang]['username_invalid'])
            return
        value = text
    else:
        await state.clear()
        return
    if update_user_field(message.from_user.id, field, value):
        await message.answer(LANGUAGES[lang]['update_success'])
    else:
        await message.answer(LANGUAGES[lang]['update_failed'].format("DB"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_user_search'], LANGUAGES['ru']['admin_user_search'], LANGUAGES['en']['admin_user_search']]))
async def admin_user_search(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['search_user_prompt'])
    await state.set_state(Register.search_user)

@dp.message(Register.search_user)
async def process_user_search(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    query = message.text.strip()
    users = search_user(query)
    if not users:
        await message.answer(LANGUAGES[lang]['no_user_found'])
    else:
        info = "\n".join([LANGUAGES[lang]['user_info'].format(f"ID: {u['user_id']}, Name: {u['full_name']}, Verified: {u['verified']}") for u in users])
        await message.answer(info)
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_announce'], LANGUAGES['ru']['admin_announce'], LANGUAGES['en']['admin_announce']]))
async def admin_announce(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['announce_prompt'])
    await state.set_state(Register.announce)

@dp.message(Register.announce)
async def process_announce(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    text = message.text
    if await send_message_safe(GROUP_ID, text):
        await message.answer(LANGUAGES[lang]['announce_success'])
    else:
        await message.answer(LANGUAGES[lang]['broadcast_failed'].format("Group send error"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['poll_create'], LANGUAGES['ru']['poll_create'], LANGUAGES['en']['poll_create']]))
async def create_poll(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['poll_prompt'])
    await state.set_state(Register.poll)

@dp.message(Register.poll)
async def process_poll(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    text = message.text
    pattern = r"Savol: (.+)\n((?:.+\n?)+)" if lang == 'uz' else r"Вопрос: (.+)\n((?:.+\n?)+)" if lang == 'ru' else r"Question: (.+)\n((?:.+\n?)+)"
    match = re.match(pattern, text, re.DOTALL)
    if not match:
        await message.reply("Invalid format.")
        return
    question, options_str = match.groups()
    options = [o.strip() for o in options_str.split('\n') if o.strip()]
    if len(options) < 2:
        await message.reply("At least 2 options required.")
        return
    try:
        await bot.send_poll(GROUP_ID, question, options)
        await message.answer(LANGUAGES[lang]['poll_success'])
    except Exception as e:
        await message.answer(LANGUAGES[lang]['poll_failed'].format(str(e)))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['event_schedule'], LANGUAGES['ru']['event_schedule'], LANGUAGES['en']['event_schedule']]))
async def schedule_event(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['event_prompt'])
    await state.set_state(Register.event)

@dp.message(Register.event)
async def process_event(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    parts = message.text.split('\n')
    if len(parts) < 3:
        await message.reply("Format: Name\nTime\nDescription")
        return
    name, event_date, description = parts[0].strip(), parts[1].strip(), '\n'.join(parts[2:]).strip()
    if save_event(name, description, event_date):
        await message.answer(LANGUAGES[lang]['event_success'])
    else:
        await message.answer(LANGUAGES[lang]['error'].format("DB"))
    await state.clear()

@dp.message(Command("events"))
async def list_events(message: Message, state: FSMContext):
    if not is_private_chat(message):
        return
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    events = get_events()
    if not events:
        await message.answer(LANGUAGES[lang]['no_events'])
    else:
        event_list = "\n".join([f"{ev['name']}: {ev['description']} - {ev['event_date']}" for ev in events])
        await message.answer(LANGUAGES[lang]['event_list'].format(event_list))

@dp.message(F.text.in_([LANGUAGES['uz']['reminder_set'], LANGUAGES['ru']['reminder_set'], LANGUAGES['en']['reminder_set']]))
async def set_reminder(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['reminder_prompt'])
    await state.set_state(Register.reminder)

@dp.message(Register.reminder)
async def process_reminder(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    parts = message.text.split('\n')
    if len(parts) < 2:
        await message.reply("Format: Text\nTime (seconds)")
        return
    text, seconds_str = parts[0].strip(), parts[1].strip()
    try:
        seconds = int(seconds_str)
        await message.answer(LANGUAGES[lang]['reminder_success'])
        await asyncio.sleep(seconds)
        await send_message_safe(user_id, text)
    except ValueError:
        await message.reply("Invalid time.")
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['feedback_prompt'], LANGUAGES['ru']['feedback_prompt'], LANGUAGES['en']['feedback_prompt']]))
async def feedback_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['feedback_prompt'])
    await state.set_state(Register.feedback)

@dp.message(Register.feedback)
async def process_feedback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    text = message.text.strip()
    if save_feedback(user_id, text):
        await message.answer(LANGUAGES[lang]['feedback_success'])
    else:
        await message.answer(LANGUAGES[lang]['error'].format("DB"))
    await state.clear()

@dp.message(F.text.in_([LANGUAGES['uz']['admin_view_feedback'], LANGUAGES['ru']['admin_view_feedback'], LANGUAGES['en']['admin_view_feedback']]))
async def view_feedback(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    feedback = get_feedback()
    if not feedback:
        await message.answer(LANGUAGES[lang]['no_feedback'])
    else:
        fb_list = "\n".join([f"User {fb['user_id']}: {fb['feedback_text']} ({fb['feedback_date']})" for fb in feedback])
        await message.answer(LANGUAGES[lang]['feedback_list'].format(fb_list))

@dp.message(F.text.in_([LANGUAGES['uz']['admin_backup_db'], LANGUAGES['ru']['admin_backup_db'], LANGUAGES['en']['admin_backup_db']]))
async def backup_db_handler(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    backup_path = backup_db()
    if backup_path:
        await message.answer_document(FSInputFile(backup_path), caption=LANGUAGES[lang]['backup_success'])
        os.remove(backup_path)
    else:
        await message.answer(LANGUAGES[lang]['backup_failed'].format("Error"))

@dp.message(F.text.in_([LANGUAGES['uz']['admin_restore_db'], LANGUAGES['ru']['admin_restore_db'], LANGUAGES['en']['admin_restore_db']]))
async def restore_db_handler(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['restore_prompt'])
    await state.set_state(Register.restore)

@dp.message(Register.restore, F.document)
async def process_restore(message: Message, state: FSMContext):
    if message.from_user.username != ADMIN_USERNAME:
        return
    lang = get_lang(message.from_user.id)
    document = message.document
    backup_path = await bot.download(document, destination=f"restore_{document.file_id}.db")
    if restore_db(backup_path.name):
        await message.answer(LANGUAGES[lang]['restore_success'])
    else:
        await message.answer(LANGUAGES[lang]['restore_failed'].format("File error"))
    os.remove(backup_path.name)
    await state.clear()

@dp.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def on_user_join(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    lang = get_lang(user.id) or 'uz'
    dm_text = LANGUAGES[lang]['verification_needed']
    await send_dm_or_group_notice(user.id, dm_text, event.chat.id, user.username, user.first_name, lang)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=LANGUAGES[lang]['start_verify'])]],
        resize_keyboard=True
    )
    await send_message_safe(user.id, LANGUAGES[lang]['welcome'], kb)
    save_user(user.id, join_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dp.message(F.chat.type != "private")
async def prevent_group_messages(message: Message):
    user_id = message.from_user.id
    if await is_user_verified(user_id):
        return
    lang = get_lang(user_id)
    await send_dm_or_group_notice(user_id, LANGUAGES[lang]['verification_needed'], message.chat.id, message.from_user.username, message.from_user.first_name, lang)
    await send_membership_notice(user_id, lang)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.error(f"Delete message error: {str(e)}")

@dp.message(F.text.in_([LANGUAGES['uz']['start_verify'], LANGUAGES['ru']['start_verify'], LANGUAGES['en']['start_verify']]))
async def start_verify(message: Message, state: FSMContext):
    if not is_private_chat(message):
        return
    user_id = message.from_user.id
    lang = get_lang(user_id)
    captcha_text, captcha_answer = generate_captcha()  # async emas, to'g'rilandi
    await message.answer(LANGUAGES[lang]['captcha_prompt'].format(captcha_text))
    await state.set_state(Register.captcha)
    await state.update_data(captcha_answer=captcha_answer)

@dp.message(Register.captcha)
async def process_captcha(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(message.from_user.id)
    try:
        answer = int(message.text.strip())
        if answer == data['captcha_answer']:
            await message.answer(LANGUAGES[lang]['captcha_success'])
            await message.answer(LANGUAGES[lang]['full_name_prompt'])
            await state.set_state(Register.full_name)
        else:
            await message.reply(LANGUAGES[lang]['captcha_invalid'])
            await state.clear()
    except ValueError:
        await message.reply(LANGUAGES[lang]['captcha_invalid'])
        await state.clear()

@dp.message(Register.full_name)
async def get_name(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    text = message.text.strip()
    if len(text.split()) < 2:
        await message.reply(LANGUAGES[lang]['full_name_invalid'])
        return
    await state.update_data(full_name=text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['phone_prompt'], reply_markup=kb)
    await state.set_state(Register.phone)

@dp.message(Register.phone, F.contact)
async def get_phone_contact(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    phone = clean_phone_number(message.contact.phone_number)
    if phone:
        await state.update_data(phone=phone)
        await message.answer(LANGUAGES[lang]['age_prompt'], reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Register.age)
    else:
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
        await message.reply(LANGUAGES[lang]['phone_invalid'], reply_markup=kb)

@dp.message(Register.age)
async def get_age(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    try:
        age = int(message.text.strip())
        if MIN_AGE <= age <= MAX_AGE:
            await state.update_data(age=age)
            await message.answer(LANGUAGES[lang]['username_prompt'])
            await state.set_state(Register.username)
        else:
            await message.reply(LANGUAGES[lang]['age_invalid'])
    except ValueError:
        await message.reply(LANGUAGES[lang]['age_invalid'])

@dp.message(Register.username)
async def get_username(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    username = message.text.strip()
    if re.match(USERNAME_REGEX, username):
        await state.update_data(username=username)
        await complete_verification(message, state)
    else:
        await message.reply(LANGUAGES[lang]['username_invalid'])

async def complete_verification(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = get_lang(message.from_user.id)
    user_id = message.from_user.id
    join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_user(
        user_id, data['full_name'], data['phone'], data['age'], data['username'], join_date, verified=True, language=lang
    )
    post_text = f"New user verified:\nName: {data['full_name']}\nPhone: {data['phone']}\nAge: {data['age']}\nUsername: {data['username']}\nID: {user_id}\nDate: {join_date}"
    await bot.send_message(SECRET_CHANNEL, post_text)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Join Group")],
            [KeyboardButton(text="📢 Join Channel")],
            [KeyboardButton(text=LANGUAGES[lang]['mods_menu'])],
        ],
        resize_keyboard=True
    )
    await message.answer(LANGUAGES[lang]['verification_complete'], reply_markup=kb)
    await state.clear()

@dp.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id)
    await message.answer(LANGUAGES[lang]['help'])

@dp.message(Command("weather"))
async def weather_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        lang = get_lang(user_id)
        await message.answer(LANGUAGES[lang]['verification_needed'])
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['weather_prompt'])
    await state.set_state(Register.weather)

@dp.message(Register.weather)
async def process_weather(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    city = message.text.strip()
    weather_data = await get_weather(city)
    if weather_data:
        temp, condition, humidity = weather_data
        await message.answer(LANGUAGES[lang]['weather_info'].format(city, temp, condition, humidity))
    else:
        await message.answer(LANGUAGES[lang]['weather_error'])
    await state.clear()

@dp.message(Command("calculator"))
async def calculator_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        lang = get_lang(user_id)
        await message.answer(LANGUAGES[lang]['verification_needed'])
        return
    lang = get_lang(user_id)
    await message.answer(LANGUAGES[lang]['calculator_prompt'])
    await state.set_state(Register.calculator)

@dp.message(Register.calculator)
async def process_calculator(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    expr = message.text.strip()
    result = calculate_expression(expr)
    if result is not None:
        await message.answer(LANGUAGES[lang]['calculator_result'].format(result))
    else:
        await message.answer(LANGUAGES[lang]['calculator_error'])
    await state.clear()

@dp.message(Command("news"))
async def news_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not await is_user_verified(user_id):
        lang = get_lang(user_id)
        await message.answer(LANGUAGES[lang]['verification_needed'])
        return
    lang = get_lang(user_id)
    news = await get_news()
    if news:
        await message.answer(LANGUAGES[lang]['news_prompt'] + "\n" + news)
    else:
        await message.answer(LANGUAGES[lang]['news_error'])

@dp.message()
async def catch_all(message: Message, state: FSMContext):
    if not is_private_chat(message):
        return
    lang = get_lang(message.from_user.id)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=LANGUAGES[lang]['start_verify'])],
            [KeyboardButton(text=LANGUAGES[lang]['mods_menu'])],
            [KeyboardButton(text=LANGUAGES[lang]['admin_panel'])] if message.from_user.username == ADMIN_USERNAME else [],
        ],
        resize_keyboard=True
    )
    await message.answer("Unknown command. Use /help.", reply_markup=kb)

# ================= MAIN =================
async def main():
    dp.message.middleware(RateLimitMiddleware())
    dp.chat_member.middleware(RateLimitMiddleware())
    await dp.start_polling(bot, on_startup=on_startup)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
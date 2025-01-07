from flask import Flask, jsonify, request
from telethon import TelegramClient
import asyncio
from colorama import Fore, Style, init
import os
from dotenv import load_dotenv
from threading import Thread

# Inisialisasi Flask
app = Flask('')

@app.route('/')
def home():
    """Endpoint default untuk memeriksa status bot."""
    return "Telegram Bot is running!"

@app.route('/send_message', methods=['POST'])
def send_message_api():
    """Endpoint untuk mengirim pesan ke grup tertentu melalui API."""
    data = request.json
    group_name = data.get('group_name')
    message = data.get('message')

    if not group_name or not message:
        return jsonify({"error": "Nama grup dan pesan wajib diisi."}), 400

    async def send_to_group():
        try:
            group = await client.get_entity(group_name)
            await client.send_message(group, message)
            return jsonify({"success": f"Pesan terkirim ke grup {group_name}."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    asyncio.run(send_to_group())
    return jsonify({"message": "Pesan sedang diproses."})

def run_flask():
    """Jalankan server Flask di thread terpisah."""
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """Jaga Flask tetap aktif."""
    t = Thread(target=run_flask, daemon=True)
    t.start()

# Inisialisasi Colorama untuk warna terminal
init(autoreset=True)

# Muat variabel lingkungan dari file .env
load_dotenv()

# Fungsi utilitas
def clear():
    """Hapus layar terminal."""
    if os.name == 'nt':
        os.system('cls')  # Windows
    else:
        os.system('clear')  # Unix/Linux/macOS

def print_logo():
    """Cetak logo aplikasi."""
    print(Fore.YELLOW + Style.BRIGHT + r"""
▄▀█ █░█ ▀█▀ █▀█   █▀ █▀▀ █▄░█ █▀▄ █▀▀ █▀█
█▀█ █▄█ ░█░ █▄█   ▄█ ██▄ █░▀█ █▄▀ ██▄ █▀▄
""" + Fore.CYAN + Style.BRIGHT + r"""
       Coded by @forumkt
""")

def get_env_variable(var_name, prompt, is_numeric=False):
    """
    Ambil variabel dari .env, atau minta input pengguna jika tidak ditemukan.
    """
    value = os.getenv(var_name)
    if value is None or value.strip() == "":
        clear()  # Bersihkan layar sebelum input
        while True:
            value = input(f"{prompt}: ").strip()
            if not value:
                print(Fore.RED + Style.BRIGHT + "Input tidak boleh kosong. Silakan coba lagi.")
                continue
            if is_numeric and not value.isdigit():
                print(Fore.RED + Style.BRIGHT + "Input harus berupa angka. Silakan coba lagi.")
                continue
            # Simpan ke .env
            with open('.env', 'a') as env_file:
                env_file.write(f"{var_name}={value}\n")
            break
    return int(value) if is_numeric else value

# Konfigurasi utama dari .env
api_id = get_env_variable('API_ID', 'Masukkan API ID', is_numeric=True)
api_hash = get_env_variable('API_HASH', 'Masukkan API Hash')
phone_number = get_env_variable('PHONE_NUMBER', 'Masukkan Nomor Telepon')
sender_username = get_env_variable('SENDER_USERNAME', 'Masukkan Username Pengirim')
group_count = get_env_variable('GROUP_COUNT', 'Masukkan Jumlah Grup untuk Mengirim Pesan', is_numeric=True)
interval_minutes = get_env_variable('INTERVAL_MINUTES', 'Masukkan Interval Waktu Pengiriman Pesan (menit)', is_numeric=True)

# Inisialisasi Telegram Client
client = TelegramClient('session_name', api_id, api_hash)

# Fungsi Telegram
async def get_last_message(client, username):
    """Ambil pesan terakhir dari pengguna tertentu."""
    try:
        user = await client.get_entity(username)
        messages = await client.get_messages(user, limit=1)
        return messages[0].text if messages else None
    except Exception as e:
        print(Fore.RED + f"Gagal mendapatkan pesan dari {username}: {e}")
        return None

async def get_groups(client):
    """Dapatkan daftar grup dari akun."""
    try:
        dialogs = await client.get_dialogs()
        return [dialog.entity for dialog in dialogs if dialog.is_group]
    except Exception as e:
        print(Fore.RED + f"Gagal mendapatkan grup: {e}")
        return []

async def send_message(client, group, message):
    """Kirim pesan ke grup."""
    try:
        await client.send_message(group, message)
        print(Fore.GREEN + f"Pesan terkirim ke grup {group.title}")
    except Exception as e:
        print(Fore.RED + f"Gagal mengirim pesan ke grup {group.title}: {e}")

# Alur utama pengiriman pesan
async def send_messages_periodically(client):
    """Kirim pesan ke grup dalam interval tertentu."""
    interval_seconds = interval_minutes * 60
    while True:
        clear()
        await print_logo_and_account_info(client)

        # Ambil pesan terbaru
        message = await get_last_message(client, sender_username)
        if not message:
            print(Fore.YELLOW + f"Tidak ada pesan terbaru dari {sender_username}.")
            await asyncio.sleep(10)
            continue

        # Ambil grup
        groups = await get_groups(client)
        if not groups:
            print(Fore.RED + "Tidak ada grup yang ditemukan.")
            break

        # Batasi jumlah grup
        selected_groups = groups[:min(group_count, len(groups))]

        for group in selected_groups:
            await send_message(client, group, message)
            await asyncio.sleep(6)  # Jeda antar pesan

        print(Fore.CYAN + f"Menunggu {interval_minutes} menit sebelum pengiriman berikutnya...")
        await asyncio.sleep(interval_seconds)

async def print_logo_and_account_info(client):
    """Cetak logo dan informasi akun."""
    print_logo()
    try:
        me = await client.get_me()
        print(Fore.YELLOW + f"Username: {me.username or 'Tidak ada username'}")
        print(Fore.YELLOW + f"Nomor Telepon: {me.phone or 'Tidak ada nomor telepon'}")
    except Exception as e:
        print(Fore.RED + f"Gagal mendapatkan informasi akun: {e}")

async def main():
    """Jalankan bot Telegram."""
    await client.start(phone_number)
    print(Fore.WHITE + "Bot aktif, siap mengirim pesan...")
    await asyncio.gather(
        send_messages_periodically(client)
    )

# Jalankan aplikasi
if __name__ == '__main__':
    # Jaga Flask tetap aktif
    keep_alive()

    # Jalankan Telegram bot
    asyncio.run(main())

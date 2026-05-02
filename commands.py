import discord
import os
from discord.ext import commands
from discord import app_commands
import json

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Команды синхронизированы!")

bot = MyBot()

@bot.tree.command(name="say", description="Сырая отправка JSON (Идеальная копия Discohook)")
@app_commands.describe(json_code="Код JSON", file="Файл .txt/.json с кодом")
@app_commands.default_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, json_code: str = None, file: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    try:
        # 1. Достаем сырой текст
        raw_data = ""
        if file:
            raw_data = (await file.read()).decode('utf-8')
        elif json_code:
            raw_data = json_code
        else:
            return await interaction.followup.send("❌ Передай код или файл!", ephemeral=True)
            
        data = json.loads(raw_data.strip())
        
        # 2. Формируем чистый payload для API Дискорда
        # Забираем только то, что нужно для отправки сообщения, отсекая мусор Дискохука
        payload = {
            "content": data.get("content", ""),
            "embeds": data.get("embeds", []),
            "components": data.get("components", []),
            "flags": data.get("flags", 0)
        }

        # 3. МАГИЯ: Отправляем запрос НАПРЯМУЮ в Discord API в обход discord.py
        # Это заставит Discord отрендерить Контейнеры, Галереи и Разделители точь-в-точь как в вебхуке
        route = discord.http.Route('POST', f'/channels/{interaction.channel_id}/messages')
        await bot.http.request(route, json=payload)

        await interaction.followup.send("✅ Сообщение отправлено идеально!", ephemeral=True)

    except json.JSONDecodeError:
        await interaction.followup.send("❌ Ошибка: кривой JSON формат.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка API: `{e}`", ephemeral=True)
@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 Пинг: `{round(bot.latency * 1000)} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

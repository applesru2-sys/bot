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

@bot.tree.command(name="say", description="Отправить сообщение (копия макета Discohook)")
@app_commands.describe(json_code="Код JSON", file="Файл с кодом")
@app_commands.default_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, json_code: str = None, file: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    try:
        raw_data = ""
        if file:
            raw_data = (await file.read()).decode('utf-8')
        elif json_code:
            raw_data = json_code
        else:
            return await interaction.followup.send("❌ Передай код или файл!", ephemeral=True)
            
        data = json.loads(raw_data.strip())
        content = data.get("content")
        embeds_to_send = []
        
        # Цвет темной темы Discord (чтобы полоска слева была почти невидимой)
        DEFAULT_COLOR = 0x2b2d31 

        # 1. Сначала ищем медиа (Type 12) — это будет ПЕРВЫЙ эмбед (картинка сверху)
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    if comp.get("type") == 12:
                        for item in comp.get("items", []):
                            url = item.get("media", {}).get("url")
                            if url:
                                img_e = discord.Embed(color=DEFAULT_COLOR)
                                img_e.set_image(url=url)
                                embeds_to_send.append(img_e)

        # 2. Обрабатываем текстовые блоки и разделители
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    # Тип 10 — Текстовые блоки
                    if comp.get("type") == 10:
                        text = comp.get("content", "")
                        if text.strip():
                            # Создаем новый эмбед для каждого блока, чтобы были отступы
                            embeds_to_send.append(discord.Embed(description=text, color=DEFAULT_COLOR))
                    
                    # Тип 14 — Разделители (тонкие линии)
                    elif comp.get("type") == 14:
                        if embeds_to_send:
                            last_e = embeds_to_send[-1]
                            # Используем символ длинной черты для имитации разделителя
                            line = "\n" + "⎯" * 32 
                            if last_e.description is None: last_e.description = line
                            else: last_e.description += line

        # 3. Добавляем классические эмбеды (если они есть в JSON)
        for e_dict in data.get("embeds", []):
            embeds_to_send.append(discord.Embed.from_dict(e_dict))

        # Discord позволяет отправить до 10 эмбедов в одном сообщении
        # Они будут склеены визуально в одну длинную колонку
        await interaction.channel.send(content=content, embeds=embeds_to_send[:10])
        await interaction.followup.send("✅ Сообщение отправлено!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка парсинга: `{e}`", ephemeral=True)
@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 Пинг: `{round(bot.latency * 1000)} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

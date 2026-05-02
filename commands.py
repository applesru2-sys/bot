import discord
import os
from discord.ext import commands
from discord import app_commands
import json
import io

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Команды синхронизированы!")

bot = MyBot()

@bot.tree.command(name="say", description="Отправить сообщение (поддержка Layouts)")
@app_commands.describe(json_code="JSON код", file="Или файл с кодом")
async def say(interaction: discord.Interaction, json_code: str = None, file: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)
    try:
        raw_data = ""
        if file:
            raw_data = (await file.read()).decode('utf-8')
        elif json_code:
            raw_data = json_code
            
        data = json.loads(raw_data.strip())
        content = data.get("content")
        embeds_to_send = []

        # 1. Сначала обрабатываем стандартные эмбеды (если они есть)
        for e_dict in data.get("embeds", []):
            embeds_to_send.append(discord.Embed.from_dict(e_dict))

        # 2. Обработка Layouts (как на фото 1)
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    # Тип 10 — это текстовые блоки (заголовки и описания)
                    if comp.get("type") == 10:
                        text = comp.get("content", "")
                        # Если это заголовок (короткий текст в рамке на фото 1)
                        # Мы можем выделить его жирным или в отдельный эмбед
                        if embeds_to_send:
                            # Добавляем текст в последний эмбед, если он уже есть
                            last_embed = embeds_to_send[-1]
                            if not last_embed.description:
                                last_embed.description = text
                            else:
                                last_embed.description += f"\n\n{text}"
                        else:
                            # Создаем новый эмбед для этого блока
                            embeds_to_send.append(discord.Embed(description=text, color=0x2b2d31))

                    # Тип 12 — Медиа (картинка сверху)
                    elif comp.get("type") == 12:
                        for item in comp.get("items", []):
                            url = item.get("media", {}).get("url")
                            if url:
                                if embeds_to_send:
                                    embeds_to_send[0].set_image(url=url)
                                else:
                                    e = discord.Embed(color=0x2b2d31)
                                    e.set_image(url=url)
                                    embeds_to_send.append(e)
                    
                    # Тип 14 — Разделители (линии)
                    elif comp.get("type") == 14:
                        if embeds_to_send:
                            embeds_to_send[-1].description += "\n\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"

        await interaction.channel.send(content=content, embeds=embeds_to_send[:10])
        await interaction.followup.send("✅ Сообщение отправлено!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{e}`", ephemeral=True)

@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    ping = round(bot.latency * 1000)
    await interaction.response.send_message(f"🟢 Пинг: `{ping} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

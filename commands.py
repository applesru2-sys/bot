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

@bot.tree.command(name="say", description="Отправить сообщение (максимальное сходство)")
@app_commands.describe(json_code="JSON код", file="Или файл с кодом")
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
        media_url = None
        DEFAULT_COLOR = 0x2b2d31 

        # 1. Сначала ищем URL картинки в компонентах
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    if comp.get("type") == 12: # Media
                        for item in comp.get("items", []):
                            media_url = item.get("media", {}).get("url")

        # 2. Обрабатываем текстовые блоки
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    # Текстовые блоки (Type 10)
                    if comp.get("type") == 10:
                        text = comp.get("content", "")
                        if text.strip():
                            # Создаем эмбед для текста
                            new_e = discord.Embed(description=text, color=DEFAULT_COLOR)
                            
                            # Если мы нашли картинку ранее, прикрепляем её К ПЕРВОМУ текстовому эмбеду
                            if media_url and not any(e.image.url for e in embeds_to_send):
                                new_e.set_image(url=media_url)
                            
                            embeds_to_send.append(new_e)

                    # Разделители (Type 14)
                    elif comp.get("type") == 14:
                        if embeds_to_send:
                            last_e = embeds_to_send[-1]
                            line = "\n" + "⎯" * 35 
                            if last_e.description is None:
                                last_e.description = line
                            else:
                                last_e.description += line

        # Если в JSON были обычные эмбеды, добавляем их
        for e_dict in data.get("embeds", []):
            embeds_to_send.append(discord.Embed.from_dict(e_dict))

        if not content and not embeds_to_send:
            return await interaction.followup.send("❌ Сообщение пустое!", ephemeral=True)

        # Отправляем (максимум 10 эмбедов)
        await interaction.channel.send(content=content, embeds=embeds_to_send[:10])
        await interaction.followup.send("✅ Сообщение отправлено!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{e}`", ephemeral=True)
@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 Пинг: `{round(bot.latency * 1000)} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

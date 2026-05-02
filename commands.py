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

@bot.tree.command(name="say", description="Все в одном эмбеде (картинка + текст)")
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
        
        # Переменные для сборки ОДНОГО эмбеда
        full_description = ""
        media_url = None
        DEFAULT_COLOR = 0x2b2d31 

        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    # Собираем ТЕКСТ
                    if comp.get("type") == 10:
                        text = comp.get("content", "")
                        if text.strip():
                            # Добавляем текст к общему описанию
                            full_description += text + "\n\n"

                    # Ищем КАРТИНКУ
                    elif comp.get("type") == 12:
                        for item in comp.get("items", []):
                            media_url = item.get("media", {}).get("url")

                    # Добавляем РАЗДЕЛИТЕЛЬ
                    elif comp.get("type") == 14:
                        full_description += "⎯" * 35 + "\n\n"

        # Создаем ОДИН эмбед
        final_embed = discord.Embed(
            description=full_description.strip(), 
            color=DEFAULT_COLOR
        )
        
        # Если нашли картинку — ставим её (она будет под текстом в том же блоке)
        if media_url:
            final_embed.set_image(url=media_url)

        # Добавляем классические эмбеды из секции "embeds", если они были
        all_embeds = [final_embed]
        for e_dict in data.get("embeds", []):
            all_embeds.append(discord.Embed.from_dict(e_dict))

        # Проверка на пустоту
        if not content and not full_description and not media_url:
            return await interaction.followup.send("❌ JSON не содержит данных для отправки.", ephemeral=True)

        await interaction.channel.send(content=content, embeds=all_embeds[:10])
        await interaction.followup.send("✅ Успешно отправлено!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{e}`", ephemeral=True)
@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 Пинг: `{round(bot.latency * 1000)} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

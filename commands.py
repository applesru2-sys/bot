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

@bot.tree.command(name="say", description="Отправить сообщение из JSON кода или файла")
@app_commands.describe(
    json_code="Вставьте JSON код здесь (если он короткий)",
    file="Или прикрепите .txt/.json файл (если код очень длинный)"
)
@app_commands.default_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, json_code: str = None, file: discord.Attachment = None):
    await interaction.response.defer(ephemeral=True)

    try:
        raw_data = ""

        # 1. Сначала проверяем, прикреплен ли файл
        if file:
            # Читаем содержимое файла
            file_bytes = await file.read()
            raw_data = file_bytes.decode('utf-8')
        # 2. Если файла нет, берем текст из поля ввода
        elif json_code:
            raw_data = json_code
        else:
            return await interaction.followup.send("❌ Вы не ввели код и не прикрепили файл!", ephemeral=True)

        # Парсим JSON
        data = json.loads(raw_data.strip())
        
        content = data.get("content")
        embeds_to_send = []

        # Извлекаем стандартные эмбеды
        embeds_list = data.get("embeds", [])
        for e_dict in embeds_list:
            cleaned_embed = {k: v for k, v in e_dict.items() if v is not None}
            embeds_to_send.append(discord.Embed.from_dict(cleaned_embed))

        # Логика для Discohook Layouts (твои компоненты)
        if "components" in data:
            for comp_group in data["components"]:
                for sub_comp in comp_group.get("components", []):
                    # Текстовые блоки (тип 10)
                    if "content" in sub_comp:
                        txt = sub_comp["content"]
                        if len(txt) > 200 or embeds_to_send:
                            embeds_to_send.append(discord.Embed(description=txt, color=0x9b59b6))
                        else:
                            content = txt
                    
                    # Медиа блоки (картинки, тип 12)
                    if "items" in sub_comp:
                        for item in sub_comp["items"]:
                            if "media" in item and "url" in item["media"]:
                                url = item["media"]["url"]
                                if embeds_to_send:
                                    embeds_to_send[0].set_image(url=url)
                                else:
                                    embeds_to_send.append(discord.Embed().set_image(url=url))

        if not content and not embeds_to_send:
            return await interaction.followup.send("❌ В JSON не найдено подходящих данных для отправки.", ephemeral=True)

        # Отправляем в канал
        await interaction.channel.send(content=content, embeds=embeds_to_send[:10])
        await interaction.followup.send("✅ Успешно отправлено!", ephemeral=True)

    except json.JSONDecodeError:
        await interaction.followup.send("❌ Ошибка: Неверный формат JSON. Проверьте скобки.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Произошла ошибка: `{str(e)}`", ephemeral=True)

@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    ping = round(bot.latency * 1000)
    await interaction.response.send_message(f"🟢 Пинг: `{ping} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

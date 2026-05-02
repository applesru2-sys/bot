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

@bot.tree.command(name="say", description="Отправить сообщение (максимальное сходство с Discohook)")
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

        # Цвет фона как в Discord (темно-серый), чтобы не было ярких полосок
        DEFAULT_COLOR = 0x2b2d31 

        # 1. Сначала стандартные эмбеды
        for e_dict in data.get("embeds", []):
            embeds_to_send.append(discord.Embed.from_dict(e_dict))

        # 2. Обработка Layouts
        if "components" in data:
            for row in data["components"]:
                for comp in row.get("components", []):
                    
                    # --- ТЕКСТОВЫЕ БЛОКИ (Type 10) ---
                    if comp.get("type") == 10:
                        text = comp.get("content", "")
                        if not text.strip(): continue

                        # Чтобы блоки не слипались, создаем ДЛЯ КАЖДОГО новый эмбед
                        # Это создаст визуальные отступы между секциями, как на фото 1
                        new_e = discord.Embed(description=text, color=DEFAULT_COLOR)
                        embeds_to_send.append(new_e)

                    # --- МЕДИА (Type 12) ---
                    elif comp.get("type") == 12:
                        for item in comp.get("items", []):
                            url = item.get("media", {}).get("url")
                            if url:
                                # Картинку вешаем на самый первый эмбед в списке
                                if embeds_to_send:
                                    embeds_to_send[0].set_image(url=url)
                                else:
                                    e = discord.Embed(color=DEFAULT_COLOR)
                                    e.set_image(url=url)
                                    embeds_to_send.append(e)
                    
                    # --- РАЗДЕЛИТЕЛИ (Type 14) ---
                    elif comp.get("type") == 14:
                        # Если есть предыдущий эмбед, просто добавляем черту в конец
                        if embeds_to_send:
                            # Используем специальный символ длинной черты
                            line = "\n" + "⎯" * 35 
                            if embeds_to_send[-1].description:
                                embeds_to_send[-1].description += line

        # Discord разрешает до 10 эмбедов в одном сообщении
        final_embeds = embeds_to_send[:10]

        if not content and not final_embeds:
            return await interaction.followup.send("❌ Сообщение пустое!", ephemeral=True)

        await interaction.channel.send(content=content, embeds=final_embeds)
        await interaction.followup.send("✅ Сообщение успешно отправлено!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{e}`", ephemeral=True)

@bot.tree.command(name="status", description="Проверка пинга")
async def status_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 Пинг: `{round(bot.latency * 1000)} мс`", ephemeral=True)

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)

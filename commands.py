import discord
import os
from discord.ext import commands
from discord import app_commands
import json

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Глобальная синхронизация
        await self.tree.sync()
        print("Команды синхронизированы!")


bot = MyBot()


@bot.tree.command(name="say", description="Отправить эмбед из JSON (формат Discohook)")
@app_commands.describe(json_code="Вставьте JSON код целиком")
@app_commands.default_permissions(manage_messages=True)
async def say(interaction: discord.Interaction, json_code: str):
    await interaction.response.defer(ephemeral=True)

    try:
        data = json.loads(json_code.strip())
        content = data.get("content")
        embeds_to_send = []

        # 1. Пытаемся извлечь стандартные эмбеды
        embeds_list = data.get("embeds", [])
        for e_dict in embeds_list:
            cleaned_embed = {k: v for k, v in e_dict.items() if v is not None}
            embeds_to_send.append(discord.Embed.from_dict(cleaned_embed))

        # 2. ОСОБАЯ ЛОГИКА ДЛЯ КОМПОНЕНТОВ (Discohook Layouts)
        # Если текста/эмбедов нет, ищем текст внутри компонентов
        if not content and not embeds_to_send and "components" in data:
            for comp_group in data["components"]:
                for sub_comp in comp_group.get("components", []):
                    # Ищем поле 'content' внутри текстовых блоков компонентов
                    if "content" in sub_comp:
                        # Если текст очень длинный, лучше отправить его в эмбеде
                        if len(sub_comp["content"]) > 100:
                            new_embed = discord.Embed(description=sub_comp["content"], color=0x9b59b6)
                            embeds_to_send.append(new_embed)
                        else:
                            content = sub_comp["content"]

        # 3. Проверка на картинку в Media компонентах
        # Если в JSON есть картинка (как в вашем примере), добавим её в эмбед
        for comp_group in data.get("components", []):
            for sub_comp in comp_group.get("components", []):
                for item in sub_comp.get("items", []):
                    if "media" in item and "url" in item["media"]:
                        if embeds_to_send:
                            embeds_to_send[0].set_image(url=item["media"]["url"])
                        else:
                            img_embed = discord.Embed().set_image(url=item["media"]["url"])
                            embeds_to_send.append(img_embed)

        if not content and not embeds_to_send:
            await interaction.followup.send("❌ Ошибка: Не удалось найти текст или эмбеды в JSON.", ephemeral=True)
            return

        await interaction.channel.send(content=content, embeds=embeds_to_send[:10])
        await interaction.followup.send("✅ Сообщение успешно отправлено!", ephemeral=True)

    except json.JSONDecodeError:
        await interaction.followup.send("❌ Ошибка синтаксиса JSON.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка: `{str(e)}`", ephemeral=True)

# --- НОВАЯ КОМАНДА СТАТУСА ---
@bot.tree.command(name="status", description="Проверить, жив ли бот и какой у него пинг")
async def status_command(interaction: discord.Interaction):
    ping = round(bot.latency * 1000)
    response_text = f"🟢 **Система работает стабильно!**\n📶 Пинг до Discord: `{ping} мс`"
    await interaction.response.send_message(response_text, ephemeral=True)


# Ловим токен из безопасного поля BotHost
TOKEN = os.environ.get("TOKEN") 

# Запуск бота 
bot.run(TOKEN)

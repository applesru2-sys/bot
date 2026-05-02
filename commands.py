import discord
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
    # 1. СРАЗУ ПРОСИМ ОТСРОЧКУ У ДИСКОРДА (защита от ошибки 404)
    await interaction.response.defer(ephemeral=True)

    try:
        # Очистка кода от возможных лишних пробелов по краям
        data = json.loads(json_code.strip())

        content = None
        embeds_to_send = []

        # Разбираем структуру Discohook
        if isinstance(data, dict):
            # 1. Извлекаем основной текст сообщения (если есть)
            content = data.get("content")
            if content == "" or content is None:
                content = None

            # 2. Извлекаем список эмбедов
            embeds_list = data.get("embeds", [])

            # Если в JSON нет ключа 'embeds', но есть поля эмбеда (title, description) в корне
            if not embeds_list and ("title" in data or "description" in data):
                embeds_list = [data]

            for e_dict in embeds_list:
                # Очищаем словарь эмбеда от пустых полей, которые могут вызвать ошибку 400
                cleaned_embed = {k: v for k, v in e_dict.items() if v is not None}

                # Создаем объект эмбеда
                embed = discord.Embed.from_dict(cleaned_embed)
                embeds_to_send.append(embed)

        # Проверка на пустоту
        if not content and not embeds_to_send:
            await interaction.followup.send("❌ Ошибка: JSON не содержит ни текста, ни эмбедов.", ephemeral=True)
            return

        # Лимит Discord — максимум 10 эмбедов в одном сообщении
        final_embeds = embeds_to_send[:10]

        # Отправляем в канал
        await interaction.channel.send(content=content, embeds=final_embeds)

        # Подтверждение автору (скрытое) через followup (так как мы брали отсрочку)
        await interaction.followup.send("✅ Сообщение успешно отправлено!", ephemeral=True)

    except json.JSONDecodeError:
        await interaction.followup.send(
            "❌ **Ошибка синтаксиса JSON.** Убедитесь, что вы скопировали код полностью со всеми скобками `{ }`.",
            ephemeral=True)
    except discord.HTTPException as e:
        await interaction.followup.send(
            f"❌ **Ошибка Discord API (400):**\n`{e.text}`\n\n*Проверьте, не превышены ли лимиты символов и все ли поля заполнены корректно.*",
            ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ **Непредвиденная ошибка:**\n`{str(e)}`", ephemeral=True)


# --- НОВАЯ КОМАНДА СТАТУСА ---
@bot.tree.command(name="status", description="Проверить, жив ли бот и какой у него пинг")
async def status_command(interaction: discord.Interaction):
    ping = round(bot.latency * 1000)
    response_text = f"🟢 **Система работает стабильно!**\n📶 Пинг до Discord: `{ping} мс`"
    await interaction.response.send_message(response_text, ephemeral=True)


# Запуск бота 
bot.run("MTQ5NDk3MzQ1MjgwMzkwMzYwMA.GxAe79.Aozg-QrJMsPjerUhdjY1yADrDA2ZumTrtYApzk")
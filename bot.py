import discord
from discord.ext import commands
import os
import time

# 환경변수에서 읽기
TOKEN = os.getenv("TOKEN")
GUILD_ID_A = int(os.getenv("GUILD_ID_A"))
GUILD_ID_B = int(os.getenv("GUILD_ID_B"))
WEBHOOK_CHANNEL_ID = int(os.getenv("WEBHOOK_CHANNEL_ID"))
OPEN_CHANNEL_ID = int(os.getenv("OPEN_CHANNEL_ID"))

# Intents 설정
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 매물 메시지 가공 함수
def clean_mamul_message(original_message):
    lines = original_message.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() == "📝 매물 신청이 들어왔습니다!":
            continue
        if line.startswith("- 게임 아이디:") or line.startswith("- 게임 비밀번호:"):
            continue
        if line.startswith("- 가격:"):
            price_text = line.split(':', 1)[1].strip()
            price_text = price_text.replace(',', '').replace('원', '')
            try:
                price = int(price_text)
                discounted_price = int(price * 0.7)
                line = f"- 가격: {discounted_price:,}원"
            except:
                pass
        new_lines.append(line)
    return '\n'.join(new_lines)

def clean_mamul_message2(original_message):
    lines = original_message.split('\n')
    new_lines = []
    for line in lines:
        if line.strip() == "📝 매물 신청이 들어왔습니다!":
            continue
        if line.startswith("- 가격:"):
            price_text = line.split(':', 1)[1].strip()
            price_text = price_text.replace(',', '').replace('원', '')
            try:
                price = int(price_text)
                discounted_price = int(price * 0.7)
                line = f"- 가격: {discounted_price:,}원"
            except:
                pass
        new_lines.append(line)
    return '\n'.join(new_lines)

saved_original_messages = {}
claimed_messages = set()
rejected_users = set()

@bot.event
async def on_ready():
    print(f'{bot.user} 봇이 켜졌습니다!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == WEBHOOK_CHANNEL_ID:
        await message.add_reaction('✅')

    await bot.process_commands(message)  # 명령어 사용 가능하게 추가!

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.channel.id == WEBHOOK_CHANNEL_ID and str(reaction.emoji) == '✅':
        guild_b = bot.get_guild(GUILD_ID_B)
        open_channel = guild_b.get_channel(OPEN_CHANNEL_ID)

        original_message = reaction.message.content
        cleaned_message = clean_mamul_message(original_message)

        open_message = await open_channel.send(f"📢 매물 신청 공개!\n{cleaned_message}")
        await open_message.add_reaction('🆙')

        saved_original_messages[open_message.id] = original_message

    if reaction.message.channel.id == OPEN_CHANNEL_ID:
        if reaction.message.id in claimed_messages:
            return

        if user.id in rejected_users:
            await reaction.message.channel.send(f"❗ {user.mention} 님은 현재 다른 매물 진행 중입니다. 완료 후 다시 신청해주세요!")
            await reaction.remove(user)
            return

        rejected_users.add(user.id)

        winner = user
        original_message = saved_original_messages.get(reaction.message.id)

        if original_message:
            dm = await winner.create_dm()
            cleaned_message2 = clean_mamul_message2(original_message)
            confirm_message = await dm.send(f"✅ 매물을 맡게 되었습니다!\n\n{cleaned_message2}\n\n**작업 완료 후 이 메시지에 리액션과 기사채팅방에 전적사진을 공유해주세요!**")
            saved_original_messages[confirm_message.id] = (reaction.message.id, user.id)
        else:
            await winner.send("✅ 매물을 맡게 되었습니다!\n(원본 정보를 찾을 수 없습니다.)")

        await reaction.message.channel.send(f"🎉 {winner.mention} 님이 매물을 맡았습니다!")
        claimed_messages.add(reaction.message.id)

    if isinstance(reaction.message.channel, discord.DMChannel):
        if reaction.message.id in saved_original_messages:
            info = saved_original_messages[reaction.message.id]
            if isinstance(info, tuple):
                rejected_users.discard(user.id)
                await reaction.message.channel.send("🎉 작업 완료가 확인되었습니다! 다음 매물도 신청하실 수 있습니다!")
                print(f"✅ {user} 작업 완료 처리됨")

# Railway/로컬에서 안전하게 구동
if __name__ == "__main__":
    bot.run(TOKEN)

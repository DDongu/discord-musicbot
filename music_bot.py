import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import os
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# 대기열에는 (search_query, title)를 저장함.
queue = deque()
now_playing = {"title": None, "url": None}

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ 존재하지 않는 명령어예요! `!help`로 사용 가능한 명령어를 확인해보세요.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ 명령어에 필요한 값이 빠졌어요! `!help`에서 형식을 확인해보세요.")
    else:
        await ctx.send(f"⚠️ 오류가 발생했어요: `{type(error).__name__}`")
        raise error

@bot.command(aliases=['j'])
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
    else:
        await ctx.send("🎙 음성 채널에 먼저 들어가 있어야 해요!")

@bot.command()  # leave는 약어 없음
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        now_playing["title"] = None
        now_playing["url"] = None

def play_next(ctx):
    if queue:
        # 대기열에서 검색어와 제목을 꺼내옴.
        search_query, title = queue.popleft()

        # 최신 URL을 받기 위해 새로 yt_dlp로 정보 추출
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'default_search': 'ytsearch',
            'socket_timeout': 10,
            'retries': 2,
            'nocheckcertificate': True,
            'noprogress': True,
            'source_address': '0.0.0.0'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(search_query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
            except Exception:
                # 오류 발생 시 대기열에서 해당 곡을 건너뛰고 재생 시도
                asyncio.run_coroutine_threadsafe(ctx.send(f"❌ '{title}'의 최신 URL을 받아오지 못했어요."), bot.loop)
                play_next(ctx)
                return

            audio_url = info['url']
            now_playing["title"] = info.get("title", title)
            now_playing["url"] = info.get("webpage_url", "링크 없음")

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -protocol_whitelist file,http,https,tcp,tls"
            ),
            after=lambda e: play_next(ctx)
        )
        coro = ctx.send(f"▶️ 다음 곡 재생 중: **{now_playing['title']}**")
        asyncio.run_coroutine_threadsafe(coro, bot.loop)
    else:
        now_playing["title"] = None
        now_playing["url"] = None

@bot.command(aliases=['p'])
async def play(ctx, *, search: str):
    if not ctx.voice_client:
        await ctx.invoke(bot.get_command("join"))

    # 공통 yt_dlp 옵션
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'socket_timeout': 10,
        'retries': 2,
        'nocheckcertificate': True,
        'noprogress': True,
        'source_address': '0.0.0.0'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info:
                info = info['entries'][0]
        except Exception:
            await ctx.send("❌ 유튜브에서 정보를 불러오는 데 실패했어요.")
            return

        # 즉시 재생할 때 사용될 URL (현재 fresh URL)
        audio_url = info['url']
        title = info.get('title', 'Unknown Title')
        webpage_url = info.get('webpage_url', '링크 없음')

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        now_playing["title"] = title
        now_playing["url"] = webpage_url
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(
                audio_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -protocol_whitelist file,http,https,tcp,tls"
            ),
            after=lambda e: play_next(ctx)
        )
        await ctx.send(f"▶️ 재생 중: **{title}**")
    else:
        # 대기열에는 원본 검색어(또는 링크)와 제목을 저장함.
        queue.append((search, title))
        await ctx.send(f"⏱ 큐에 추가됨: **{title}**")

@bot.command(aliases=['ps'])
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ 노래 일시정지!")

@bot.command(aliases=['r'])
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ 노래 다시 재생!")

@bot.command(aliases=['s'])
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ 다음 곡으로 넘어갈게요!")

@bot.command(name="list", aliases=["l"])
async def list_command(ctx):
    if not queue:
        await ctx.send("📭 대기열이 비어 있어요!")
    else:
        msg = "\n".join([f"{idx+1}. {title}" for idx, (_, title) in enumerate(queue)])
        await ctx.send(f"📋 재생 목록:\n{msg}")

@bot.command()
async def now(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing() and now_playing["title"]:
        await ctx.send(f"🎶 현재 재생 중: **{now_playing['title']}**\n🔗 {now_playing['url']}")
    else:
        await ctx.send("⏹ 현재 재생 중인 곡이 없어요.")

@bot.command()
async def search(ctx, *, search: str = None):
    if not search:
        await ctx.send("❌ 검색어를 입력해주세요. 예: `!search 아이유`")
        return

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'default_search': 'ytsearch',
        'socket_timeout': 10,
        'retries': 2,
        'nocheckcertificate': True,
        'noprogress': True,
        'source_address': '0.0.0.0'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            results = ydl.extract_info(f"ytsearch5:{search}", download=False)['entries']
        except Exception as e:
            await ctx.send("⚠️ YouTube 검색 중 문제가 발생했어요. 잠시 후 다시 시도해주세요.")
            print("YT-DLP ERROR:", e)
            return

    if not results:
        await ctx.send("❌ 검색 결과가 없어요.")
        return

    msg = "\n".join([f"{idx+1}. {video['title']} ({video['webpage_url']})" for idx, video in enumerate(results)])
    await ctx.send(f"🔍 **'{search}' 검색 결과 (상위 5개):**\n{msg}")

@bot.command()
async def help(ctx):
    help_text = """
🎵 **사용 가능한 명령어 목록 (약어 포함):**

`!play <제목/링크>` or `!p` - 노래 재생 (즉시 재생 또는 대기열에 추가; 대기열은 fresh URL로 재생됨)
`!pause` or `!ps` - 일시정지
`!resume` or `!r` - 다시 재생
`!skip` or `!s` - 다음 곡
`!list` or `!l` - 재생 목록 보기 (대기열에 저장된 검색어 기준)
`!now` - 현재 재생 중인 곡 확인
`!join` or `!j` - 봇 음성 채널에 초대
`!leave` - 봇 음성 채널에서 퇴장
`!search <제목>` - 유튜브에서 검색 (상위 5개 링크 출력)
`!help` - 이 도움말 보기
"""
    await ctx.send(help_text)


load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

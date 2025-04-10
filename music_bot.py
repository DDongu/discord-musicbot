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

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queue.clear()
        now_playing["title"] = None
        now_playing["url"] = None

# 🔧 yt-dlp 옵션 개선
def get_ydl_opts():
    return {
        'format': 'bestaudio/best',  # ✅ 가장 좋은 오디오 포맷 자동 선택
        'quiet': True,
        'default_search': 'ytsearch',
        'socket_timeout': 10,
        'retries': 3,
        'nocheckcertificate': True,
        'noprogress': True,
        'geo_bypass': True,
        'source_address': '0.0.0.0',
    }

# 🔧 ffmpeg 음질/버퍼 최적화
def get_ffmpeg_opts():
    return {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -ar 48000 -ac 2 -b:a 192k'  # ✅ 오디오 음질 및 안정화 옵션
    }

def play_next(ctx):
    if queue:
        search_query, title = queue.popleft()
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            try:
                info = ydl.extract_info(search_query, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
            except Exception:
                asyncio.run_coroutine_threadsafe(
                    ctx.send(f"❌ '{title}'의 최신 URL을 받아오지 못했어요."), bot.loop
                )
                play_next(ctx)
                return

            audio_url = info['url']
            now_playing["title"] = info.get("title", title)
            now_playing["url"] = info.get("webpage_url", "링크 없음")

        ctx.voice_client.play(
            discord.FFmpegPCMAudio(audio_url, **get_ffmpeg_opts()),  # 🔧 ffmpeg 음질 옵션 반영
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
        await asyncio.sleep(1)

    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("❌ 음성 채널에 연결되지 않았어요. 잠시 후 다시 시도해주세요.")
        return

    with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
        try:
            info = ydl.extract_info(search, download=False)
            if 'entries' in info:
                info = info['entries'][0]
        except Exception:
            await ctx.send("❌ 유튜브에서 정보를 불러오는 데 실패했어요.")
            return

        audio_url = info['url']
        title = info.get('title', 'Unknown Title')
        webpage_url = info.get('webpage_url', '링크 없음')

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        now_playing["title"] = title
        now_playing["url"] = webpage_url
        ctx.voice_client.play(
            discord.FFmpegPCMAudio(audio_url, **get_ffmpeg_opts()),  # 🔧 ffmpeg 음질 옵션 반영
            after=lambda e: play_next(ctx)
        )
        await ctx.send(f"▶️ 재생 중: **{title}**")
    else:
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

    with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
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

!play <제목/링크> or !p - 노래 재생
!pause or !ps - 일시정지
!resume or !r - 다시 재생
!skip or !s - 다음 곡
!list or !l - 재생 목록 보기
!now - 현재 재생 곡 보기
!join or !j - 음성 채널 참여
!leave - 음성 채널 퇴장
!search <제목> - 유튜브 검색
!help - 도움말
"""
    await ctx.send(help_text)

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)

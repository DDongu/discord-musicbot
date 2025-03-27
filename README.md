# 🎵 Discord Music Bot

디스코드에서 유튜브 음악을 검색하고 재생할 수 있는 심플한 음악 봇입니다.

FFmpeg와 yt-dlp를 사용하며, 대기열 기능, 재생/일시정지/다음곡 스킵 등 기본적인 컨트롤 기능을 지원합니다.

---

✅ 주요 기능

- !play <검색어 또는 링크>: 곡 재생 (재생 중이면 대기열에 추가됨)
- !pause / !resume / !skip: 재생 제어
- !list: 대기열 보기
- !now: 현재 재생 중인 곡 확인
- !search <검색어>: 유튜브 상위 5개 검색 결과 보기
- !join / !leave: 봇 음성 채널 입장/퇴장
- !help: 명령어 전체 목록 출력
- 대기열에 있는 곡도 재생 직전에 항상 최신 URL로 갱신됨

---

# 🚀 설치 및 실행 방법 (Mac 기준)

1.  레포지토리 클론

    ```
    git clone https://github.com/yourusername/Discord-MusicBot.git

    cd Discord-MusicBot
    ```

2.  가상환경 및 패키지 설치

    ```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

    📌 requirements.txt 파일

    ```txt
    discord.py
    yt-dlp
    python-dotenv
    ```

3.  .env 파일 수정

    ```
    DISCORD_TOKEN=여기에_당신의_디스코드_봇_토큰
    ```

4.  실행 (백그라운드 + 로그 기록)

    ```
    ./start_bot.sh
    ```

    (실행되면 bot.log 파일에 로그와 PID가 기록됩니다.)

5.  봇 중지

    ```
    kill $(grep "Discord Music Bot started with PID" bot.log | tail -1 | awk '{print $NF}')

    또는 ps aux | grep music_bot.py 로 PID 확인 후 kill `<PID>`
    ```

---

# 📦 예시 명령어

```
🎵 사용 가능한 명령어 목록 (약어 포함):

!play <제목/링크> or !p - 노래 재생 (즉시 재생 또는 대기열에 추가; 대기열은 fresh URL로 재생됨)
!pause or !ps - 일시정지
!resume or !r - 다시 재생
!skip or !s - 다음 곡
!list or !l - 재생 목록 보기 (대기열에 저장된 검색어 기준)
!now - 현재 재생 중인 곡 확인
!join or !j - 봇 음성 채널에 초대
!leave - 봇 음성 채널에서 퇴장
!search <제목> - 유튜브에서 검색 (상위 5개 링크 출력)
!help - 이 도움말 보기
```

---

# 📌 주의사항

- FFmpeg와 yt-dlp가 설치되어 있어야 합니다.

  - macOS: brew install ffmpeg
  - 최신 yt-dlp: pip install -U yt-dlp

- search 명령어에서 오류 로그가 뜨는데 사용에는 문제가 없어보입니다.

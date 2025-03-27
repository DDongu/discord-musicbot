#!/bin/zsh

cd ~/projects/Discord-MusicBot  # 봇 디렉토리로 이동
source venv/bin/activate

# 현재 디렉토리에 log 저장하고 백그라운드 실행
nohup python3 music_bot.py > bot.log 2>&1 &

# 백그라운드 PID 저장
echo "✅ 봇이 백그라운드에서 실행 중입니다. 로그: ./bot.log"


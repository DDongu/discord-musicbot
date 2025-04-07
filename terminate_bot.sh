#!/bin/bash

# music_bot.py 실행 중인 프로세스 찾기
PID=$(ps aux | grep music_bot.py | grep -v grep | awk '{print $2}')

if [ -z "$PID" ]; then
  echo "❌ 실행 중인 봇 프로세스를 찾을 수 없어요."
else
  echo "🛑 봇 프로세스 종료 중... (PID: $PID)"
  kill -9 "$PID"
  echo "✅ 봇이 성공적으로 종료되었습니다."
fi

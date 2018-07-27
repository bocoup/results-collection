#!/bin/bash

set -e

create_session() {
  curl \
    -X POST \
    --data '{"capabilities":{}}' \
    --fail \
    http://localhost:9876/session > /dev/null 2>&1
}

is_automation_enabled() {
  /Applications/Safari\ Technology\ Preview.app/Contents/MacOS/safaridriver --port 9876 &
  stp_pid=$!

  while true ; do
    if curl --fail http://localhost:9876/status > /dev/null 2>&1; then
      break
    fi
  done

  create_session
  result=$?

  kill -9 $stp_pid
  wait $stp_pid 2> /dev/null

  return $result
}

toggle_automation() {
  osascript - <<SCRIPT
  activate application "Safari Technology Preview"

  tell application "System Events"
      set ready to false

      repeat while not ready
          repeat with processd in every process
              if name of processd as string is "Safari Technology Preview" then
                  set ready to true
              end if
          end repeat
      end repeat

      tell process "Safari Technology Preview"
          click menu item "Allow Remote Automation" of menu "Develop" of menu bar item "Develop" of menu bar 1
      end tell
  end tell

  tell application "Safari Technology Preview" to quit
SCRIPT
}

is_automation_enabled || toggle_automation

if ! is_automation_enabled; then
  echo Unable to enable automation >&2
  exit 1
fi

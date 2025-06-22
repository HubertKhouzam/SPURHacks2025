import socket
from datetime import datetime, timedelta
from collections import deque

def chatFunc():
    # Twitch IRC connection info
    HOST = 'irc.chat.twitch.tv'
    PORT = 6667
    NICK = 'flaccdo'
    TOKEN = 'oauth:5hat2rxorg0y8j0ti7gt13rdtztadj'
    CHANNEL = '#jasontheween'

    # Detection config
    WINDOW_SECONDS = 60
    PEAK_MULTIPLIER = 2
    PRE_ROLL = 10  # seconds before peak to include in clip
    END_COOLDOWN = 10  # seconds after last peak to mark end of hype
    ALPHA = 0.1  # EMA smoothing factor

    # State
    message_times = deque()
    baseline_rate = 0.5
    in_peak = False
    last_peak_time = None
    clip_start = None
    clip_windows = []

    # Connect to Twitch IRC
    sock = socket.socket()
    sock.connect((HOST, PORT))
    sock.send(f"PASS {TOKEN}\n".encode('utf-8'))
    sock.send(f"NICK {NICK}\n".encode('utf-8'))
    sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))
    print(f"Connected to {CHANNEL} as {NICK}")

    while True:
        resp = sock.recv(2048).decode('utf-8')

        for line in resp.strip().split('\r\n'):
            if line.startswith("PING"):
                sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
                continue

            if "PRIVMSG" in line:
                message = line.split('PRIVMSG', 1)[1].split(':', 1)[1]
                now = datetime.now()
                message_times.append(now)

                print(f"[{now.strftime('%H:%M:%S')}] {message.strip()}")

                # Trim window
                while len(message_times) >= 2 and (message_times[-1] - message_times[0]).total_seconds() > WINDOW_SECONDS:
                    message_times.popleft()

                # Compute current rate
                duration = (message_times[-1] - message_times[0]).total_seconds()
                rate = len(message_times) / duration if duration > 0 else 0

                # Update baseline rate (EMA)
                baseline_rate = (1 - ALPHA) * baseline_rate + ALPHA * rate

                # Peak detection
                if not in_peak and rate > PEAK_MULTIPLIER * baseline_rate:
                    in_peak = True
                    last_peak_time = now
                    clip_start = now - timedelta(seconds=PRE_ROLL)
                    print(f"🔥 HYPE DETECTED! Start: {clip_start.strftime('%H:%M:%S')}")

                elif in_peak:
                    if rate < baseline_rate * 1.1:
                        time_since_last_peak = (now - last_peak_time).total_seconds()
                        if time_since_last_peak >= END_COOLDOWN:
                            in_peak = False
                            clip_end = now
                            clip_windows.append((clip_start, clip_end))
                            print(f"🎬 HYPE ENDED! End: {clip_end.strftime('%H:%M:%S')}")
                            print(f"🧠 Saved hype clip: {clip_start.strftime('%H:%M:%S')} to {clip_end.strftime('%H:%M:%S')}")

if __name__ == '__main__':
    chatFunc()

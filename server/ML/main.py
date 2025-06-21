import socket
from datetime import datetime

# 🔧 Replace these with your details
HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'flaccdo'  # Your Twitch username
TOKEN = 'oauth:5hat2rxorg0y8j0ti7gt13rdtztadj'  # From TwitchTokenGenerator
CHANNEL = '#xqc'  # The channel you want to monitor, e.g. #xqc
from collections import deque

# Set up socket connection to Twitch IRC
sock = socket.socket()
sock.connect((HOST, PORT))
sock.send(f"PASS {TOKEN}\n".encode('utf-8'))
sock.send(f"NICK {NICK}\n".encode('utf-8'))
sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))


WINDOW_SECONDS = 60
PEAK_MULTIPLIER = 2

message_times = deque()

print(f"Connected to {CHANNEL} as {NICK}")

# Listen for messages
while 1:
    resp = sock.recv(2048).decode('utf-8')

    # Respond to PINGs to avoid being disconnected
    if resp.startswith("PING"):
        sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
        continue

    # Print chat messages
    if "PRIVMSG" in resp:
        # username = resp.split('!', 1)[0][1:]
        message = resp.split('PRIVMSG', 1)[1].split(':', 1)[1]
        # print(f"{username}: {message.strip()}")
        timestamp = datetime.now().strftime("%H:%M:%S")
        message_times.append(timestamp)
        print(f"[{timestamp}] {message}")

        # Convert timestamp strings to datetime objects for comparison
        now = datetime.strptime(timestamp, "%H:%M:%S")
        while message_times and (now - datetime.strptime(message_times[0], "%H:%M:%S")).total_seconds() > WINDOW_SECONDS:
            message_times.popleft()


        if len(message_times) > 1:
            duration = (datetime.strptime(message_times[-1], "%H:%M:%S") - datetime.strptime(message_times[0], "%H:%M:%S")).total_seconds()
            avg_rate = len(message_times) / duration if duration > 0 else 0
            current_rate = len(message_times) / WINDOW_SECONDS


            if avg_rate > current_rate * PEAK_MULTIPLIER:
                print(f"Peak detected! Avg rate: {avg_rate:.2f} msgs/s, Current rate: {current_rate:.2f} msgs/s")
        



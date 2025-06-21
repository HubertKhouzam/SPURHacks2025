import socket
from datetime import datetime

# 🔧 Replace these with your details
HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'flaccdo'  # Your Twitch username
TOKEN = 'oauth:5hat2rxorg0y8j0ti7gt13rdtztadj'  # From TwitchTokenGenerator
CHANNEL = '#caedrel'  # The channel you want to monitor, e.g. #xqc

# Set up socket connection to Twitch IRC
sock = socket.socket()
sock.connect((HOST, PORT))
sock.send(f"PASS {TOKEN}\n".encode('utf-8'))
sock.send(f"NICK {NICK}\n".encode('utf-8'))
sock.send(f"JOIN {CHANNEL}\n".encode('utf-8'))

print(f"Connected to {CHANNEL} as {NICK}")

# Listen for messages
while 1:
    resp = sock.recv(2048).decode('utf-8')

    for line in resp.strip().split('\r\n'):
        if line.startswith("PING"):
            sock.send("PONG :tmi.twitch.tv\n".encode('utf-8'))
            continue

        if "PRIVMSG" in line:
            try:
                message = line.split('PRIVMSG', 1)[1].split(':', 1)[1]
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] {message.strip()}")
            except IndexError:
                print(f"[WARN] Could not parse line: {line}")

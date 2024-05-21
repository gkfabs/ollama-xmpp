#! /usr/bin/python3

import argparse
import ollama
import time
import xmpp

def handle_messages(ollama_model, ollama_client, ollama_keep_alive):
    def handler(client, stanza):
        sender = stanza.getFrom()
        message_type = stanza.getType()
        message = stanza.getBody()
        stream = ollama_client.chat(model=ollama_model, messages=[
            {
                'role': 'user',
                'content': message,
            },
        ], stream=True, keep_alive = ollama_keep_alive)
        msg = ""
        for chunk in stream:
            if chunk['message']['content'].endswith('\n'):
                msg += chunk['message']['content']
                client.send(xmpp.Message(sender, msg, typ=message_type))
                msg = ""
            else:
                msg += chunk['message']['content']
        client.send(xmpp.Message(sender, msg, typ=message_type))
    return handler

def handle_presences():
    def handler(client, stanza):
        sender = stanza.getFrom()
        presence_type = stanza.getType()
        if presence_type == "subscribe":
            client.send(xmpp.Presence(to=sender, typ="subscribed"))
    return handler

ap = argparse.ArgumentParser()
ap.add_argument('--xmpp_host', default=None, required=True)
ap.add_argument('--xmpp_port', default=5222, type=int)
ap.add_argument('--xmpp_username', default='ollama')
ap.add_argument('--xmpp_password', default=None, required=True)
ap.add_argument('--ollama_host', default='localhost')
ap.add_argument('--ollama_port', default=11434, type=int)
ap.add_argument('--ollama_model', default='llama3')
ap.add_argument('--ollama_keep_alive', default='5m')
args = ap.parse_args()

ollama_client = ollama.Client(host='http://' + args.ollama_host + ':' + str(args.ollama_port))
try:
    ollama_client.show(args.ollama_model)
except ollama.ResponseError as e:
    try:
        ollama_client.pull(args.ollama_model)
    except ollama.ResponseError as e:
        print('Ollama model ' + args.ollama_model + ' doesn\'t exist')
        exit()

xmpp_client = xmpp.Client(args.xmpp_host, debug=[])
if not xmpp_client.connect(server=(args.xmpp_host, args.xmpp_port)):
    print('Count not connect to ' + args.xmpp_host)
    exit()
if not xmpp_client.auth(args.xmpp_username, args.xmpp_password, 'bot'):
    print('Count not with username ' + args.username)
    exit()

message_callback = handle_messages(args.ollama_model, ollama_client, args.ollama_keep_alive)
xmpp_client.RegisterHandler("message", message_callback)

presence_callback = handle_presences()
xmpp_client.RegisterHandler("presence", presence_callback)

xmpp_client.sendInitPresence()
xmpp_client.Process()

print('Bot init done')
while xmpp_client.isConnected():
    xmpp_client.Process()
    time.sleep(1)

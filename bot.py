# Job offer feed Telegram channels to Discord (bot)
# The bot listen some Telegram channels and post offers in Discord, following some patterns
# Author: Elena Mestanza (github.com/elemestanza)
# Write in Python version 3.10.4

import os, re, time
import platform
import json
import asyncio

try:
    from dotenv import load_dotenv

    from telethon import TelegramClient, events

    import discord
    from discord.ext import commands

    from langdetect import detect

    from colorama import just_fix_windows_console
    from termcolor import colored
except ImportError:
    os.system('py -m pip install -r requirements.txt')

just_fix_windows_console()

VERSION="2.8.10_r2-LOCAL"
# LOAD ENVIRONTMENT
load_dotenv()
# Telegram
ID = os.getenv('API_ID')
HASH = os.getenv('API_HASH')
LOCAL = os.getenv('MY_FEED')
TLISTEN = ('https://t.me/trabajo_gamattica', 'https://t.me/gamedevjobs_es')
# Discord
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
CHANNEL = int(os.getenv('DISCORD_CHANNEL_ID'))
DLISTEN = int(os.getenv('DISCORD_FEEDS_ID'))
ROLE_JUNIOR = "<@&ROLE_ID>"

# CLIENTS
client = TelegramClient('anon', ID, HASH) #Telegram
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all()) #Discord

offerID = 0

# START EVENT
# Off-line messages revisor
# @bot.event
async def on_ready():
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Revising offline messages...")

    # JSON: Open
    f = open('data.json', 'r+')
    data = json.load(f)

    # Discord
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Revising Discord...")
    channel = bot.get_channel(DLISTEN)
    print("DEBUG:", channel)
    messID = data["last_messages"]["discord"]
    print("DEBUG:", messID)
    messages = []
    print("DEBUG:", messages)
    async for m in channel.history(after=messID):
        print("DEBUG:", m.id)
        messages.append(m)
    data["last_messages"]["discord"] = messages[0].id # Es el más antiguo de los mensajes
    if len(messages) == 0: print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Discord offers are already up-to-date\n")
    else:
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] ", len(messages), "Discord offers founded\n")
        for m in messages:
            print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Discord message:", m.content)
            await postman(m.content)

    # Telegram
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Revising Telegram...")
    messages = []
    for i in range(0, len(TLISTEN)):
        messID = data["last_messages"]["telegram"][i]
        async for message in client.iter_messages(TLISTEN[i], min_id=messID):
            data["last_messages"]["telegram"][i] = message.id
            messages.append(message)
    if len(messages) == 0: print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Telegram offers are already up-to-date\n")
    else:
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] ", len(messages), "Telegram offers founded\n")
        for m in messages:
            print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Telegram message:", m.message)
            await postman(m.message)

    # JSON: Close
    f.seek(0)
    json.dump(data, f, indent = 4)
    f.truncate()

    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"] Offline messages revised\n")

# LISTENERS EVENTS
# My Telegram Channel
@client.on(events.NewMessage(chats=LOCAL))
async def newMyMessageListener(event):
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Message received", "cyan"))
    newMessage = "\n" + event.message.text
    channel = bot.get_channel(CHANNEL) # OdEV Controller Server > test-channel
    for i in range(0, len(newMessage), 2000):
        await channel.send(newMessage[i:2000+i])
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Message sent successfully\n", "green"))

# Telegram Channels
@client.on(events.NewMessage(chats=TLISTEN))
async def newMessageListener(event):
    global offerID
    offerID += 1

    # JSON: Open & Close
    f = open('data.json', 'r+')
    data = json.load(f)

    for id in list(data["telegram-broadcasts-id"]):
        if (event.message.peer_id.channel_id == int(id)):
            sender = data["telegram-broadcasts-id"][id]
            write_last_message(event.message.id, sender)
            break
    f.close()

    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Telegram offer ", "cyan") + colored("#"+str(offerID), "white", "on_cyan") + colored(" received from "+sender, "cyan"))
    newMessage = event.message.text
    if (len(newMessage) > 280): prompt = newMessage[:280] + "[...]"
    else: prompt = newMessage
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Telegram message:", "cyan"), prompt)
    await postman(newMessage, offerID, sender)

# Discord Channel
@bot.event
async def on_message(message):
    if message.channel.id == DLISTEN and message.content != "":
        sender = message.author.name
        global offerID
        offerID += 1
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Discord offer ", "blue") + colored("#"+str(offerID), "white", "on_blue") + colored(" received from "+sender, "blue"))
        if (len(message.content) > 280): prompt = message.content[:280] + "[...]"
        else: prompt = message.content
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Discord message:", "blue"), prompt)
        write_last_message(message.id, "Discord")
        await postman(message.content, offerID, sender)
    await bot.process_commands(message)

# POSTMAN
async def postman(offer, offerID, sender):
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("In postman", "yellow"))
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("[DEBUG] NEW FEATURE:", "yellow"))
    lang = detect(offer)
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("[DEBUG] Offer language:", "yellow"), lang)
    # JSON: Open
    f = open('data.json', 'r+')
    data = json.load(f)

    # Fix offer first lines
    offerLines = offer.split("\n")
    offerLinesToPrompt = []
    movePrompt = 0
    if (sender == "Gamattica"): movePrompt = 1
    if (len(offerLines) > 3 + movePrompt):
        offerLinesToPrompt = offerLines[movePrompt : 3 + movePrompt] + offerLines[len(offerLines) - 2:]
    else: offerLinesToPrompt = offerLines[movePrompt:]
    offerPrompt = "\n".join(offerLinesToPrompt)

    categories = list(data["channels"])
    regexList = (r'(?i)2d', r'(?i)3d', r'(?i)account\W*manager', r'(?i)analyst|anali', r'(?i)animat|animad', r'(?i)art|graphic|gráfic', r'(?i)audio|sound|sonid|music|composer', r'(?i)character', r'(?i)compos', r'(?i)concept', r'(?i)develop|desarrolla', r'(?i)engineer|ingenier', r'(?i)environtment', r'(?i)game design|\Wdesigner\W|diseñado',  r'(?i)game manag', r'(?i)gameplay', r'(?i)generalist', r'(?i)level design|puzzle design', r'(?i)marketing|sale|comerci|commerci', r'(?i)modela',r'(?i)narrativ|writ|escri', r'(?i)productor|produce', r'(?i)program|script', r'(?i)product\W*manager', r'(?i)product\W*owner', r'(?i)project\W*manager', r'(?i)qa|qc', r'(?i)scrum\W*master', r'(?i)technical', r'(?i)test', r'(?i)sfx|sound\W*effects', r'(?i)vfx|video\W*effects', r'(?i)\Wui\W', r'(?i)\Wux\W', r'(?i)assistant', r'(?i)junior|jr', r'(?i)mid|\Wmed\W', r'(?i)senior', r'(?i)lead|director', r'(?i)android', r'(?i)\Wios\W', r'(?i)unity', r'(?i)unreal')

    channels = set()
    for i in range(0, len(categories)):
        filteredMessage = re.findall(regexList[i], offerPrompt, flags=re.IGNORECASE)
        if len(filteredMessage) != 0:
            for x in data["channels"][categories[i]]: channels.add(x)
    channels = list(channels)

    if (offerID > data["offer"]): data["offer"] = offerID

    # JSON: Close
    f.seek(0)
    json.dump(data, f, indent = 4)
    f.truncate()

    # Fix message
    match sender:
        case "Gamattica":
            offer = "\n".join(offerLines[1:3]) + "\n\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"
        case "Gamedev Job ES":
            offer = "\n".join(offerLines[:3]) + "\n\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"
        case "Remote Game Jobs":
            offer = "\n".join(offerLines[:2]) + "\n\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"
        case "Work with Indies":
            offer = "\n".join(offerLines[1:2]) + "\n\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_"

    # Send message
    if len(channels) != 0:
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Offer ", "green") + colored("#"+str(offerID), "white", "on_green") + colored(" accepted", "green"))
        for cid in channels:
            channel = bot.get_channel(cid)
            for i in range(0, len(offer), 2000):
                await channel.send(offer[i:2000+i], suppress_embeds=True)
        print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Offer ", "green") + colored("#"+str(offerID), "white", "on_green") + colored(" sent successfully\n", "green"))
    else: print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Offer ", "red") + colored("#"+str(offerID), "white", "on_red") + colored(" denied\n", "red"))

# BOT COMMANDS
# Know job lists
@bot.command()
async def joblists(ctx):
    print("DEBUG: in !joblists")
    f = open('data.json', 'r+')
    data = json.load(f)
    categories = ', '.join(list(data["channels"]))
    f.close()
    print("DEBUG: ", ctx.channel)
    await ctx.send("Job lists are", categories)

# Add job list to a channel
@bot.command()
async def addjoblist(ctx, *args):
    # JSON: Open
    f = open('data.json', 'r+')
    data = json.load(f)
    categories = list(data["channels"])
    technical = ['account-manager', 'analyst', 'developer', 'engineer', 'game-manager', 'gameplay', 'marketing', 'producer', 'product-manager', 'product-owner', 'programmer', 'project-manager', 'qa', 'scrum-master', 'technical', 'tester']
    artistic = ['2d', '3d', 'animation', 'artist', 'audio', 'character', 'composer', 'concept', 'environtment', 'game-designer', 'generalist', 'level-designer', 'modelator', 'narrative', 'sfx', 'vfx', 'ui', 'ux']
    
    # Show help
    if (len(args) == 0 or args[0] == 'help'):
        # await ctx.send("pong!")
        return
    else: # Add categories
        channelID = ctx.channel.id
        if (args[0] == 'all'): # All categories
            for c in categories: 
                if not c in data["channels"][c]: data["channels"][c].append(channelID)
            # await ctx.send("All job lists added!")
        elif (args[0] == 'technical'): # Technical offers
            for c in technical: 
                if not c in data["channels"][c]: data["channels"][c].append(channelID)
            # await ctx.send("Technical job lists added!")
        elif (args[0] == 'artistic'): # Artistic offers
            for c in artistic: 
                if not c in data["channels"][c]: data["channels"][c].append(channelID)
            # await ctx.send("Artistic job lists added!")
        else: # Some categories
            validCategories = []
            for a in args:
                if a in categories: validCategories.append(a)
            for c in validCategories:
                if not c in data["channels"][c]: data["channels"][c].append(channelID)
            strCat = ", ".join(validCategories)
            # await ctx.send(strCat, "job lists added!")
    
    # JSON: Close
    f.seek(0)
    json.dump(data, f, indent = 4)
    f.truncate()

# Remove job list to a channel
@bot.command()
async def removejoblist(ctx, *args):
    # JSON: Open
    f = open('data.json', 'r+')
    data = json.load(f)
    categories = list(data["channels"])
    technical = ['account-manager', 'analyst', 'developer', 'engineer', 'game-manager', 'gameplay', 'marketing', 'producer', 'product-manager', 'product-owner', 'programmer', 'project-manager', 'qa', 'scrum-master', 'technical', 'tester']
    artistic = ['2d', '3d', 'animation', 'artist', 'audio', 'character', 'composer', 'concept', 'environtment', 'game-designer', 'generalist', 'level-designer', 'modelator', 'narrative', 'sfx', 'vfx', 'ui', 'ux']
    
    # Show help
    if (len(args) == 0 or args[0] == 'help'):
        return
    else: # Remove categories
        channelID = ctx.channel.id
        if (args[0] == 'all'): # All categories
            for c in categories:
                if channelID in data["channels"][c]:
                    data["channels"][c].remove(channelID)
        elif (args[0] == 'technical'): # Technical offers
            for c in technical:
                if channelID in data["channels"][c]:
                    data["channels"][c].remove(channelID)
        elif (args[0] == 'artistic'): # Artistic offers
            for c in artistic:
                if channelID in data["channels"][c]:
                    data["channels"][c].remove(channelID)
        else: # Some categories
            for a in args:
                if a in categories:
                    if channelID in data["channels"][c]:
                        data["channels"][c].remove(channelID)
    
    # JSON: Close
    f.seek(0)
    json.dump(data, f, indent = 4)
    f.truncate()


# JSON
# Write last message
def write_last_message(new_data, source, filename='data.json'):
    with open(filename,'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside
        if (source == "Discord"):
            file_data["last_messages"]["discord"] = new_data
        elif (source == "Gamattica"):
            file_data["last_messages"]["telegram"][0] = new_data
        elif (source == "Gamedev Jobs ES"):
            file_data["last_messages"]["telegram"][1] = new_data
        # Sets file's current position at offset.
        file.seek(0)
        json.dump(file_data, file, indent = 4)
        file.truncate()

# START
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
async def main():
    # Get last ID offer
    f = open('data.json', 'r+')
    file_data = json.load(f)
    global offerID
    offerID = file_data["offer"]
    f.close()

    # Initial prompt
    # os.system("cls")
    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Welcome to OdEV Terminal\n", "magenta"),
          "  > Version:", colored(VERSION, "magenta"),"\n"
          "   >", colored("Python", "blue", "on_yellow"), "version:", colored(platform.python_version(), "magenta"),"\n"
          "   >", colored("Running in ", "magenta")+ colored(os.environ['COMPUTERNAME'], on_color="on_magenta") +colored("\n", "white"))

    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Initializing environtment...\n", "magenta"),
          ">", colored("TELEGRAM", "cyan"), "\n"
          "  >", colored("ID=","magenta")+str(ID)+",", type(ID),"\n"
          "  >", colored("HASH=","magenta")+str(HASH)+",", type(HASH),"\n"
          "  >", colored("LOCAL=","magenta")+str(LOCAL)+",", type(LOCAL),"\n"
          "  >", colored("TLISTEN=","magenta")+"('"+TLISTEN[0]+"',")
    for i in range(1, len(TLISTEN)-1, 1):
        print("             '"+TLISTEN[i]+"',")
    print("             '"+TLISTEN[len(TLISTEN)-1]+"'),", type(TLISTEN),"\n"
          " >", colored("DISCORD", "blue"), "\n"
          "  >", colored("TOKEN=","magenta")+str(TOKEN)+",", type(TOKEN),"\n"
          "  >", colored("GUILD=","magenta")+str(GUILD)+",", type(GUILD),"\n"
          "  >", colored("CHANNEL=","magenta")+str(CHANNEL)+",", type(CHANNEL),"\n"
          "  >", colored("DLISTEN=","magenta")+str(DLISTEN)+",", type(DLISTEN),"\n")

    print("> ["+ time.strftime('%H:%M:%S', time.localtime()) +"]", colored("Starting clients...\n", "magenta"))
    await client.start()
    await bot.start(TOKEN, reconnect=True)

loop.run_until_complete(main())
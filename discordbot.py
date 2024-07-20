import asyncio
import discord
import threading
import datetime
import psutil
from env import botToken, botChannelId

class MyBot(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        await self.createStatusMessage()
        self.startTime = datetime.datetime.now()

    async def createStatusMessage(self):
        channel = self.get_channel(int(botChannelId))
        msg = await channel.send('Starting...')
        self.msg = msg

    async def updateStatusMessage(self, done = False):
        print("Updating status message...")

        if (not done):
            text = "Running since " + self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        else:
            text = "Ran from " + self.startTime.strftime("%Y-%m-%d %H:%M:%S") + " to " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            text += "\nTime Taken: " + str(datetime.datetime.now() - self.startTime)

        text += "\nLast updated at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        text += "\n\nResource Usage:\n\tRAM Usage: " + \
            str(round(psutil.Process().memory_info().rss/ 1024 ** 2)) + " mb \n\tTotal RAM Usage: " + \
            str(round(psutil.virtual_memory().percent, 1)) + "%\n\tCPU Usage: " + \
            str(psutil.cpu_percent()) + "%"
        
        if (hasattr(self, "statusMsg")):
            text += "\n\n" + self.statusMsg

        await self.msg.edit(content=text)

async def runBot(exitFlag):
    task = asyncio.create_task(bot.start(botToken))

    while True:
        await asyncio.sleep(10)
        await bot.updateStatusMessage()
        if exitFlag.is_set():
            break

    print("Exiting bot...")
    await bot.updateStatusMessage(True)
    await bot.close()
    task.cancel()

def startBotOtherThread(exitFlag):
    asyncio.run(runBot(exitFlag))

def startBot(exitFlag):
    print("Starting bot...")

    intents = discord.Intents.default()

    global bot
    bot = MyBot(intents=intents)
    
    thread = threading.Thread(target=startBotOtherThread, args=(exitFlag, ))
    thread.start()
    return thread
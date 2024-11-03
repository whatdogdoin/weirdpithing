import RPi.GPIO as GPIO
import time
import asyncio
import discord
from discord.ext import commands

# Replace 'YOUR_DISCORD_BOT_TOKEN' with your actual Discord bot token
TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
USER_ID = 1234567890  # Replace with the target user's Discord ID
TRIGGER_WORD = "activate"  # The word that will trigger the bridge
BRIDGE_DURATION = 5  # Duration for bridge to stay active, in seconds

# Set up GPIO pins
GPIO.setmode(GPIO.BCM)
input_pin = 18
output_pin = 23  # The GPIO pin we want to bridge to

GPIO.setup(input_pin, GPIO.IN)      # Voltage detection pin
GPIO.setup(output_pin, GPIO.OUT)    # Bridging control pin
GPIO.output(output_pin, GPIO.LOW)   # Initialize as LOW (off)

# Initialize Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Track voltage state
voltage_state = GPIO.input(input_pin)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    user = await bot.fetch_user(USER_ID)
    await user.send("Bot is online and monitoring voltage.")

@bot.event
async def on_message(message):
    # Check if the message is from the specified user and contains the trigger word
    if message.author.id == USER_ID and TRIGGER_WORD in message.content.lower():
        await activate_bridge(message.channel)

    await bot.process_commands(message)

async def activate_bridge(channel):
    GPIO.output(output_pin, GPIO.HIGH)  # Enable bridging
    await channel.send(f"Bridge connection enabled for {BRIDGE_DURATION} seconds.")

    # Wait for the specified duration, then disable the bridge
    await asyncio.sleep(BRIDGE_DURATION)
    GPIO.output(output_pin, GPIO.LOW)   # Disable bridging
    await channel.send("Bridge connection disabled.")

async def check_voltage():
    global voltage_state
    user = await bot.fetch_user(USER_ID)

    while True:
        current_state = GPIO.input(input_pin)
        if current_state != voltage_state:
            voltage_state = current_state
            if current_state == GPIO.HIGH:
                await user.send("Voltage is ON")
            else:
                await user.send("Voltage is OFF")
        time.sleep(1)

bot.loop.create_task(check_voltage())  # Start the voltage check loop
bot.run(TOKEN)

import gpiod
import time
import asyncio
import discord
from discord.ext import commands

# Replace with your actual Discord bot token and target user ID
TOKEN = 'BOT_TOKEN'
USER_ID = YOUR_ID  # Replace with the target user's Discord ID

# GPIO chip and line configuration
POWER_DETECTION_CHIP = "gpiochip2"  # GPIO chip for Physical Pin 11 (GPIO17)
POWER_DETECTION_LINE = 20           # Line number for GPIO17 (Physical Pin 11)

BRIDGE_CONTROL_CHIP = "gpiochip2"   # GPIO chip for Physical Pin 13 (GPIO27)
BRIDGE_CONTROL_LINE = 21            # Line number for GPIO27 (Physical Pin 13)

SECOND_BRIDGE_CONTROL_CHIP = "gpiochip2"  # GPIO chip for Physical Pin 15 (GPIO22)
SECOND_BRIDGE_CONTROL_LINE = 22           # Line number for GPIO22 (Physical Pin 15)

BRIDGE_DURATION = 1                 # Duration for bridge to stay active, in seconds
TRIGGER_WORD = "trigger-word"       # Keyword to trigger bridging

# Initialize GPIO chip and lines
chip = gpiod.Chip(POWER_DETECTION_CHIP)
power_line = chip.get_line(POWER_DETECTION_LINE)
bridge_line = chip.get_line(BRIDGE_CONTROL_LINE)
second_chip = gpiod.Chip(SECOND_BRIDGE_CONTROL_CHIP)
second_bridge_line = second_chip.get_line(SECOND_BRIDGE_CONTROL_LINE)

# Configure GPIO lines with pull-down resistors
power_line.request(consumer="power-detection", type=gpiod.LINE_REQ_DIR_IN)  # Request input for power detection
bridge_line.request(consumer="bridge-control", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_OPEN_DRAIN)  # Request output for bridge control with pull-down
second_bridge_line.request(consumer="second-bridge-control", type=gpiod.LINE_REQ_DIR_OUT, flags=gpiod.LINE_REQ_FLAG_OPEN_DRAIN)  # Request output for second bridge with pull-down

# Initialize outputs to LOW
bridge_line.set_value(0)
second_bridge_line.set_value(0)

# Initialize Discord bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Fetch the user to notify and store it in the bot instance
        self.user_to_notify = await self.fetch_user(USER_ID)
        await self.user_to_notify.send("Bot is online and monitoring voltage.")
        # Start the power detection loop
        self.loop.create_task(check_power_state())

bot = MyBot(command_prefix="!", intents=intents)

# Track power state
power_state = power_line.get_value()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

async def check_power_state():
    """Function to monitor power status and notify user of changes."""
    global power_state
    user = bot.user_to_notify

    while True:
        current_state = power_line.get_value()
        if current_state != power_state:
            # Debounce the signal
            await asyncio.sleep(0.05)
            if power_line.get_value() == current_state:
                power_state = current_state
                if current_state == 1:
                    await user.send("Power is ON")
                else:
                    await user.send("Power is OFF")
        await asyncio.sleep(1)

@bot.event
async def on_message(message):
    """Listen for messages to trigger bridge activation with a keyword."""
    if message.author.id == USER_ID and TRIGGER_WORD in message.content.lower():
        await activate_bridge(message.channel)

    await bot.process_commands(message)

async def activate_bridge(channel):
    """Activate the bridge for a set duration."""
    bridge_line.set_value(1)  # Enable first bridge output (GPIO27/Physical Pin 13)
    second_bridge_line.set_value(1)  # Enable second bridge output (GPIO22/Physical Pin 15)
    
    await channel.send(f"Bridge connection enabled for {BRIDGE_DURATION} seconds.")

    # Wait for the specified duration, then disable both bridges
    await asyncio.sleep(BRIDGE_DURATION)

    bridge_line.set_value(0)  # Disable first bridge output (GPIO27/Physical Pin 13)
    second_bridge_line.set_value(0)  # Disable second bridge output (GPIO22/Physical Pin 15)
    
    await channel.send("Bridge connection disabled.")

async def main():
    await bot.start(TOKEN)

# Run the main function
asyncio.run(main())

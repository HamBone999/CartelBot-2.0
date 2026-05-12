import nextcord as discord
from base import EconomyBot, Auth

# Slash-command bot — no Message Content intent needed for Discord App Discovery.
intents = discord.Intents.default()
intents.members = True  # needed to resolve Member arguments in slash commands
client = EconomyBot(command_prefix=Auth.COMMAND_PREFIX, intents=intents)

if __name__ == "__main__":
    print("Starting bot...")
    client.run(Auth.TOKEN)
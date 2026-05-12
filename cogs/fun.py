import nextcord
from nextcord.ext import commands
from numpy import random
from base import EconomyBot


class Fun(commands.Cog):
    def __init__(self, client: EconomyBot):
        self.client = client
        self.bank = self.client.db.bank

    @nextcord.slash_command(name="roll", description="High-risk dice gambling (1,000–15,000 Pesos)")
    async def roll(self, interaction: nextcord.Interaction,
                   amount: int = nextcord.SlashOption(description="Amount to bet", min_value=1000, max_value=15000)):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < amount:
            return await interaction.response.send_message("You don't have enough money!", ephemeral=True)

        result = random.randint(1, 6)
        if result >= 5:
            profit = int(amount * 3.5)
            await self.bank.update_acc(interaction.user, profit)
            await interaction.response.send_message(f"🎲 You rolled **{result}** → **JACKPOT!** +**{profit:,} Pesos** 🔥")
        elif result >= 3:
            profit = int(amount * 1.8)
            await self.bank.update_acc(interaction.user, profit)
            await interaction.response.send_message(f"🎲 You rolled **{result}** → Nice! +**{profit:,} Pesos**")
        else:
            await self.bank.update_acc(interaction.user, -amount)
            await interaction.response.send_message(f"🎲 You rolled **{result}** → You lost **{amount:,} Pesos** 💸")


def setup(client):
    client.add_cog(Fun(client))

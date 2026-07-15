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

        await self.bank.update_acc(interaction.user, -amount)  # take the bet first
        result = random.randint(1, 7)  # numpy → 1..6
        if result == 6:
            added, lost = await self.bank.add_to_wallet(interaction.user, int(amount * 3))
            msg = f"🎲 You rolled **6** → **JACKPOT!** You win **{added:,} Pesos** (3×) 🔥"
        elif result >= 4:
            added, lost = await self.bank.add_to_wallet(interaction.user, int(amount * 1.4))
            msg = f"🎲 You rolled **{result}** → Nice! You get **{added:,} Pesos** (1.4×)"
        else:
            return await interaction.response.send_message(f"🎲 You rolled **{result}** → You lost **{amount:,} Pesos** 💸")
        if lost > 0:
            msg += f"\n⚠️ Wallet capped — {lost:,} Pesos lost."
        await interaction.response.send_message(msg)


def setup(client):
    client.add_cog(Fun(client))

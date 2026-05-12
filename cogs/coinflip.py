import nextcord
from nextcord.ext import commands
import random

GID = [547181131766693900]


class CoinflipView(nextcord.ui.View):
    def __init__(self, challenger: nextcord.Member, opponent: nextcord.Member, amount: int, bank):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.amount = amount
        self.bank = bank
        self.resolved = False

    @nextcord.ui.button(label="✅ Accept", style=nextcord.ButtonStyle.success)
    async def accept(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("This challenge isn't for you!", ephemeral=True)
        if self.resolved:
            return
        self.resolved = True

        # Re-check both wallets
        ch = await self.bank.get_acc(self.challenger)
        op = await self.bank.get_acc(self.opponent)
        if ch[1] < self.amount or op[1] < self.amount:
            return await interaction.response.edit_message(
                content="❌ One of you doesn't have enough Pesos anymore.", embed=None, view=None)

        winner = random.choice([self.challenger, self.opponent])
        loser = self.opponent if winner == self.challenger else self.challenger

        await self.bank.update_acc(loser, -self.amount)
        added, lost = await self.bank.add_to_wallet(winner, self.amount * 2)

        coin = "🟡 Heads" if random.random() < 0.5 else "⚪ Tails"
        em = nextcord.Embed(title="🪙 Coinflip Result", color=0xffd700)
        em.add_field(name="Coin landed on", value=f"**{coin}**", inline=False)
        em.add_field(name="Winner", value=f"🏆 {winner.mention} — **+{added:,} Pesos**", inline=False)
        em.add_field(name="Loser", value=f"💸 {loser.mention} — **-{self.amount:,} Pesos**", inline=False)
        if lost > 0:
            em.add_field(name="⚠️ Wallet cap", value=f"{lost:,} Pesos lost (winner's wallet was capped)", inline=False)
        await interaction.response.edit_message(embed=em, view=None)

    @nextcord.ui.button(label="❌ Decline", style=nextcord.ButtonStyle.danger)
    async def decline(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.opponent.id:
            return await interaction.response.send_message("This challenge isn't for you!", ephemeral=True)
        self.resolved = True
        await interaction.response.edit_message(content=f"{self.opponent.mention} declined the coinflip.", embed=None, view=None)

    async def on_timeout(self):
        if not self.resolved:
            self.resolved = True


class Coinflip(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank

    @nextcord.slash_command(name="coinflip", description="Challenge a player to a 50/50 coinflip")
    async def coinflip(self, interaction: nextcord.Interaction,
                       member: nextcord.Member = nextcord.SlashOption(description="Who to challenge"),
                       amount: int = nextcord.SlashOption(description="Wager", min_value=100, max_value=50_000)):
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("You can't challenge that!", ephemeral=True)

        await self.bank.open_acc(interaction.user)
        await self.bank.open_acc(member)
        ch = await self.bank.get_acc(interaction.user)
        op = await self.bank.get_acc(member)
        if ch[1] < amount:
            return await interaction.response.send_message("❌ You don't have enough Pesos.", ephemeral=True)
        if op[1] < amount:
            return await interaction.response.send_message(f"❌ {member.mention} doesn't have **{amount:,} Pesos** to match.", ephemeral=True)

        em = nextcord.Embed(title="🪙 Coinflip Challenge", color=0xf1c40f)
        em.description = f"{interaction.user.mention} challenges {member.mention} to a coinflip for **{amount:,} Pesos**!"
        em.set_footer(text=f"{member.name} has 60 seconds to accept")

        view = CoinflipView(interaction.user, member, amount, self.bank)
        await interaction.response.send_message(content=member.mention, embed=em, view=view)


def setup(client):
    client.add_cog(Coinflip(client))

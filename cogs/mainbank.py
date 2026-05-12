import nextcord
from nextcord.ext import commands
from datetime import datetime
from base import EconomyBot


class MainBank(commands.Cog):
    def __init__(self, client: EconomyBot):
        self.client = client
        self.bank = self.client.db.bank

    def _build_lb_embed(self, title: str, members, footer: str, color=0xffd700):
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        if not members:
            desc = "*No one has money yet...*"
        else:
            lines = []
            for i, (user, amt) in enumerate(members, start=1):
                prefix = medals.get(i, f"`#{i:>2}`")
                lines.append(f"{prefix}  **{user}** — `{amt:,}₱`")
            desc = "\n".join(lines)
        em = nextcord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())
        em.set_footer(text=footer)
        return em

    @nextcord.slash_command(name="leaderboard", description="Show the global richest cartel members")
    async def leaderboard(self, interaction: nextcord.Interaction):
        rows = await self.bank.get_networth_lb()
        members = []
        for member in rows:
            if len(members) >= 15:
                break
            user = self.client.get_user(member[0])
            if user:
                members.append((user, member[1]))
        em = self._build_lb_embed("🌍  Global Richest Cartel Members", members, "Global • All servers")
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="serverlb", description="Show the richest members in this server")
    async def server_leaderboard(self, interaction: nextcord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        rows = await self.bank.get_networth_lb()
        members = []
        for member in rows:
            if len(members) >= 15:
                break
            user = interaction.guild.get_member(member[0])
            if user:
                members.append((user, member[1]))
        em = self._build_lb_embed(f"🏆  {interaction.guild.name} Richest", members, f"Server-only • {interaction.guild.name}")
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="balance", description="Check your (or someone else's) balance")
    async def balance(self, interaction: nextcord.Interaction,
                      member: nextcord.Member = nextcord.SlashOption(description="Member to check (default: yourself)", required=False)):
        user = member or interaction.user
        if user.bot:
            return await interaction.response.send_message("Bots don't have an account", ephemeral=True)
        await self.bank.open_acc(user)
        users = await self.bank.get_acc(user)
        wallet_amt = users[1]
        bank_amt   = users[2]
        net_amt    = wallet_amt + bank_amt
        cap        = await self.bank.get_wallet_cap(user)
        # wallet bar
        pct = int((wallet_amt / cap) * 10) if cap > 0 else 0
        bar = "▰" * pct + "▱" * (10 - pct)
        em = nextcord.Embed(
            title=f"💼  {user.name}'s Balance",
            color=0x2ecc71,
        )
        em.set_thumbnail(url=user.display_avatar.url)
        em.add_field(name="💵  Wallet", value=f"**{wallet_amt:,}** / {cap:,}₱\n`{bar}`", inline=False)
        em.add_field(name="🏦  Bank",   value=f"**{bank_amt:,}₱**",  inline=True)
        em.add_field(name="📊  Net",    value=f"**{net_amt:,}₱**",   inline=True)
        em.set_footer(text="More trap houses → bigger wallet cap • /deposit to safe-store cash")
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="deposit", description="Move money from your wallet to your bank")
    async def deposit(self, interaction: nextcord.Interaction,
                      amount: str = nextcord.SlashOption(description="Amount (or 'all')")):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        wallet = users[1]
        if amount.lower() == "all":
            amt = wallet
        else:
            if not amount.isdigit() or int(amount) <= 0:
                return await interaction.response.send_message("❌ Enter a positive amount or 'all'.", ephemeral=True)
            amt = int(amount)
        if wallet <= 0:
            return await interaction.response.send_message("❌ Your wallet is empty.", ephemeral=True)
        moved = await self.bank.deposit(interaction.user, amt)
        await interaction.response.send_message(f"🏦 Deposited **{moved:,} Pesos** into your bank.")

    @nextcord.slash_command(name="withdraw", description="Move money from your bank to your wallet")
    async def withdraw(self, interaction: nextcord.Interaction,
                       amount: str = nextcord.SlashOption(description="Amount (or 'all')")):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        bank_amt = users[2]
        if amount.lower() == "all":
            amt = bank_amt
        else:
            if not amount.isdigit() or int(amount) <= 0:
                return await interaction.response.send_message("❌ Enter a positive amount or 'all'.", ephemeral=True)
            amt = int(amount)
        if bank_amt <= 0:
            return await interaction.response.send_message("❌ Your bank is empty.", ephemeral=True)
        moved, _, cap_short = await self.bank.withdraw(interaction.user, amt)
        msg = f"💵 Withdrew **{moved:,} Pesos** to your wallet."
        if cap_short > 0:
            msg += f"\n⚠️ Wallet was capped — **{cap_short:,}** couldn't fit. Buy more trap houses."
        await interaction.response.send_message(msg)


def setup(client):
    client.add_cog(MainBank(client))

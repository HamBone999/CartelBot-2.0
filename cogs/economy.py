import nextcord
from nextcord.ext import commands
from numpy import random
import time
from base import EconomyBot


class Economy(commands.Cog):
    def __init__(self, client: EconomyBot):
        self.client = client
        self.bank = self.client.db.bank
        self._daily_cd: dict = {}
        self._weekly_cd: dict = {}
        self._monthly_cd: dict = {}

    async def _do_reward(self, interaction, cd_dict, cd_seconds, lo, hi, label):
        uid, now = interaction.user.id, time.time()
        remaining = cd_seconds - (now - cd_dict.get(uid, 0))
        if remaining > 0:
            d = int(remaining) // 86400
            h = (int(remaining) % 86400) // 3600
            m = (int(remaining) % 3600) // 60
            parts = []
            if d: parts.append(f"{d}d")
            if h: parts.append(f"{h}h")
            if m or not parts: parts.append(f"{m}m")
            return await interaction.response.send_message(f"⏳ Come back in **{' '.join(parts)}**", ephemeral=True)
        cd_dict[uid] = now
        await self.bank.open_acc(interaction.user)
        base = int(random.randint(lo, hi))
        mult = await self.bank.get_rank_multiplier(interaction.user)
        final = int(base * mult)
        added, lost = await self.bank.add_to_wallet(interaction.user, final)
        msg = f"💵 {label}: **{added:,} Pesos** (base {base:,} • rank x{mult:.2f})"
        if lost > 0:
            msg += f"\n⚠️ Wallet capped — **{lost:,}** Pesos lost. Deposit more often."
        await interaction.response.send_message(msg)

    @nextcord.slash_command(name="daily", description="Collect your daily reward")
    async def daily(self, interaction: nextcord.Interaction):
        await self._do_reward(interaction, self._daily_cd, 86400, 600, 1300, "Daily")

    @nextcord.slash_command(name="weekly", description="Collect your weekly reward")
    async def weekly(self, interaction: nextcord.Interaction):
        await self._do_reward(interaction, self._weekly_cd, 604800, 2800, 4800, "Weekly")

    @nextcord.slash_command(name="monthly", description="Collect your monthly reward")
    async def monthly(self, interaction: nextcord.Interaction):
        await self._do_reward(interaction, self._monthly_cd, 2592000, 12000, 22000, "Monthly")


def setup(client):
    client.add_cog(Economy(client))

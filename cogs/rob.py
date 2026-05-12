import nextcord
from nextcord.ext import commands
import random
import time
from modules.bank_funcs import RANK_NAMES

GID = [547181131766693900]


class Rob(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv
        self._cd: dict = {}

    @nextcord.slash_command(name="rob", description="Try to rob another player (30 min cooldown)")
    async def rob(self, interaction: nextcord.Interaction,
                  member: nextcord.Member = nextcord.SlashOption(description="Who to rob")):
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("You can't rob that!", ephemeral=True)

        uid, now, cd = interaction.user.id, time.time(), 1800
        remaining = cd - (now - self._cd.get(uid, 0))
        if remaining > 0:
            m, s = int(remaining) // 60, int(remaining) % 60
            return await interaction.response.send_message(f"⏳ Heat's still on you. Wait **{m}m {s}s**.", ephemeral=True)

        await self.bank.open_acc(interaction.user)
        await self.bank.open_acc(member)
        await self.inv.open_acc(member)

        target_data = await self.bank.get_acc(member)
        target_wallet = target_data[1]
        if target_wallet < 500:
            return await interaction.response.send_message(f"💸 {member.mention} is broke — not worth the risk.", ephemeral=True)

        # Padlock blocks the rob, burns one lock
        if await self.inv.has_item(member, "padlock"):
            await self.inv.consume(member, "padlock", 1)
            self._cd[uid] = now
            em = nextcord.Embed(title="🔒 PADLOCKED!", color=0xffa500)
            em.description = f"You tried to rob {member.mention} but their wallet was **padlocked**! Lock broke off."
            return await interaction.response.send_message(embed=em)

        self._cd[uid] = now

        # ITEM BONUSES
        ski_mask    = await self.inv.has_item(interaction.user, "ski_mask")
        lockpick    = await self.inv.has_item(interaction.user, "lockpick_set")
        crowbar     = await self.inv.has_item(interaction.user, "crowbar")
        success_rate = 0.45 + (0.10 if ski_mask else 0) + (0.10 if lockpick else 0) + (0.05 if crowbar else 0)

        bonus_lines = []
        if ski_mask: bonus_lines.append("🎭 Ski Mask: +10% success")
        if lockpick: bonus_lines.append("🔓 Lockpick: +10% success")
        if crowbar:  bonus_lines.append("🔧 Crowbar: +5% success")

        if random.random() < success_rate:
            steal_pct = random.uniform(0.10, 0.30)
            stolen = min(int(target_wallet * steal_pct), 8000)
            await self.bank.update_acc(member, -stolen)
            added, lost = await self.bank.add_to_wallet(interaction.user, stolen)
            await self.bank.update_acc(interaction.user, 8, mode="heat")
            new_xp, new_rank, leveled = await self.bank.award_xp(interaction.user, 20)

            em = nextcord.Embed(title="🏴‍☠️ Rob successful!", color=0x2ecc71)
            em.description = f"You jumped {member.mention} and got away with **{added:,} Pesos**!"
            em.add_field(name="Heat", value="+8", inline=True)
            em.add_field(name="XP", value="+20", inline=True)
            em.add_field(name="Success rate", value=f"{int(success_rate*100)}%", inline=True)
            if bonus_lines:
                em.add_field(name="Item bonuses", value="\n".join(bonus_lines), inline=False)
            if lost > 0:
                em.add_field(name="⚠️ Wallet cap", value=f"**{lost:,}** Pesos lost", inline=False)
            if leveled:
                em.add_field(name="🎉 RANKED UP!", value=f"You're now a **{RANK_NAMES[new_rank]}**!", inline=False)
            await interaction.response.send_message(embed=em)
        else:
            fine = random.randint(800, 2500)
            users = await self.bank.get_acc(interaction.user)
            fine = min(fine, users[1])
            await self.bank.update_acc(interaction.user, -fine)
            await self.bank.update_acc(interaction.user, 15, mode="heat")
            em = nextcord.Embed(title="🚨 Rob FAILED!", color=0xff0000)
            em.description = f"{member.mention} pulled out a piece — you bolted but dropped **{fine:,} Pesos** running."
            em.add_field(name="Heat", value="+15", inline=True)
            em.add_field(name="Success rate", value=f"{int(success_rate*100)}%", inline=True)
            if bonus_lines:
                em.add_field(name="Item bonuses (applied)", value="\n".join(bonus_lines), inline=False)
            await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Rob(client))

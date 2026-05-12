import nextcord
from nextcord.ext import commands
import random
from modules.bank_funcs import RANK_NAMES

GID = [547181131766693900]

TARGETS = {
    "gas_station": {"emoji": "⛽", "name": "Gas Station",  "stake":  1_000, "min_p": 2, "base_success": 0.70, "payout_low":  2_000, "payout_high":  5_000, "xp":  20, "min_rank": 0},
    "liquor_store":{"emoji": "🥃", "name": "Liquor Store", "stake":  3_000, "min_p": 2, "base_success": 0.60, "payout_low":  6_000, "payout_high": 14_000, "xp":  40, "min_rank": 1},
    "bank":        {"emoji": "🏦", "name": "Bank",         "stake": 10_000, "min_p": 3, "base_success": 0.45, "payout_low": 22_000, "payout_high": 50_000, "xp":  80, "min_rank": 2},
    "casino":      {"emoji": "🎰", "name": "Casino",       "stake": 25_000, "min_p": 4, "base_success": 0.35, "payout_low": 60_000, "payout_high":150_000, "xp": 150, "min_rank": 3},
}


class HeistLobby(nextcord.ui.View):
    def __init__(self, host: nextcord.Member, target_key: str, bank, inv, channel):
        super().__init__(timeout=60)
        self.host = host
        self.target_key = target_key
        self.target = TARGETS[target_key]
        self.bank = bank
        self.inv = inv
        self.channel = channel
        self.participants = [host]
        self.started = False

    def _build_embed(self):
        t = self.target
        em = nextcord.Embed(title=f"{t['emoji']} HEIST: {t['name']}", color=0xe74c3c)
        em.description = (
            f"**{self.host.mention}** is planning a heist!\n\n"
            f"Stake: **{t['stake']:,} Pesos** per player\n"
            f"Min players: **{t['min_p']}** • Min rank: **{RANK_NAMES[t['min_rank']]}**\n"
            f"Payout pool: **{t['payout_low']:,}–{t['payout_high']:,}**\n"
            f"Base success: **{int(t['base_success']*100)}%** (+5% per extra player, +bonuses)\n\n"
            f"**Crew ({len(self.participants)}):** " + ", ".join(p.mention for p in self.participants)
        )
        em.set_footer(text="60-second lobby — owning getaway_van / armored_suv / walkie_talkie boosts success")
        return em

    @nextcord.ui.button(label="🤝 Join Heist", style=nextcord.ButtonStyle.success)
    async def join(self, button, interaction: nextcord.Interaction):
        if self.started:
            return await interaction.response.send_message("Too late — heist already started.", ephemeral=True)
        if interaction.user in self.participants:
            return await interaction.response.send_message("You're already in the crew.", ephemeral=True)
        if interaction.user.bot:
            return await interaction.response.send_message("Bots don't rob banks.", ephemeral=True)

        # rank gate
        rank = await self.bank.get_rank(interaction.user)
        if rank < self.target["min_rank"]:
            return await interaction.response.send_message(
                f"❌ You need to be at least **{RANK_NAMES[self.target['min_rank']]}** to hit this target.", ephemeral=True)

        # heat gate
        heat = await self.bank.get_heat(interaction.user)
        if heat >= 50:
            return await interaction.response.send_message(
                f"🌡️ You're too hot ({heat}/100) — lay low first.", ephemeral=True)

        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < self.target["stake"]:
            return await interaction.response.send_message(
                f"❌ You need **{self.target['stake']:,} Pesos** in your wallet to join.", ephemeral=True)

        self.participants.append(interaction.user)
        await interaction.response.edit_message(embed=self._build_embed(), view=self)

    @nextcord.ui.button(label="🚀 Start Heist", style=nextcord.ButtonStyle.danger)
    async def start(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.host.id:
            return await interaction.response.send_message("Only the host can start.", ephemeral=True)
        if self.started:
            return
        if len(self.participants) < self.target["min_p"]:
            return await interaction.response.send_message(
                f"Need at least **{self.target['min_p']}** players. You have **{len(self.participants)}**.", ephemeral=True)
        self.started = True
        await interaction.response.defer()
        await self._run(interaction)

    async def on_timeout(self):
        if not self.started:
            self.started = True
            if len(self.participants) >= self.target["min_p"]:
                try:
                    await self._run(None)
                except Exception:
                    pass

    async def _run(self, interaction):
        t = self.target
        stake = t["stake"]
        for p in self.participants:
            await self.bank.update_acc(p, -stake)

        # Item bonuses across crew
        item_bonus = 0.0
        crew_bonuses = []
        for p in self.participants:
            if await self.inv.has_item(p, "getaway_van"):
                item_bonus += 0.05
                crew_bonuses.append(f"🚐 {p.display_name} has Getaway Van (+5%)")
            if await self.inv.has_item(p, "armored_suv"):
                item_bonus += 0.10
                crew_bonuses.append(f"🛡️ {p.display_name} has Armored SUV (+10%)")
            if await self.inv.has_item(p, "walkie_talkie"):
                item_bonus += 0.03
                crew_bonuses.append(f"📻 {p.display_name} has Walkie Talkie (+3%)")
            if await self.inv.has_item(p, "police_scanner"):
                item_bonus += 0.05
                crew_bonuses.append(f"📡 {p.display_name} has Police Scanner (+5%)")

        success_chance = min(0.95, t["base_success"] + 0.05 * (len(self.participants) - t["min_p"]) + item_bonus)
        success = random.random() < success_chance

        em = nextcord.Embed(title=f"{t['emoji']} {t['name']} Heist — RESULT", color=0x2ecc71 if success else 0xff0000)
        em.add_field(name="Crew", value=", ".join(p.mention for p in self.participants), inline=False)
        em.add_field(name="Success roll", value=f"**{int(success_chance*100)}%** chance", inline=True)

        if success:
            total_pot = random.randint(t["payout_low"], t["payout_high"])
            share = total_pot // len(self.participants)
            lines = []
            for p in self.participants:
                added, lost = await self.bank.add_to_wallet(p, share)
                await self.bank.award_xp(p, t["xp"])
                msg = f"{p.mention} → **+{added:,}**"
                if lost > 0:
                    msg += f" (lost {lost:,} to cap)"
                lines.append(msg)
            em.add_field(name="💰 Pot", value=f"**{total_pot:,} Pesos** split {len(self.participants)} ways", inline=True)
            em.add_field(name="Share", value=f"**{share:,} each • +{t['xp']} XP**", inline=True)
            em.add_field(name="Payout", value="\n".join(lines), inline=False)
        else:
            for p in self.participants:
                await self.bank.update_acc(p, 25, mode="heat")
            em.add_field(name="💀 Outcome", value=f"The heist FAILED. Stakes ({stake:,} each) lost. Crew **+25 heat**.", inline=False)

        if crew_bonuses:
            em.add_field(name="🎒 Item bonuses", value="\n".join(crew_bonuses[:10]), inline=False)

        for child in self.children:
            child.disabled = True
        if interaction:
            await interaction.followup.send(embed=em)
        else:
            await self.channel.send(embed=em)


class Heist(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv

    @nextcord.slash_command(name="heist", description="Plan a multiplayer heist")
    async def heist(self, interaction: nextcord.Interaction,
                    target: str = nextcord.SlashOption(
                        description="Target to hit",
                        choices={
                            "⛽ Gas Station (any rank)": "gas_station",
                            "🥃 Liquor Store (Trap Star+)": "liquor_store",
                            "🏦 Bank (Lieutenant+)": "bank",
                            "🎰 Casino (Capo+)": "casino",
                        })):
        t = TARGETS[target]
        # rank check for host
        rank = await self.bank.get_rank(interaction.user)
        if rank < t["min_rank"]:
            return await interaction.response.send_message(
                f"❌ You need to be **{RANK_NAMES[t['min_rank']]}** to host this heist.", ephemeral=True)
        # heat check
        heat = await self.bank.get_heat(interaction.user)
        if heat >= 50:
            return await interaction.response.send_message(
                f"🌡️ Too hot to host ({heat}/100). Lay low first.", ephemeral=True)
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < t["stake"]:
            return await interaction.response.send_message(
                f"❌ You need **{t['stake']:,} Pesos** in your wallet to host.", ephemeral=True)

        view = HeistLobby(interaction.user, target, self.bank, self.inv, interaction.channel)
        await interaction.response.send_message(embed=view._build_embed(), view=view)


def setup(client):
    client.add_cog(Heist(client))

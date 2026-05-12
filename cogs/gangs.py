import nextcord
from nextcord.ext import commands
import random
import time


class ShootConfirmView(nextcord.ui.View):
    def __init__(self, user_id: int, member: nextcord.Member):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.member = member
        self.confirmed = False

    @nextcord.ui.button(label="🔫 Shoot", style=nextcord.ButtonStyle.danger)
    async def confirm_shoot(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)
        self.confirmed = True
        self.stop()
        await interaction.response.defer()

    @nextcord.ui.button(label="Cancel", style=nextcord.ButtonStyle.secondary)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This is not for you!", ephemeral=True)
        self.stop()
        await interaction.response.send_message("Shoot cancelled.", ephemeral=True)


class Gangs(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv
        self._shoot_cd: dict = {}

    GUNS = {
        "pistol": {"cost": 4500, "damage": 35, "name": "🔫 Pistol"},
        "uzi": {"cost": 12500, "damage": 55, "name": "🔫 Uzi"},
        "ak": {"cost": 28000, "damage": 75, "name": "🔫 AK-47"},
        "rocket": {"cost": 65000, "damage": 95, "name": "🚀 Rocket Launcher"}
    }

    @nextcord.slash_command(name="buy_gun", description="Buy a weapon for street fights")
    async def buy_gun(self, interaction: nextcord.Interaction,
                      gun: str = nextcord.SlashOption(
                          description="Choose your weapon",
                          choices={"🔫 Pistol (4,500)": "pistol", "🔫 Uzi (12,500)": "uzi",
                                   "🔫 AK-47 (28,000)": "ak", "🚀 Rocket Launcher (65,000)": "rocket"})):
        cost = self.GUNS[gun]["cost"]
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < cost:
            return await interaction.response.send_message("❌ Not enough cash!", ephemeral=True)
        await self.bank.update_acc(interaction.user, -cost)
        await self.bank.update_acc(interaction.user, gun, mode="gun")
        await interaction.response.send_message(f"🔫 You armed up with a **{self.GUNS[gun]['name']}**!")

    @nextcord.slash_command(name="shoot", description="Shoot another player and try to steal their Pesos (1 min cooldown)")
    async def blickyshoot(self, interaction: nextcord.Interaction,
                          member: nextcord.Member = nextcord.SlashOption(description="Who to shoot")):
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("You can't shoot that!", ephemeral=True)

        uid, now, cd = interaction.user.id, time.time(), 60
        remaining = cd - (now - self._shoot_cd.get(uid, 0))
        if remaining > 0:
            return await interaction.response.send_message(f"⏳ Gun's hot — wait **{int(remaining)}s**", ephemeral=True)

        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        gun = users[5] if len(users) > 5 else "none"
        if gun == "none":
            return await interaction.response.send_message("You don't have a gun! Buy one with `/buy_gun`", ephemeral=True)

        em = nextcord.Embed(title="🔫 Confirm Shoot", description=f"Are you sure you want to shoot **{member}**?", color=0xff0000)
        view = ShootConfirmView(interaction.user.id, member)
        await interaction.response.send_message(embed=em, view=view)
        await view.wait()

        if view.confirmed:
            self._shoot_cd[uid] = now
            damage = {"pistol": 35, "uzi": 55, "ak": 75, "rocket": 95}.get(gun, 30)
            if random.randint(1, 100) <= damage:
                # Bulletproof vest deflects 50% of hits
                if await self.inv.has_item(member, "bulletproof_vest") and random.random() < 0.5:
                    await self.inv.consume(member, "bulletproof_vest", 1)
                    await self.bank.update_acc(interaction.user, 5, mode="heat")
                    return await interaction.edit_original_message(
                        content=f"🦺 **DEFLECTED!** {member.mention}'s bulletproof vest soaked the round — vest destroyed but they took no money loss.",
                        embed=None, view=None)
                target_data = await self.bank.get_acc(member)
                target_wallet = target_data[1] if target_data else 0
                if target_wallet <= 0:
                    return await interaction.edit_original_message(content=f"💸 {member.mention} is broke — nothing to steal!", embed=None, view=None)
                stolen = min(random.randint(5000, 20000), target_wallet)
                await self.bank.update_acc(member, -stolen)
                added, lost = await self.bank.add_to_wallet(interaction.user, stolen)
                await self.bank.update_acc(interaction.user, 10, mode="heat")
                new_xp, new_rank, leveled = await self.bank.award_xp(interaction.user, 15)
                msg = f"🔫 **BOOM!** You hit {member.mention} and stole **{added:,} Pesos**! (+15 XP)"
                if lost > 0:
                    msg += f"\n⚠️ Wallet cap — {lost:,} Pesos lost."
                if leveled:
                    from modules.bank_funcs import RANK_NAMES
                    msg += f"\n🎉 **RANKED UP** to {RANK_NAMES[new_rank]}!"
                await interaction.edit_original_message(content=msg, embed=None, view=None)
            else:
                await self.bank.update_acc(interaction.user, 15, mode="heat")
                await interaction.edit_original_message(content=f"😣 You missed {member.mention}! Heat +15", embed=None, view=None)

    @nextcord.slash_command(name="claimterritory", description="Claim a territory for passive income (costs 75,000 Pesos)")
    async def claimterritory(self, interaction: nextcord.Interaction,
                              territory_name: str = nextcord.SlashOption(
                                  description="Name your territory (3–25 characters)",
                                  min_length=3, max_length=25)):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[7] is not None:
            return await interaction.response.send_message("You already own a territory!", ephemeral=True)
        if users[1] < 75000:
            return await interaction.response.send_message("❌ You need **75,000 Pesos** to claim a territory!", ephemeral=True)
        await self.bank.update_acc(interaction.user, -75000)
        await self.bank.update_acc(interaction.user, territory_name, mode="territory")
        await interaction.response.send_message(f"🏙️ **{territory_name}** is now your territory!\nPassive income every 10 minutes.")

    @nextcord.slash_command(name="abandonterritory", description="Give up your territory")
    async def abandonterritory(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[7] is None:
            return await interaction.response.send_message("You don't own any territory.", ephemeral=True)
        await self.bank.update_acc(interaction.user, None, mode="territory")
        await interaction.response.send_message("🏚️ You abandoned your territory.")

    @nextcord.slash_command(name="territory", description="Check which territory you own")
    async def territory(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        terr = users[7]
        if terr is None:
            return await interaction.response.send_message("You don't own any territory.\nUse `/claimterritory`")
        await interaction.response.send_message(f"🏙️ You own **{terr}** territory.")


def setup(client):
    client.add_cog(Gangs(client))

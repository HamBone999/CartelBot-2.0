import nextcord
from nextcord.ext import commands
import time


class TycoonView(nextcord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @nextcord.ui.button(label="💰 Collect Income", style=nextcord.ButtonStyle.success, emoji="📦")
    async def collect(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("This is not your tycoon!", ephemeral=True)
        await self.game.collect_income(interaction)

    @nextcord.ui.button(label="Upgrade Trap House", style=nextcord.ButtonStyle.primary, emoji="🏠")
    async def upgrade(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("This is not your tycoon!", ephemeral=True)
        await self.game.upgrade_house(interaction)

    @nextcord.ui.button(label="Buy New Spot", style=nextcord.ButtonStyle.primary, emoji="🛒")
    async def buy_spot(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.game.user_id:
            return await interaction.response.send_message("This is not your tycoon!", ephemeral=True)
        await self.game.buy_new_spot(interaction)


class TrapHouseTycoon(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.last_collect: dict = {}

    @nextcord.slash_command(name="traptycoon", description="Open your Trap House Tycoon empire")
    async def traptycoon(self, interaction: nextcord.Interaction):
        game = TycoonGame(self, interaction)
        await game.start()


class TycoonGame:
    def __init__(self, cog, interaction: nextcord.Interaction):
        self.cog = cog
        self.interaction = interaction
        self.user_id = interaction.user.id
        self.houses = 1
        self.level = 1
        self.base_income = 800
        self.upgrade_cost = 12000

    async def _save(self):
        await self.cog.bank.update_tycoon(self.interaction.user, self.houses, self.level)

    def get_current_upgrade_cost(self):
        return int(self.upgrade_cost * (1.1 ** (self.houses - 1)))

    def build_embed(self):
        income = self.base_income * self.houses
        wallet_cap_bonus = self.houses * 10_000
        em = nextcord.Embed(
            title="🏚️  Trap House Tycoon",
            description="*Your empire of trap houses. Collect, expand, dominate the block.*\n​",
            color=0x16a085,
        )
        em.add_field(name="🏠 Houses",      value=f"**{self.houses}**",                          inline=True)
        em.add_field(name="📈 Level",       value=f"**{self.level}**",                           inline=True)
        em.add_field(name="💵 Per 10 min",  value=f"**{income:,}₱**",                            inline=True)
        em.add_field(name="🔨 Upgrade",     value=f"**{self.get_current_upgrade_cost():,}₱**",   inline=True)
        em.add_field(name="🛒 New Spot",    value="**80,000₱**",                                  inline=True)
        em.add_field(name="🎒 Cap Bonus",   value=f"**+{wallet_cap_bonus:,}₱**",                  inline=True)
        em.set_footer(text="10-min cooldown on Collect • Each house: +10k wallet cap, +10 plant slots")
        return em

    async def start(self):
        row = await self.cog.bank.get_tycoon(self.interaction.user)
        self.houses, self.level = row[0], row[1]
        await self.interaction.response.send_message(embed=self.build_embed(), view=TycoonView(self))

    async def collect_income(self, interaction: nextcord.Interaction):
        now = time.time()
        last = self.cog.last_collect.get(self.user_id, 0)
        if now - last < 600:
            remaining = int(600 - (now - last))
            return await interaction.response.send_message(f"⏳ **Cooldown active!** {remaining//60}m {remaining%60}s left.", ephemeral=True)
        self.cog.last_collect[self.user_id] = now
        income = self.base_income * self.houses
        await self.cog.bank.update_acc(self.interaction.user, income)
        await interaction.response.send_message(f"💰 Collected **{income:,} Pesos** from your trap houses!", ephemeral=True)
        await interaction.message.edit(embed=self.build_embed())

    async def upgrade_house(self, interaction: nextcord.Interaction):
        cost = self.get_current_upgrade_cost()
        await self.cog.bank.open_acc(self.interaction.user)
        users = await self.cog.bank.get_acc(self.interaction.user)
        if users[1] < cost:
            return await interaction.response.send_message(f"❌ You need **{cost:,} Pesos** to upgrade!", ephemeral=True)
        await self.cog.bank.update_acc(self.interaction.user, -cost)
        self.houses += 1
        self.level += 1
        await self._save()
        await interaction.response.send_message(f"🏠 Trap House upgraded! You now have **{self.houses}** houses.", ephemeral=True)
        await interaction.message.edit(embed=self.build_embed())

    async def buy_new_spot(self, interaction: nextcord.Interaction):
        cost = 80000
        await self.cog.bank.open_acc(self.interaction.user)
        users = await self.cog.bank.get_acc(self.interaction.user)
        if users[1] < cost:
            return await interaction.response.send_message(f"❌ You need **{cost:,} Pesos** for a new spot!", ephemeral=True)
        await self.cog.bank.update_acc(self.interaction.user, -cost)
        self.houses += 1
        self.level += 1
        await self._save()
        await interaction.response.send_message(f"🛒 New trap spot acquired! Total houses: **{self.houses}**", ephemeral=True)
        await interaction.message.edit(embed=self.build_embed())


def setup(client):
    client.add_cog(TrapHouseTycoon(client))

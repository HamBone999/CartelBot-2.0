import nextcord
from nextcord.ext import commands

GID = [547181131766693900]


class Gift(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv

    @nextcord.slash_command(name="send", description="Send Pesos from your wallet to another player")
    async def send_cash(self, interaction: nextcord.Interaction,
                        member: nextcord.Member = nextcord.SlashOption(description="Who to send to"),
                        amount: int = nextcord.SlashOption(description="Amount to send", min_value=1)):
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("You can't send to that.", ephemeral=True)

        await self.bank.open_acc(interaction.user)
        await self.bank.open_acc(member)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < amount:
            return await interaction.response.send_message(f"❌ You only have **{users[1]:,} Pesos** in your wallet.", ephemeral=True)

        await self.bank.update_acc(interaction.user, -amount)
        added, lost = await self.bank.add_to_wallet(member, amount)

        em = nextcord.Embed(title="💸 Cash Sent", color=0x00ff88)
        em.description = f"{interaction.user.mention} sent **{added:,} Pesos** to {member.mention}"
        if lost > 0:
            # refund the over-cap portion to the sender's wallet
            await self.bank.add_to_wallet(interaction.user, lost)
            em.add_field(name="⚠️ Recipient wallet was capped", value=f"**{lost:,} Pesos** refunded to you.", inline=False)
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="gift", description="Give an item from your inventory to another player")
    async def gift(self, interaction: nextcord.Interaction,
                   member: nextcord.Member = nextcord.SlashOption(description="Who to gift to"),
                   item: str = nextcord.SlashOption(description="Exact item name (e.g. weed_seeds)"),
                   amount: int = nextcord.SlashOption(description="How many", min_value=1, default=1)):
        if member.bot or member.id == interaction.user.id:
            return await interaction.response.send_message("You can't gift that.", ephemeral=True)

        item_name = item.lower().strip().replace(" ", "_")
        valid = {i["name"] for i in self.inv.shop_items}
        if item_name not in valid:
            return await interaction.response.send_message(
                f"❌ Unknown item `{item}`. Check `/inventory` for exact names.", ephemeral=True)

        await self.inv.open_acc(interaction.user)
        await self.inv.open_acc(member)
        qty_data = await self.inv.update_acc(interaction.user, 0, item_name)
        owned = qty_data[0] if qty_data else 0
        if owned < amount:
            return await interaction.response.send_message(f"❌ You only have **{owned}x {item_name}**.", ephemeral=True)

        await self.inv.update_acc(interaction.user, -amount, item_name)
        await self.inv.update_acc(member, amount, item_name)

        em = nextcord.Embed(title="🎁 Item Gifted", color=0x00ff88)
        em.description = f"{interaction.user.mention} gave **{amount}x {item_name.replace('_', ' ').title()}** to {member.mention}"
        await interaction.response.send_message(embed=em)

    @gift.on_autocomplete("item")
    async def gift_item_autocomplete(self, interaction: nextcord.Interaction, item: str):
        suggestions = [i["name"] for i in self.inv.shop_items if item.lower() in i["name"]]
        await interaction.response.send_autocomplete(suggestions[:25])


def setup(client):
    client.add_cog(Gift(client))

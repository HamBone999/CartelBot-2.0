import nextcord
from nextcord.ext import commands
from base import EconomyBot
from modules.inventory_funcs import SHOP_CATEGORIES

GID = [547181131766693900]


class Inventory(commands.Cog):
    def __init__(self, client: EconomyBot):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv

    @nextcord.slash_command(name="inventory", description="View your (or someone else's) inventory")
    async def inventory(self, interaction: nextcord.Interaction,
                        member: nextcord.Member = nextcord.SlashOption(description="Member to check (default: yourself)", required=False)):
        user = member or interaction.user
        if user.bot:
            return await interaction.response.send_message("Bots don't have an account", ephemeral=True)
        await self.inv.open_acc(user)

        em = nextcord.Embed(title=f"🎒  {user.name}'s Inventory", color=0x3498db)
        em.set_thumbnail(url=user.display_avatar.url)

        total_value = 0
        total_items = 0
        # group by category
        for cat_key, (cat_emoji, cat_label) in SHOP_CATEGORIES.items():
            cat_items = [i for i in self.inv.shop_items if i.get("category") == cat_key]
            lines = []
            for item in cat_items:
                qty = await self.inv.get_qty(user, item["name"])
                if qty > 0:
                    name = item["name"].replace("_", " ").title()
                    value = qty * item["cost"]
                    total_value += value
                    total_items += qty
                    lines.append(f"**{qty}x** {item['info'].split()[0] if item['info'] else '📦'} {name} *({value:,}₱)*")
            if lines:
                em.add_field(name=f"{cat_emoji}  {cat_label}", value="\n".join(lines), inline=False)

        if total_items == 0:
            em.description = "*Inventory is empty — try `/search` or `/shop`*"
        else:
            em.description = f"**{total_items}** items • Total value: **{total_value:,}₱**\n​"

        em.set_footer(text="Sell cooking items with /cartelmenu → Sell All • Gift items with /gift")
        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Inventory(client))

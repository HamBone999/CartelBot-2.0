import nextcord
from nextcord.ext import commands
from modules.inventory_funcs import SHOP_CATEGORIES

GID = [547181131766693900]

# Color theme per category (matches /chelp vibe)
CATEGORY_COLORS = {
    "cooking":  0x27ae60,
    "gear":     0x3498db,
    "weapons":  0xe74c3c,
    "vehicles": 0x95a5a6,
    "luxury":   0xf1c40f,
    "misc":     0x9b59b6,
}

CATEGORY_BLURBS = {
    "cooking":  "Raw materials for cooking ops & search drops.",
    "gear":     "Wearable items + gadgets with passive bonuses.",
    "weapons":  "Melee tools and explosives for the rough work.",
    "vehicles": "Speed, escape, intimidate. Heist success boosts.",
    "luxury":   "Status symbols. Sell for big returns when desperate.",
    "misc":     "Consumables, edge cases, and chaos in a bag.",
}

# Tips per category — non-obvious gameplay info
CATEGORY_TIPS = {
    "cooking": [
        "🧪 **Gas Mask** — +25% search yield, -50% search heat",
        "👁️ **Night Vision** — +15% search yield",
    ],
    "gear": [
        "🔒 **Padlock** — blocks one rob attempt (consumed)",
        "🦺 **Bulletproof Vest** — 50% chance to deflect a shoot",
        "🎭 **Ski Mask** — +10% rob success",
        "🔓 **Lockpick Set** — +10% rob success",
        "📡 **Police Scanner** — -25% search heat, +5% heist success",
    ],
    "weapons": [
        "🔧 **Crowbar** — +5% rob success",
        "Most weapons sell for their cost — store wealth in them",
    ],
    "vehicles": [
        "🚐 **Getaway Van** — +5% heist success",
        "🛡️ **Armored SUV** — +10% heist success",
    ],
    "luxury": [
        "💸 Best 'storage' for wealth — buy then sell back when needed",
    ],
    "misc": [
        "📫 **Mystery Package** — random cash/items (`/use`)",
        "🎒 **Sus Backpack** — 50/50 jackpot or bomb (`/use`)",
        "💼 **Blood Money Case** — 40k–100k Pesos (`/use`)",
        "🧴 **Bleach** — `/use` to drop heat",
    ],
}


def home_embed(wallet: int, cap: int, total_items: int) -> nextcord.Embed:
    em = nextcord.Embed(
        title="🛒  Cartel Shop",
        description=(
            f"**{total_items} items** across **{len(SHOP_CATEGORIES)} categories**.\n"
            f"💵 Your wallet: **{wallet:,}** / {cap:,} Pesos\n​"
        ),
        color=0x00ff88,
    )
    rows = []
    for key, (emoji, label) in SHOP_CATEGORIES.items():
        rows.append(f"{emoji}  **{label}** — {CATEGORY_BLURBS[key]}")
    em.add_field(name="​", value="\n\n".join(rows), inline=False)
    em.set_footer(text="Pick a category from the dropdown ↓")
    return em


def category_embed(active_cat: str, shop_items, wallet: int, cap: int) -> nextcord.Embed:
    emoji, label = SHOP_CATEGORIES[active_cat]
    items = [i for i in shop_items if i.get("category") == active_cat]
    em = nextcord.Embed(
        title=f"{emoji}  {label}",
        description=f"*{CATEGORY_BLURBS[active_cat]}*\n💵 Wallet: **{wallet:,}** / {cap:,} Pesos\n​",
        color=CATEGORY_COLORS[active_cat],
    )
    # split items into two columns if many
    lines = []
    for i in items:
        afford = "✅" if wallet >= i["cost"] else "🔒"
        lines.append(f"{afford} {i['info']} — **{i['cost']:,}₱**")
    em.add_field(name=f"**{len(items)} items**", value="\n".join(lines), inline=False)
    if CATEGORY_TIPS.get(active_cat):
        em.add_field(name="💡 **What these do**", value="\n".join(f"• {t}" for t in CATEGORY_TIPS[active_cat]), inline=False)
    em.set_footer(text="🏠 Home • dropdown to buy 1x • ✅ = affordable, 🔒 = can't afford")
    return em


class ShopView(nextcord.ui.View):
    def __init__(self, user_id: int, shop_cog, wallet: int, cap: int, active_cat: str = None):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.shop = shop_cog
        self.wallet = wallet
        self.cap = cap
        self.active_cat = active_cat
        self._rebuild()

    def _rebuild(self):
        self.clear_items()
        # Row 0: category dropdown
        options = []
        for key, (emoji, label) in SHOP_CATEGORIES.items():
            options.append(nextcord.SelectOption(
                label=label, value=key, emoji=emoji, description=CATEGORY_BLURBS[key][:100]
            ))
        cat_select = nextcord.ui.Select(placeholder="📁 Pick a category…", options=options, row=0)
        async def cat_cb(interaction: nextcord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This shop isn't yours!", ephemeral=True)
            self.active_cat = cat_select.values[0]
            # refresh wallet
            users = await self.shop.bank.get_acc(interaction.user)
            self.wallet = users[1]
            self.cap = await self.shop.bank.get_wallet_cap(interaction.user)
            self._rebuild()
            await interaction.response.edit_message(embed=category_embed(self.active_cat, self.shop.inv.shop_items, self.wallet, self.cap), view=self)
        cat_select.callback = cat_cb
        self.add_item(cat_select)

        # Row 1: item-buy dropdown if a category is active
        if self.active_cat:
            items = [i for i in self.shop.inv.shop_items if i.get("category") == self.active_cat]
            if items:
                opts = []
                for i in items[:25]:
                    name = i["name"].replace("_", " ").title()
                    desc = f"{i['cost']:,} Pesos — {i['info'][:60]}"
                    opts.append(nextcord.SelectOption(label=name, value=i["name"], description=desc[:100]))
                item_select = nextcord.ui.Select(placeholder="🛒 Buy 1x…", options=opts, row=1)
                view_ref = self
                async def item_cb(interaction: nextcord.Interaction):
                    if interaction.user.id != view_ref.user_id:
                        return await interaction.response.send_message("This shop isn't yours!", ephemeral=True)
                    await view_ref.shop.buy_item(interaction, item_select.values[0], 1)
                item_select.callback = item_cb
                self.add_item(item_select)

        # Row 2: home button
        home_btn = nextcord.ui.Button(label="🏠 Home", style=nextcord.ButtonStyle.secondary, row=2)
        async def home_cb(interaction: nextcord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This shop isn't yours!", ephemeral=True)
            self.active_cat = None
            users = await self.shop.bank.get_acc(interaction.user)
            self.wallet = users[1]
            self.cap = await self.shop.bank.get_wallet_cap(interaction.user)
            self._rebuild()
            total = len(self.shop.inv.shop_items)
            await interaction.response.edit_message(embed=home_embed(self.wallet, self.cap, total), view=self)
        home_btn.callback = home_cb
        self.add_item(home_btn)


class Shop(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv

    @nextcord.slash_command(name="shop", description="Browse the Cartel item shop")
    async def shop(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        cap = await self.bank.get_wallet_cap(interaction.user)
        view = ShopView(interaction.user.id, self, users[1], cap, active_cat=None)
        await interaction.response.send_message(embed=home_embed(users[1], cap, len(self.inv.shop_items)), view=view)

    async def buy_item(self, interaction: nextcord.Interaction, item_name: str, quantity: int = 1):
        await self.bank.open_acc(interaction.user)
        await self.inv.open_acc(interaction.user)
        item = next((i for i in self.inv.shop_items if i["name"] == item_name), None)
        if not item:
            return await interaction.response.send_message("❌ Item not found.", ephemeral=True)
        cost = item["cost"] * quantity
        users = await self.bank.get_acc(interaction.user)
        if users[1] < cost:
            return await interaction.response.send_message(
                f"❌ You need **{cost:,} Pesos** to buy that. Wallet: **{users[1]:,}**", ephemeral=True)
        await self.bank.update_acc(interaction.user, -cost)
        await self.inv.update_acc(interaction.user, quantity, item_name)
        await interaction.response.send_message(
            f"✅ Bought **{quantity}x {item['name'].replace('_', ' ').title()}** — **-{cost:,} Pesos**", ephemeral=True)


def setup(client):
    client.add_cog(Shop(client))

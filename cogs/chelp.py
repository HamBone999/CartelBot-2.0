import nextcord
from nextcord.ext import commands

GID = [547181131766693900]

# ── Category Data ────────────────────────────────────────────────────────────
CATEGORIES = {
    "economy": {
        "emoji": "💵",
        "label": "Economy & Banking",
        "blurb": "Earn, store, and move your Pesos. Rewards scale with your rank.",
        "color": 0x2ecc71,
        "commands": [
            ("/daily",     "Daily reward (24h cooldown)"),
            ("/weekly",    "Weekly reward (7d cooldown)"),
            ("/monthly",   "Monthly reward (30d cooldown)"),
            ("/work",      "Random hustle, 1h cooldown — 200–4,500 Pesos"),
            ("/balance",   "Show your wallet, bank, and wallet cap"),
            ("/deposit",   "Move wallet → bank (or 'all')"),
            ("/withdraw",  "Move bank → wallet (or 'all')"),
            ("/send",      "Send Pesos to another player"),
            ("/gift",      "Give items to another player"),
        ],
    },
    "cartel": {
        "emoji": "🌿",
        "label": "Cartel Life",
        "blurb": "Run the streets, grow your stash, sell for profit.",
        "color": 0x27ae60,
        "commands": [
            ("/search",     "Search the streets for items (5m cooldown)"),
            ("/plant",      "Plant weed seeds (10 per trap house, 1h grow)"),
            ("/harvest",    "Collect grown weed — 500–900 Pesos per seed"),
            ("/shop",       "Buy items across 6 categories (70+ items)"),
            ("/inventory",  "View your inventory"),
            ("/profile",    "Your empire stats — rank, XP, heat, gear"),
            ("/cartelmenu", "Quick action menu"),
            ("/hoodrank",   "Quick rank + XP check"),
        ],
    },
    "combat": {
        "emoji": "🔫",
        "label": "Combat & Crime",
        "blurb": "Take from others — or lose what you've got. Mind the heat.",
        "color": 0xe74c3c,
        "commands": [
            ("/rob",          "Try to rob another player (30m cooldown)"),
            ("/shoot",        "Shoot a player to steal cash (1m cooldown)"),
            ("/buy_gun",      "Buy a weapon — pistol → rocket launcher"),
            ("/heist",        "Plan a multiplayer heist (rank-gated)"),
        ],
        "tips": [
            "🔒 **Padlock** (`/shop`) blocks one rob attempt — stack them",
            "🎭 Ski Mask + 🔓 Lockpick + 🔧 Crowbar boost rob success",
            "🦺 Bulletproof Vest deflects 50% of shoot hits",
        ],
    },
    "heat": {
        "emoji": "🌡️",
        "label": "Heat Management",
        "blurb": "The feds are always watching. Lay low or get raided.",
        "color": 0xff5500,
        "commands": [
            ("/heat",     "Check current heat level"),
            ("/laylow",   "Cool off — 1h cooldown, -25 heat"),
            ("/use",      "Consume an item (bleach, burner_barrel, etc.)"),
        ],
        "tips": [
            "🧴 **Bleach** — `/use bleach` removes 25 heat",
            "🛢️ **Burner Barrel** — `/use burner_barrel` removes 15 heat",
            "🪪 **Dirty Cop Badge** — `/use dirty_cop_badge` removes 50 heat",
            "🛂 **Fake Passport** — `/use fake_passport` resets heat to 0",
            "⚠️ **Heat 50+** blocks joining heists",
            "🚔 **Heat 70+** triggers random police raids on /search",
        ],
    },
    "crew": {
        "emoji": "🏴‍☠️",
        "label": "Crew & Territory",
        "blurb": "Build your organization. Claim your block.",
        "color": 0xf39c12,
        "commands": [
            ("/createcrew",        "Create a crew — costs 50,000 Pesos"),
            ("/joincrew",          "Join an existing crew"),
            ("/leavecrew",         "Leave your current crew"),
            ("/crew",              "View your crew info"),
            ("/claimterritory",    "Claim turf — costs 75,000 Pesos"),
            ("/abandonterritory",  "Give up your territory"),
            ("/territory",         "View your territory"),
        ],
    },
    "games": {
        "emoji": "🎮",
        "label": "Gambling & Games",
        "blurb": "House always wins. Unless you're the house.",
        "color": 0x9b59b6,
        "commands": [
            ("/slots",      "Spin the slots — jackpot pays 15x on triple 7️⃣"),
            ("/blackjack",  "Cartel Blackjack — natural pays 3:2"),
            ("/coinflip",   "Challenge a player to a 50/50 wager"),
            ("/roll",       "Dice roll — high risk, high reward"),
            ("/traptycoon", "Trap House Tycoon — passive income & wallet cap"),
        ],
    },
    "stats": {
        "emoji": "🏆",
        "label": "Stats & Leaderboards",
        "blurb": "See who's on top of the food chain.",
        "color": 0x3498db,
        "commands": [
            ("/leaderboard",  "Global richest players (top 15)"),
            ("/serverlb",     "Richest players in this server"),
            ("/profile",      "Detailed personal stats"),
        ],
    },
    "ranks": {
        "emoji": "🎓",
        "label": "Rank Progression",
        "blurb": "XP unlocks bigger heists and bigger payouts.",
        "color": 0xe67e22,
        "commands": [
            ("Corner Boy",  "0 XP — Starting rank • 1.00× payout"),
            ("Trap Star",   "100 XP — 1.05× payout, unlocks Liquor Store heist"),
            ("Lieutenant",  "500 XP — 1.10× payout, unlocks Bank heist"),
            ("Capo",        "2,000 XP — 1.15× payout, unlocks Casino heist"),
            ("Boss",        "5,000 XP — 1.25× payout"),
            ("Kingpin",     "10,000 XP — 1.50× payout — top rank 👑"),
        ],
        "tips": [
            "XP per action: search +5 • work/harvest +10 • shoot +15 • rob +20",
            "Heist XP scales with target: gas station +20 → casino +150",
        ],
    },
}

ORDER = ["economy", "cartel", "combat", "heat", "crew", "games", "stats", "ranks"]


def home_embed() -> nextcord.Embed:
    em = nextcord.Embed(
        title="📖  CartelBot Codex",
        description=(
            "Welcome to the **CartelBot Codex**. Pick a category below to view its commands.\n\n"
            "💡 *Tip: most items in `/shop` provide passive bonuses — check the category descriptions to find them.*"
        ),
        color=0x00ff88,
    )
    rows = []
    for key in ORDER:
        c = CATEGORIES[key]
        rows.append(f"{c['emoji']}  **{c['label']}** — {c['blurb']}")
    em.add_field(name="​", value="\n\n".join(rows), inline=False)
    em.set_footer(text="Use the dropdown ↓ to dive in")
    return em


def category_embed(key: str) -> nextcord.Embed:
    c = CATEGORIES[key]
    em = nextcord.Embed(
        title=f"{c['emoji']}  {c['label']}",
        description=f"*{c['blurb']}*",
        color=c["color"],
    )
    # Commands table
    if c.get("commands"):
        lines = "\n".join(f"`{name}` — {desc}" for name, desc in c["commands"])
        em.add_field(name="**Commands**", value=lines, inline=False)
    # Tips
    if c.get("tips"):
        em.add_field(name="💡 **Tips**", value="\n".join(f"• {t}" for t in c["tips"]), inline=False)
    em.set_footer(text="🏠 Home to return • dropdown to switch category")
    return em


class HelpView(nextcord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self._add_select()
        self._add_home_button()

    def _add_select(self):
        options = []
        for key in ORDER:
            c = CATEGORIES[key]
            options.append(nextcord.SelectOption(
                label=c["label"], value=key, emoji=c["emoji"], description=c["blurb"][:100]
            ))
        select = nextcord.ui.Select(placeholder="📖 Pick a category…", options=options, row=0)
        async def callback(interaction: nextcord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This menu isn't yours!", ephemeral=True)
            await interaction.response.edit_message(embed=category_embed(select.values[0]), view=self)
        select.callback = callback
        self.add_item(select)

    def _add_home_button(self):
        btn = nextcord.ui.Button(label="🏠 Home", style=nextcord.ButtonStyle.secondary, row=1)
        async def home_cb(interaction: nextcord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("This menu isn't yours!", ephemeral=True)
            await interaction.response.edit_message(embed=home_embed(), view=self)
        btn.callback = home_cb
        self.add_item(btn)


class Help(commands.Cog):
    def __init__(self, client):
        self.client = client

    @nextcord.slash_command(name="chelp", description="Open the CartelBot command codex")
    async def chelp(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(embed=home_embed(), view=HelpView(interaction.user.id))


def setup(client):
    client.add_cog(Help(client))

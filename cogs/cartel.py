import nextcord
from nextcord.ext import commands
import random
import time

from modules.bank_funcs import RANK_NAMES, RANK_THRESHOLDS, calc_rank

GID = [547181131766693900]


def progress_bar(value, max_value, length=10):
    if max_value <= 0:
        return "▱" * length
    filled = int(length * min(value, max_value) / max_value)
    return "▰" * filled + "▱" * (length - filled)


def menu_home_embed(user_name: str) -> nextcord.Embed:
    em = nextcord.Embed(
        title="🧭  Cartel Command Hub",
        description=(
            f"Hey **{user_name}** — what's the move?\n​"
        ),
        color=0x00ff88,
    )
    em.add_field(
        name="​",
        value=(
            "💼  **Profile** — View your rank, XP, heat & gear\n\n"
            "💰  **Sell All** — Dump every cooking item in your inventory\n\n"
            "🌡️  **Heat Status** — Quick heat check\n\n"
            "🏴‍☠️  **How to Rob** — Tips on robbing & padlocks"
        ),
        inline=False,
    )
    em.set_footer(text="Pick an action below ↓")
    return em


class CartelMenuView(nextcord.ui.View):
    def __init__(self, user_id: int, cartel_cog):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.cartel = cartel_cog

    @nextcord.ui.button(label="Profile", style=nextcord.ButtonStyle.primary, emoji="💼", row=0)
    async def profile_button(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu is not for you!", ephemeral=True)
        await self.cartel._send_profile(interaction)

    @nextcord.ui.button(label="Sell All", style=nextcord.ButtonStyle.success, emoji="💰", row=0)
    async def sell_all_button(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu is not for you!", ephemeral=True)
        await self.cartel.sell_all_items(interaction)

    @nextcord.ui.button(label="Heat", style=nextcord.ButtonStyle.secondary, emoji="🌡️", row=0)
    async def heat_button(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu is not for you!", ephemeral=True)
        heat = await self.cartel.bank.get_heat(interaction.user)
        bar = progress_bar(min(heat, 100), 100)
        status = "🟢 Cool" if heat < 30 else ("🟡 Watch your back" if heat < 60 else ("🟠 They're sniffing around" if heat < 80 else "🔴 RUN"))
        em = nextcord.Embed(title="🌡️ Heat Status",
                             description=f"**{heat}/100**\n{bar}\n\n{status}",
                             color=0xff5500 if heat >= 60 else 0xffd700 if heat >= 30 else 0x00ff88)
        em.set_footer(text="/laylow to cool off • /use bleach/fake_passport to drop heat")
        await interaction.response.send_message(embed=em, ephemeral=True)

    @nextcord.ui.button(label="How to Rob", style=nextcord.ButtonStyle.danger, emoji="🏴‍☠️", row=0)
    async def rob_button(self, button, interaction: nextcord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("This menu is not for you!", ephemeral=True)
        em = nextcord.Embed(title="🏴‍☠️ How to Rob", color=0xe74c3c)
        em.description = (
            "Use `/rob @user` to try and rob another player.\n"
            "**45%** base success rate. Steal up to **8,000 Pesos** on success.\n\n"
            "**Boost your odds:**\n"
            "🎭 Ski Mask — +10%\n"
            "🔓 Lockpick Set — +10%\n"
            "🔧 Crowbar — +5%\n\n"
            "**Defend yourself:**\n"
            "🔒 Buy a padlock from `/shop` — blocks one rob"
        )
        await interaction.response.send_message(embed=em, ephemeral=True)


class Cartel(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv
        self._search_cd: dict = {}

    ITEM_EMOTES = {
        "weed_seeds": "🌱", "coke_kit": "❄️", "meth": "💎",
        "battery": "🔋", "pseudo": "💊", "acetone": "🧪",
        "sulfuric": "🧪", "red_phos": "🔥", "coffee_filters": "☕",
        "scale": "⚖️", "ziplock": "📦", "lighter": "🔥",
        "gloves": "🧤", "muriatic": "🧪", "iodine": "🧪"
    }

    GUNS = {
        "pistol": {"cost": 4500, "damage": 35, "name": "🔫 Pistol"},
        "uzi": {"cost": 12500, "damage": 55, "name": "🔫 Uzi"},
        "ak": {"cost": 28000, "damage": 75, "name": "🔫 AK-47"},
        "rocket": {"cost": 65000, "damage": 95, "name": "🚀 Rocket Launcher"}
    }

    async def random_encounter(self, interaction: nextcord.Interaction):
        # Heat raises the encounter base rate
        heat = await self.bank.get_heat(interaction.user)
        roll = random.random()
        heat_bonus = (heat / 100) * 0.20  # +20% encounter chance at max heat

        if roll < 0.06 + heat_bonus:
            await self.bank.open_acc(interaction.user)
            users = await self.bank.get_acc(interaction.user)
            robbed = int(users[1] * 0.075)
            await self.bank.update_acc(interaction.user, -robbed)
            await self.inv.reset_all_items(interaction.user)
            em = nextcord.Embed(title="🧟‍♂️ CRACKHEAD ATTACK!", description="A wild crackhead sprints out yelling **'GIMME THAT SHIT BRO!'**", color=0xff0000)
            em.add_field(name="💸 Stolen", value=f"**{robbed:,} Pesos** (7.5%)", inline=True)
            em.add_field(name="📦 Looted", value="**ALL your items**", inline=True)
            await interaction.response.send_message(embed=em)
            return True

        if roll < 0.09 + heat_bonus:
            await self.bank.open_acc(interaction.user)
            users = await self.bank.get_acc(interaction.user)
            loss = int(users[1] * 0.35)
            await self.bank.update_acc(interaction.user, -loss)
            await self.bank.update_acc(interaction.user, 20, mode="heat")
            em = nextcord.Embed(title="🚨 POLICE RAID!", description="Cops kicked in the door! They took 35% of your cash and raised your heat!", color=0x0000ff)
            await interaction.response.send_message(embed=em)
            return True

        if roll < 0.105 + heat_bonus:
            await self.bank.open_acc(interaction.user)
            users = await self.bank.get_acc(interaction.user)
            wallet = users[1]
            if wallet > 0:
                phrases = [
                    "A **Super Rock Head** tackles you, steals your wallet, and screams 'THIS IS MY HOUSE NOW BITCH!' while humping your leg",
                    "The Super Rock Head rips your cash out and yells 'I'M THE KING OF THE STREETS!' while doing the worm on the sidewalk",
                    "He looks you dead in the eyes and says 'Gimme that bag or the phallic object gets it' and takes everything",
                    "Super Rock Head steals all your wallet money while twerking aggressively and screaming 'YEEEEEET!'",
                ]
                await self.bank.update_acc(interaction.user, -wallet)
                em = nextcord.Embed(title="🪨 SUPER ROCK HEAD ATTACK!", description=random.choice(phrases), color=0x800080)
                em.add_field(name="💸 Stolen", value=f"**ALL {wallet:,} Pesos**", inline=False)
                await interaction.response.send_message(embed=em)
            return True
        return False

    async def sell_all_items(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        await self.inv.open_acc(interaction.user)
        # cooking supplies sell well, others give base price
        prices = {
            "weed_seeds": 320, "coke_kit": 1250, "meth": 2800, "battery": 125,
            "pseudo": 650, "acetone": 220, "sulfuric": 330, "red_phos": 950,
            "coffee_filters": 60, "scale": 450, "ziplock": 45, "lighter": 30,
            "gloves": 95, "muriatic": 280, "iodine": 540
        }
        mult = await self.bank.get_rank_multiplier(interaction.user)
        total = 0
        for item in self.ITEM_EMOTES.keys():
            qty = await self.inv.get_qty(interaction.user, item)
            if qty > 0:
                total += int(prices.get(item, 100) * qty * mult)
                await self.inv.update_acc(interaction.user, -qty, item)
        if total > 0:
            added, lost = await self.bank.add_to_wallet(interaction.user, total)
            msg = f"💰 **Sold everything!** You received **{added:,} Pesos** (rank x{mult:.2f})."
            if lost > 0:
                msg += f"\n⚠️ Wallet was capped — **{lost:,}** Pesos lost."
            await interaction.response.send_message(msg)
        else:
            await interaction.response.send_message("You have no items to sell.")

    async def _send_profile(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        await self.inv.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        balance = users[1]
        heat  = users[3] if len(users) > 3 else 0
        rank  = users[4] if len(users) > 4 else 0
        gun   = users[5] if len(users) > 5 else "none"
        xp    = await self.bank.get_xp(interaction.user)
        rank_name = RANK_NAMES[min(rank, 5)]

        # XP toward next rank
        if rank < 5:
            cur_thr = RANK_THRESHOLDS[rank]
            next_thr = RANK_THRESHOLDS[rank + 1]
            xp_in_rank = xp - cur_thr
            xp_needed = next_thr - cur_thr
            rank_bar = progress_bar(xp_in_rank, xp_needed)
            rank_progress = f"**{xp:,} XP** • Next: {next_thr:,} ({xp_in_rank}/{xp_needed})\n{rank_bar}"
        else:
            rank_progress = f"**{xp:,} XP** • MAX RANK 👑"

        em = nextcord.Embed(title=f"💼 {interaction.user.name}'s Cartel Empire", color=0x00ff88)
        em.set_thumbnail(url=interaction.user.display_avatar.url)
        em.add_field(name=f"🏚️ Rank — {rank_name}", value=rank_progress, inline=False)
        em.add_field(name="🔫 Equipped", value=self.GUNS.get(gun, {"name": "None"})["name"] if gun != "none" else "None", inline=True)
        em.add_field(name="💵 Balance", value=f"{balance:,} Pesos", inline=True)
        em.add_field(name="🌡️ Heat", value=f"{heat}/100\n{progress_bar(min(heat, 100), 100)}", inline=False)

        inv_list = []
        for item in self.ITEM_EMOTES:
            qty = await self.inv.get_qty(interaction.user, item)
            if qty > 0:
                inv_list.append(f"{self.ITEM_EMOTES[item]} **{qty}x {item.replace('_', ' ')}**")
        em.add_field(name="📦 Cooking Inventory", value="\n".join(inv_list) if inv_list else "Empty", inline=False)
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="search", description="Search the streets for items (5 min cooldown)")
    async def search(self, interaction: nextcord.Interaction):
        uid, now, cd = interaction.user.id, time.time(), 300
        remaining = cd - (now - self._search_cd.get(uid, 0))
        if remaining > 0:
            return await interaction.response.send_message(f"⏳ Lay low for **{int(remaining)}s** before searching again.", ephemeral=True)
        self._search_cd[uid] = now

        # heat consequence: extra raid roll at high heat
        heat = await self.bank.get_heat(interaction.user)
        if heat >= 70 and random.random() < 0.25:
            await self.bank.open_acc(interaction.user)
            users = await self.bank.get_acc(interaction.user)
            loss = int(users[1] * 0.20)
            await self.bank.update_acc(interaction.user, -loss)
            await self.bank.update_acc(interaction.user, 10, mode="heat")
            em = nextcord.Embed(title="🚔 HEAT IS TOO HIGH — POLICE RAID!", color=0xff0000)
            em.description = f"Your heat ({heat}/100) brought the feds. You lost **{loss:,} Pesos** and gained more heat."
            em.set_footer(text="Use /laylow or /use bleach to cool off.")
            return await interaction.response.send_message(embed=em)

        if await self.random_encounter(interaction):
            return

        await self.bank.open_acc(interaction.user)

        # ITEM EFFECTS
        has_gas    = await self.inv.has_item(interaction.user, "gas_mask")
        has_nv     = await self.inv.has_item(interaction.user, "night_vision")
        has_scan   = await self.inv.has_item(interaction.user, "police_scanner")

        yield_mult = 1.0 + (0.25 if has_gas else 0) + (0.15 if has_nv else 0)
        heat_mult  = (0.5 if has_gas else 1.0) * (0.75 if has_scan else 1.0)

        heat_gain = max(1, int(random.randint(3, 8) * heat_mult))
        await self.bank.update_acc(interaction.user, heat_gain, mode="heat")

        common = ["battery", "acetone", "sulfuric", "coffee_filters", "ziplock", "lighter", "gloves", "muriatic"]
        rare   = ["pseudo", "red_phos", "scale", "iodine", "meth"]
        ultra  = ["coke_kit"]
        tier = random.choices(["common", "rare", "ultra"], weights=[75, 10, 15], k=1)[0]

        found = {}
        rolls = random.randint(1, 3)
        for _ in range(rolls):
            pool = common if tier == "common" else (rare if tier == "rare" else ultra)
            base = random.randint(2, 5) if tier == "common" else (random.randint(1, 3) if tier == "rare" else random.randint(1, 2))
            qty = max(1, int(base * yield_mult))
            item = random.choice(pool)
            found[item] = found.get(item, 0) + qty
        for item, qty in found.items():
            await self.inv.update_acc(interaction.user, qty, item)

        # XP
        new_xp, new_rank, leveled = await self.bank.award_xp(interaction.user, 5)

        items_list = "\n".join(f"{self.ITEM_EMOTES.get(item, '📦')} **{qty}x {item.replace('_', ' ')}**" for item, qty in found.items())
        bonus_lines = []
        if has_gas:  bonus_lines.append("🧪 Gas Mask: +25% yield, -50% heat")
        if has_nv:   bonus_lines.append("👁️ Night Vision: +15% yield")
        if has_scan: bonus_lines.append("📡 Scanner: -25% heat")
        bonus_text = ("\n" + "\n".join(bonus_lines)) if bonus_lines else ""

        msg = f"🔎 You found:\n{items_list}\n\n**Heat +{heat_gain}** • **+5 XP**{bonus_text}"
        if leveled:
            msg += f"\n\n🎉 **RANKED UP!** You're now a **{RANK_NAMES[new_rank]}**!"
        await interaction.response.send_message(msg)

    @nextcord.slash_command(name="profile", description="View your cartel empire stats")
    async def profile(self, interaction: nextcord.Interaction):
        await self._send_profile(interaction)

    @nextcord.slash_command(name="hoodrank", description="Check your current rank in the cartel")
    async def hoodrank(self, interaction: nextcord.Interaction):
        rank = await self.bank.get_rank(interaction.user)
        xp = await self.bank.get_xp(interaction.user)
        await interaction.response.send_message(f"🏚️ **{interaction.user.name}** — **{RANK_NAMES[min(rank, 5)]}** • {xp:,} XP")

    @nextcord.slash_command(name="cartelmenu", description="Open the cartel action hub")
    async def cartelmenu(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(
            embed=menu_home_embed(interaction.user.name),
            view=CartelMenuView(interaction.user.id, self))

    @nextcord.slash_command(name="heat", description="Check your current heat level")
    async def heat_cmd(self, interaction: nextcord.Interaction):
        heat = await self.bank.get_heat(interaction.user)
        bar = progress_bar(min(heat, 100), 100)
        status = "🟢 Cool" if heat < 30 else ("🟡 Watch your back" if heat < 60 else ("🟠 They're sniffing around" if heat < 80 else "🔴 RUN — feds are close"))
        em = nextcord.Embed(title="🌡️ Heat Status", color=0xff5500 if heat >= 60 else 0xffd700 if heat >= 30 else 0x00ff88)
        em.description = f"**{heat}/100**\n{bar}\n\n{status}"
        em.set_footer(text="Use /laylow, /use bleach, /use burner_barrel, or /use fake_passport to reduce heat")
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="laylow", description="Lay low to reduce your heat (1 hour cooldown)")
    async def laylow(self, interaction: nextcord.Interaction):
        last = await self.bank.get_laylow_at(interaction.user)
        now = int(time.time())
        if now - last < 3600:
            remaining = 3600 - (now - last)
            m, s = remaining // 60, remaining % 60
            return await interaction.response.send_message(f"⏳ You can lay low again in **{m}m {s}s**.", ephemeral=True)
        reduced = await self.bank.reduce_heat(interaction.user, 25)
        await self.bank.set_laylow_at(interaction.user, now)
        if reduced > 0:
            await interaction.response.send_message(f"🛋️ You laid low for an hour. **Heat -{reduced}**.")
        else:
            await interaction.response.send_message("🛋️ You laid low. Your heat was already at 0.")

    @nextcord.slash_command(name="plant", description="Plant weed seeds — 10 per trap house, 1 hour to grow")
    async def plant(self, interaction: nextcord.Interaction,
                    amount: int = nextcord.SlashOption(description="How many weed seeds to plant", min_value=1)):
        existing = await self.bank.get_plant(interaction.user)
        if existing:
            planted_at = existing[1]
            remaining = int((planted_at + 3600) - time.time())
            if remaining > 0:
                m, s = remaining // 60, remaining % 60
                return await interaction.response.send_message(
                    f"🌱 You already have **{existing[0]}** seeds in the ground! Ready in **{m}m {s}s**.", ephemeral=True)
            else:
                return await interaction.response.send_message(
                    "🌿 Your plants are already ready! Use `/harvest` to collect them.", ephemeral=True)

        tycoon = await self.bank.get_tycoon(interaction.user)
        houses = tycoon[0]
        max_plants = houses * 10
        if amount > max_plants:
            return await interaction.response.send_message(
                f"🏚️ You can only plant **{max_plants} seeds** ({houses} trap {'house' if houses == 1 else 'houses'} × 10). "
                f"Buy more with `/traptycoon`.", ephemeral=True)

        await self.inv.open_acc(interaction.user)
        owned = await self.inv.get_qty(interaction.user, "weed_seeds")
        if owned < amount:
            return await interaction.response.send_message(
                f"❌ You only have **{owned}x weed seeds**. Buy more from `/shop`.", ephemeral=True)

        await self.inv.update_acc(interaction.user, -amount, "weed_seeds")
        await self.bank.set_plant(interaction.user, amount, int(time.time()))

        em = nextcord.Embed(title="🌱 Seeds Planted!", color=0x2ecc71)
        em.add_field(name="Seeds in ground", value=f"**{amount}x weed seeds**", inline=True)
        em.add_field(name="Ready in", value="**1 hour**", inline=True)
        await interaction.response.send_message(embed=em)

    @nextcord.slash_command(name="harvest", description="Harvest your grown weed for Pesos")
    async def harvest(self, interaction: nextcord.Interaction):
        plant = await self.bank.get_plant(interaction.user)
        if not plant:
            return await interaction.response.send_message("🌱 You have nothing planted.", ephemeral=True)
        quantity, planted_at = plant
        remaining = int((planted_at + 3600) - time.time())
        if remaining > 0:
            m, s = remaining // 60, remaining % 60
            return await interaction.response.send_message(f"⏳ Not ready yet — **{m}m {s}s** left.", ephemeral=True)

        mult = await self.bank.get_rank_multiplier(interaction.user)
        payout_per = int(random.randint(500, 900) * mult)
        total = payout_per * quantity
        added, lost = await self.bank.add_to_wallet(interaction.user, total)
        await self.bank.clear_plant(interaction.user)
        new_xp, new_rank, leveled = await self.bank.award_xp(interaction.user, 10)

        em = nextcord.Embed(title="🌿 Harvest Complete!", color=0x27ae60)
        em.add_field(name="🌱 Seeds harvested", value=f"**{quantity}x**", inline=True)
        em.add_field(name="💰 Payout", value=f"**{added:,} Pesos** (rank x{mult:.2f})", inline=True)
        em.add_field(name="🎓 XP", value="**+10 XP**", inline=True)
        if lost > 0:
            em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost", inline=False)
        if leveled:
            em.add_field(name="🎉 RANKED UP!", value=f"You're now a **{RANK_NAMES[new_rank]}**!", inline=False)
        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Cartel(client))

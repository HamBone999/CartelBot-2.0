import nextcord
from nextcord.ext import commands
import random
import time
from modules.bank_funcs import RANK_NAMES

GID = [547181131766693900]

JOBS = [
    ("ran a corner for the day",          400, 1200, 1.0),
    ("moved a brick across town",        1200, 2800, 0.9),
    ("drove a getaway for some guys",    1000, 2200, 0.9),
    ("intimidated a snitch into silence", 500, 1400, 1.0),
    ("robbed a bodega",                   800, 2000, 0.8),
    ("delivered to a Kingpin personally",2500, 4500, 0.3),
    ("scored a side hustle on craigslist",200,  900, 1.0),
    ("collected protection money",       1500, 3000, 0.7),
    ("babysat a stash house overnight",   900, 1900, 0.9),
    ("did a tattoo in the back of a bar", 400, 1100, 1.0),
]
BAD_OUTCOMES = [
    ("got pulled over and had to pay a bribe", 500, 1500),
    ("dropped your wallet running from the feds", 300, 1000),
    ("paid a guy who turned out to be a cop", 800, 1800),
]


class Work(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv
        self._cd: dict = {}

    @nextcord.slash_command(name="work", description="Hustle for cash (1 hour cooldown)")
    async def work(self, interaction: nextcord.Interaction):
        uid, now, cd = interaction.user.id, time.time(), 3600
        remaining = cd - (now - self._cd.get(uid, 0))
        if remaining > 0:
            m, s = int(remaining) // 60, int(remaining) % 60
            return await interaction.response.send_message(f"⏳ You're burned out. Come back in **{m}m {s}s**.", ephemeral=True)
        self._cd[uid] = now

        await self.bank.open_acc(interaction.user)

        # 10% chance something goes wrong
        if random.random() < 0.10:
            desc, lo, hi = random.choice(BAD_OUTCOMES)
            loss = random.randint(lo, hi)
            users = await self.bank.get_acc(interaction.user)
            loss = min(loss, users[1])
            if loss > 0:
                await self.bank.update_acc(interaction.user, -loss)
            em = nextcord.Embed(title="😬 Bad day at work", description=f"You {desc}.", color=0xff0000)
            em.add_field(name="Lost", value=f"**{loss:,} Pesos**")
            return await interaction.response.send_message(embed=em)

        weights = [j[3] for j in JOBS]
        job = random.choices(JOBS, weights=weights, k=1)[0]
        desc, lo, hi, _ = job
        payout = random.randint(lo, hi)

        # Item + rank bonuses
        cookbook_mult = 1.20 if await self.inv.has_item(interaction.user, "cartel_cookbook") else 1.0
        rank_mult = await self.bank.get_rank_multiplier(interaction.user)
        final_payout = int(payout * cookbook_mult * rank_mult)

        added, lost = await self.bank.add_to_wallet(interaction.user, final_payout)
        new_xp, new_rank, leveled = await self.bank.award_xp(interaction.user, 10)

        em = nextcord.Embed(title="💼 Day's work", description=f"You {desc}.", color=0x00ff88)
        em.add_field(name="Earned", value=f"**{added:,} Pesos**", inline=True)
        em.add_field(name="XP", value="**+10**", inline=True)
        em.add_field(name="Multipliers", value=f"Rank x{rank_mult:.2f}" + (" • 📖 Cookbook x1.20" if cookbook_mult > 1 else ""), inline=False)
        if lost > 0:
            em.add_field(name="⚠️ Wallet capped", value=f"Lost **{lost:,}** Pesos.", inline=False)
        if leveled:
            em.add_field(name="🎉 RANKED UP", value=f"You're now a **{RANK_NAMES[new_rank]}**!", inline=False)
        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Work(client))

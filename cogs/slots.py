import nextcord
from nextcord.ext import commands
import random

GID = [547181131766693900]

REELS = ["🍒", "🍋", "🔔", "🍀", "💎", "7️⃣"]
PAYOUTS_3 = {"7️⃣": 15.0, "💎": 8.0, "🍀": 5.0, "🔔": 3.0, "🍋": 2.5, "🍒": 2.0}
PAYOUT_2 = 1.2


class Slots(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank

    @nextcord.slash_command(name="slots", description="Spin the slot machine (200–25,000 Pesos)")
    async def slots(self, interaction: nextcord.Interaction,
                    bet: int = nextcord.SlashOption(description="Amount to bet", min_value=200, max_value=25_000)):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < bet:
            return await interaction.response.send_message("❌ You don't have enough Pesos!", ephemeral=True)

        await self.bank.update_acc(interaction.user, -bet)
        reels = [random.choice(REELS) for _ in range(3)]
        line = f"｜ {reels[0]} ｜ {reels[1]} ｜ {reels[2]} ｜"

        # determine payout
        if reels[0] == reels[1] == reels[2]:
            mult = PAYOUTS_3[reels[0]]
            payout = int(bet * mult)
            added, lost = await self.bank.add_to_wallet(interaction.user, payout)
            color = 0xffd700
            title = f"🎰 JACKPOT! Triple {reels[0]}"
            result = f"You won **{added:,} Pesos** ({mult}x)!"
            if lost > 0:
                result += f"\n⚠️ Wallet cap hit — **{lost:,}** Pesos lost. Deposit more often!"
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            payout = int(bet * PAYOUT_2)
            added, lost = await self.bank.add_to_wallet(interaction.user, payout)
            color = 0x00ff88
            title = "🎰 Pair! Small win"
            result = f"You won **{added:,} Pesos** ({PAYOUT_2}x)"
            if lost > 0:
                result += f"\n⚠️ Wallet cap hit — **{lost:,}** Pesos lost."
        else:
            color = 0xff0000
            title = "🎰 No match — house wins"
            result = f"You lost **{bet:,} Pesos** 💸"

        em = nextcord.Embed(title=title, color=color)
        em.add_field(name="Reels", value=line, inline=False)
        em.add_field(name="Result", value=result, inline=False)
        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Slots(client))

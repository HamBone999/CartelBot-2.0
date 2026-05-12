import nextcord
from nextcord.ext import commands
import random

GID = [547181131766693900]


class Items(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.inv = self.client.db.inv

    @nextcord.slash_command(name="use", description="Use a consumable item from your inventory")
    async def use(self, interaction: nextcord.Interaction,
                  item: str = nextcord.SlashOption(description="Item to use",
                      choices={
                          "🧴 Bleach (-25 heat)": "bleach",
                          "🛢️ Burner Barrel (-15 heat)": "burner_barrel",
                          "🪪 Dirty Cop Badge (-50 heat)": "dirty_cop_badge",
                          "🛂 Fake Passport (reset heat to 0)": "fake_passport",
                          "📫 Mystery Package (random reward)": "mystery_package",
                          "🎒 Sus Backpack (50/50 risk)": "sus_backpack",
                          "🕯️ Narco Prayer Candle (+5 XP)": "narco_prayer_candle",
                          "💼 Blood Money Case (open for cash)": "blood_money_case",
                          "💵 Counterfeit Bills (try to spend)": "counterfeit_bills",
                      })):
        if not await self.inv.has_item(interaction.user, item):
            return await interaction.response.send_message(f"❌ You don't own a `{item}`.", ephemeral=True)

        em = nextcord.Embed(color=0x00ff88)

        if item == "bleach":
            await self.inv.consume(interaction.user, item, 1)
            reduced = await self.bank.reduce_heat(interaction.user, 25)
            em.title = "🧴 Evidence cleaned"
            em.description = f"You bleached the scene. Heat **-{reduced}**."

        elif item == "burner_barrel":
            await self.inv.consume(interaction.user, item, 1)
            reduced = await self.bank.reduce_heat(interaction.user, 15)
            em.title = "🛢️ Burned the evidence"
            em.description = f"Smoke goes up, evidence goes away. Heat **-{reduced}**."

        elif item == "dirty_cop_badge":
            await self.inv.consume(interaction.user, item, 1)
            reduced = await self.bank.reduce_heat(interaction.user, 50)
            em.title = "🪪 Bribe accepted"
            em.description = f"Officer Friendly looked the other way. Heat **-{reduced}**."

        elif item == "fake_passport":
            await self.inv.consume(interaction.user, item, 1)
            await self.bank.set_heat(interaction.user, 0)
            em.title = "🛂 New identity"
            em.color = 0xffd700
            em.description = "You crossed the border. Heat reset to **0**."

        elif item == "mystery_package":
            await self.inv.consume(interaction.user, item, 1)
            roll = random.random()
            if roll < 0.5:
                cash = random.randint(500, 5000)
                added, lost = await self.bank.add_to_wallet(interaction.user, cash)
                em.title = "📫 Mystery Package — CASH"
                em.description = f"Inside was **{added:,} Pesos**!"
                if lost > 0:
                    em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost")
            elif roll < 0.85:
                drop = random.choice(["meth", "coke_kit", "pseudo", "scale", "stash_box", "padlock"])
                qty = random.randint(1, 3)
                await self.inv.update_acc(interaction.user, qty, drop)
                em.title = "📫 Mystery Package — ITEMS"
                em.description = f"Inside: **{qty}x {drop.replace('_',' ').title()}**!"
            else:
                em.title = "📫 Mystery Package — EMPTY"
                em.color = 0xff0000
                em.description = "Just an empty box. You got scammed."

        elif item == "sus_backpack":
            await self.inv.consume(interaction.user, item, 1)
            if random.random() < 0.5:
                cash = random.randint(2000, 15000)
                added, lost = await self.bank.add_to_wallet(interaction.user, cash)
                em.title = "🎒 Sus Backpack — JACKPOT"
                em.description = f"It was someone's stash. **+{added:,} Pesos**"
                if lost > 0:
                    em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost")
            else:
                em.title = "💥 Sus Backpack — IT WAS A BOMB"
                em.color = 0xff0000
                users = await self.bank.get_acc(interaction.user)
                loss = min(users[1], random.randint(1000, 5000))
                await self.bank.update_acc(interaction.user, -loss)
                em.description = f"It exploded. You lost **{loss:,} Pesos** to the chaos."

        elif item == "narco_prayer_candle":
            await self.inv.consume(interaction.user, item, 1)
            await self.bank.award_xp(interaction.user, 5)
            em.title = "🕯️ Prayer answered"
            em.description = "The cartel saints smile. **+5 XP**"

        elif item == "blood_money_case":
            await self.inv.consume(interaction.user, item, 1)
            cash = random.randint(40_000, 100_000)
            added, lost = await self.bank.add_to_wallet(interaction.user, cash)
            em.title = "💼 Case opened"
            em.color = 0xffd700
            em.description = f"**+{added:,} Pesos**"
            if lost > 0:
                em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost — deposit first next time")

        elif item == "counterfeit_bills":
            await self.inv.consume(interaction.user, item, 1)
            if random.random() < 0.6:
                cash = random.randint(8_000, 16_000)
                added, lost = await self.bank.add_to_wallet(interaction.user, cash)
                em.title = "💵 Spent the fakes"
                em.description = f"Cashier didn't check. **+{added:,} Pesos**"
                if lost > 0:
                    em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} lost")
            else:
                em.title = "💵 Cashier caught it"
                em.color = 0xff0000
                await self.bank.update_acc(interaction.user, 20, mode="heat")
                em.description = "Cashier flagged the bills. **+20 heat**."

        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Items(client))

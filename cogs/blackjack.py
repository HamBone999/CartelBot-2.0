import nextcord
from nextcord.ext import commands
import random
from modules.bank_funcs import RANK_NAMES

GID = [547181131766693900]

RED_SUITS = {"♥", "♦"}


def render_card(card: str, hidden: bool = False):
    """Return a 5-line list representing one card in ASCII art."""
    if hidden:
        return [
            "┌─────┐",
            "│░░░░░│",
            "│░ ? ░│",
            "│░░░░░│",
            "└─────┘",
        ]
    rank = card[:-1]
    suit = card[-1]
    # pad to 2 chars for alignment (10 is 2-char, others are 1-char)
    if rank == "10":
        top = f"│{rank}   │"
        bot = f"│   {rank}│"
    else:
        top = f"│{rank}    │"
        bot = f"│    {rank}│"
    return [
        "┌─────┐",
        top,
        f"│  {suit}  │",
        bot,
        "└─────┘",
    ]


def render_hand(hand, hide_index=None):
    """Render a list of cards side by side as one multi-line block."""
    cards = []
    for i, card in enumerate(hand):
        cards.append(render_card(card, hidden=(i == hide_index)))
    rows = []
    for line_idx in range(5):
        rows.append(" ".join(c[line_idx] for c in cards))
    return "\n".join(rows)


class BlackjackGame:
    def __init__(self, cog, interaction: nextcord.Interaction, bet: int):
        self.cog = cog
        self.interaction = interaction
        self.bet = bet
        self.player_hand = []
        self.dealer_hand = []
        self.doubled = False

    def calculate(self, hand):
        value, aces = 0, 0
        for card in hand:
            rank = card[:-1]
            if rank in ['J', 'Q', 'K']:
                value += 10
            elif rank == 'A':
                aces += 1
                value += 11
            else:
                value += int(rank)
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value

    async def start(self):
        await self.cog.bank.open_acc(self.interaction.user)
        users = await self.cog.bank.get_acc(self.interaction.user)
        if users[1] < self.bet:
            return await self.interaction.response.send_message("❌ You don't have enough Pesos!", ephemeral=True)
        await self.cog.bank.update_acc(self.interaction.user, -self.bet)

        self.player_hand = [self.cog.draw_card() for _ in range(2)]
        self.dealer_hand = [self.cog.draw_card() for _ in range(2)]

        # natural blackjack check
        if self.calculate(self.player_hand) == 21:
            await self.interaction.response.send_message(embed=self._build_embed(reveal=True))
            return await self._natural_blackjack()

        view = BlackjackView(self)
        await self.interaction.response.send_message(embed=self._build_embed(reveal=False), view=view)

    def _build_embed(self, reveal: bool, status: str = "Your move"):
        player_val = self.calculate(self.player_hand)
        em = nextcord.Embed(
            title=f"🃏 Cartel Blackjack — {status}",
            color=0x1abc9c
        )
        em.add_field(
            name=f"🎩 Dealer — {self.calculate(self.dealer_hand) if reveal else '?'}",
            value=f"```{render_hand(self.dealer_hand, hide_index=None if reveal else 1)}```",
            inline=False,
        )
        em.add_field(
            name=f"🧍 You — {player_val}",
            value=f"```{render_hand(self.player_hand)}```",
            inline=False,
        )
        em.add_field(name="💰 Bet", value=f"**{self.bet:,} Pesos**", inline=True)
        if self.doubled:
            em.add_field(name="⚡", value="Doubled down", inline=True)
        em.set_footer(text=f"{self.interaction.user.name} • Win pays 1:1 • Natural Blackjack pays 3:2")
        return em

    async def _natural_blackjack(self):
        # 3:2 payout
        payout = int(self.bet * 2.5)
        added, lost = await self.cog.bank.add_to_wallet(self.interaction.user, payout)
        await self.cog.bank.award_xp(self.interaction.user, 15)
        em = nextcord.Embed(title="🎰 NATURAL BLACKJACK!", color=0xffd700)
        em.add_field(name="🃏 Your hand", value=f"```{render_hand(self.player_hand)}```", inline=False)
        em.add_field(name="🎩 Dealer", value=f"```{render_hand(self.dealer_hand)}```", inline=False)
        em.add_field(name="💰 Payout (3:2)", value=f"**+{added:,} Pesos**", inline=True)
        em.add_field(name="🎓 XP", value="**+15**", inline=True)
        if lost > 0:
            em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost", inline=False)
        await self.interaction.followup.send(embed=em)

    async def hit(self, interaction):
        self.player_hand.append(self.cog.draw_card())
        if self.calculate(self.player_hand) > 21:
            return await self.bust(interaction)
        await interaction.response.edit_message(embed=self._build_embed(reveal=False, status="Hit"))

    async def stand(self, interaction):
        await self.dealer_turn(interaction)

    async def double_down(self, interaction):
        await self.cog.bank.open_acc(self.interaction.user)
        users = await self.cog.bank.get_acc(self.interaction.user)
        if users[1] < self.bet:
            return await interaction.response.send_message("❌ Not enough cash to double!", ephemeral=True)
        await self.cog.bank.update_acc(self.interaction.user, -self.bet)
        self.bet *= 2
        self.doubled = True
        self.player_hand.append(self.cog.draw_card())
        if self.calculate(self.player_hand) > 21:
            return await self.bust(interaction)
        await self.dealer_turn(interaction)

    async def dealer_turn(self, interaction):
        while self.calculate(self.dealer_hand) < 17:
            self.dealer_hand.append(self.cog.draw_card())
        player_val = self.calculate(self.player_hand)
        dealer_val = self.calculate(self.dealer_hand)
        if dealer_val > 21 or player_val > dealer_val:
            await self.win(interaction)
        elif player_val == dealer_val:
            await self.push(interaction)
        else:
            await self.lose(interaction)

    async def bust(self, interaction):
        em = nextcord.Embed(title="💥 BUST!", color=0xff0000)
        em.add_field(name=f"🧍 You — {self.calculate(self.player_hand)}", value=f"```{render_hand(self.player_hand)}```", inline=False)
        em.add_field(name="💸 Lost", value=f"**{self.bet:,} Pesos**", inline=False)
        em.set_footer(text="Try again with /blackjack")
        await interaction.response.edit_message(embed=em, view=None)

    async def win(self, interaction):
        payout = self.bet * 2
        added, lost = await self.cog.bank.add_to_wallet(self.interaction.user, payout)
        await self.cog.bank.award_xp(self.interaction.user, 10)
        em = nextcord.Embed(title="🎉 YOU WIN!", color=0x2ecc71)
        em.add_field(name=f"🎩 Dealer — {self.calculate(self.dealer_hand)}", value=f"```{render_hand(self.dealer_hand)}```", inline=False)
        em.add_field(name=f"🧍 You — {self.calculate(self.player_hand)}", value=f"```{render_hand(self.player_hand)}```", inline=False)
        em.add_field(name="💰 Payout", value=f"**+{added:,} Pesos**", inline=True)
        em.add_field(name="🎓 XP", value="**+10**", inline=True)
        if lost > 0:
            em.add_field(name="⚠️ Wallet capped", value=f"{lost:,} Pesos lost", inline=False)
        await interaction.response.edit_message(embed=em, view=None)

    async def push(self, interaction):
        await self.cog.bank.update_acc(self.interaction.user, self.bet)
        em = nextcord.Embed(title="🤝 PUSH", color=0xf1c40f)
        em.add_field(name=f"🎩 Dealer — {self.calculate(self.dealer_hand)}", value=f"```{render_hand(self.dealer_hand)}```", inline=False)
        em.add_field(name=f"🧍 You — {self.calculate(self.player_hand)}", value=f"```{render_hand(self.player_hand)}```", inline=False)
        em.add_field(name="💵 Bet returned", value=f"**{self.bet:,} Pesos**", inline=False)
        await interaction.response.edit_message(embed=em, view=None)

    async def lose(self, interaction):
        em = nextcord.Embed(title="😔 DEALER WINS", color=0xe74c3c)
        em.add_field(name=f"🎩 Dealer — {self.calculate(self.dealer_hand)}", value=f"```{render_hand(self.dealer_hand)}```", inline=False)
        em.add_field(name=f"🧍 You — {self.calculate(self.player_hand)}", value=f"```{render_hand(self.player_hand)}```", inline=False)
        em.add_field(name="💸 Lost", value=f"**{self.bet:,} Pesos**", inline=False)
        await interaction.response.edit_message(embed=em, view=None)


class BlackjackView(nextcord.ui.View):
    def __init__(self, game: BlackjackGame):
        super().__init__(timeout=120)
        self.game = game

    @nextcord.ui.button(label="Hit", style=nextcord.ButtonStyle.primary, emoji="🃏")
    async def hit(self, button, interaction):
        if interaction.user.id != self.game.interaction.user.id:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)
        await self.game.hit(interaction)

    @nextcord.ui.button(label="Stand", style=nextcord.ButtonStyle.secondary, emoji="✋")
    async def stand(self, button, interaction):
        if interaction.user.id != self.game.interaction.user.id:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)
        await self.game.stand(interaction)

    @nextcord.ui.button(label="Double Down", style=nextcord.ButtonStyle.danger, emoji="⚡")
    async def double(self, button, interaction):
        if interaction.user.id != self.game.interaction.user.id:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)
        if len(self.game.player_hand) > 2:
            return await interaction.response.send_message("You can only double on your first move.", ephemeral=True)
        await self.game.double_down(interaction)


class Blackjack(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank
        self.cards = [
            f"{r}{s}"
            for s in ["♠", "♥", "♦", "♣"]
            for r in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        ]

    def draw_card(self):
        return random.choice(self.cards)

    @nextcord.slash_command(name="blackjack", description="Play Cartel Blackjack (min bet 500 Pesos)")
    async def cartelblackjack(self, interaction: nextcord.Interaction,
                               bet: int = nextcord.SlashOption(description="Amount to bet", min_value=500)):
        game = BlackjackGame(self, interaction, bet)
        await game.start()


def setup(client):
    client.add_cog(Blackjack(client))

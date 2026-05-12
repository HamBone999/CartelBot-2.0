import nextcord
from nextcord.ext import commands
from base import EconomyBot


class Admin(commands.Cog):
    def __init__(self, client: EconomyBot):
        self.client = client
        self.bank = self.client.db.bank

    async def _owner_check(self, interaction: nextcord.Interaction) -> bool:
        if not await self.client.is_owner(interaction.user):
            await interaction.response.send_message("You cannot use this command", ephemeral=True)
            return False
        return True

    @nextcord.slash_command(name="addmoney", description="[Owner] Add money to a member's account")
    async def add_money(self, interaction: nextcord.Interaction,
                        member: nextcord.Member = nextcord.SlashOption(description="Target member"),
                        amount: int = nextcord.SlashOption(description="Amount to add", min_value=1, max_value=100000),
                        mode: str = nextcord.SlashOption(description="Wallet or bank", choices={"Wallet": "wallet", "Bank": "bank"}, required=False, default="wallet")):
        if not await self._owner_check(interaction):
            return
        if member.bot:
            return await interaction.response.send_message("You can't add money to a bot", ephemeral=True)
        await self.bank.open_acc(member)
        await self.bank.update_acc(member, +amount, mode)
        await interaction.response.send_message(f"Added **{amount:,}** to {member.mention}'s {mode}")

    @nextcord.slash_command(name="removemoney", description="[Owner] Remove money from a member's account")
    async def remove_money(self, interaction: nextcord.Interaction,
                           member: nextcord.Member = nextcord.SlashOption(description="Target member"),
                           amount: int = nextcord.SlashOption(description="Amount to remove", min_value=1),
                           mode: str = nextcord.SlashOption(description="Wallet or bank", choices={"Wallet": "wallet", "Bank": "bank"}, required=False, default="wallet")):
        if not await self._owner_check(interaction):
            return
        if member.bot:
            return await interaction.response.send_message("You can't remove money from a bot", ephemeral=True)
        await self.bank.open_acc(member)
        users = await self.bank.get_acc(member)
        current = users[2 if mode == "bank" else 1]
        if current < amount:
            return await interaction.response.send_message(f"You can only remove **{current:,}** from {member.mention}'s {mode}", ephemeral=True)
        await self.bank.update_acc(member, -amount, mode)
        await interaction.response.send_message(f"Removed **{amount:,}** from {member.mention}'s {mode}")

    @nextcord.slash_command(name="resetuser", description="[Owner] Reset a member's account to zero")
    async def reset_user(self, interaction: nextcord.Interaction,
                         member: nextcord.Member = nextcord.SlashOption(description="Member to reset")):
        if not await self._owner_check(interaction):
            return
        if member.bot:
            return await interaction.response.send_message("Bots don't have an account", ephemeral=True)
        users = await self.bank.get_acc(member)
        if users is None:
            await self.bank.open_acc(member)
        else:
            await self.bank.reset_acc(member)
        await interaction.response.send_message(f"{member.mention}'s account has been reset")


def setup(client):
    client.add_cog(Admin(client))

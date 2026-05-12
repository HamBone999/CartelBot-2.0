import nextcord
from nextcord.ext import commands


class Crew(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.bank = self.client.db.bank

    @nextcord.slash_command(name="createcrew", description="Create a new crew (costs 50,000 Pesos)")
    async def createcrew(self, interaction: nextcord.Interaction,
                         name: str = nextcord.SlashOption(description="Crew name (3–20 characters)", min_length=3, max_length=20)):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[1] < 50000:
            return await interaction.response.send_message("❌ You need **50,000 Pesos** to create a crew!", ephemeral=True)
        if users[6] is not None:
            return await interaction.response.send_message("❌ You are already in a crew! Use `/leavecrew` first.", ephemeral=True)
        await self.bank.update_acc(interaction.user, -50000)
        await self.bank.update_acc(interaction.user, name, mode="crew")
        await interaction.response.send_message(f"🏴‍☠️ **{name}** crew has been created!\nYou are now the leader.")

    @nextcord.slash_command(name="joincrew", description="Join an existing crew")
    async def joincrew(self, interaction: nextcord.Interaction,
                       name: str = nextcord.SlashOption(description="Name of the crew to join")):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[6] is not None:
            return await interaction.response.send_message("❌ You are already in a crew! Use `/leavecrew` first.", ephemeral=True)
        if not await self.bank.crew_exists(name):
            return await interaction.response.send_message(f"❌ No crew named **{name}** exists. Someone must create it first with `/createcrew`.", ephemeral=True)
        await self.bank.update_acc(interaction.user, name, mode="crew")
        await interaction.response.send_message(f"✅ You joined the **{name}** crew!")

    @nextcord.slash_command(name="leavecrew", description="Leave your current crew")
    async def leavecrew(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        if users[6] is None:
            return await interaction.response.send_message("❌ You are not in any crew.", ephemeral=True)
        await self.bank.update_acc(interaction.user, None, mode="crew")
        await interaction.response.send_message("✅ You have left your crew.")

    @nextcord.slash_command(name="crew", description="Show your current crew info")
    async def crew(self, interaction: nextcord.Interaction):
        await self.bank.open_acc(interaction.user)
        users = await self.bank.get_acc(interaction.user)
        crew_name = users[6]
        if crew_name is None:
            return await interaction.response.send_message("You are not in any crew.\nUse `/createcrew` or `/joincrew`")
        em = nextcord.Embed(title=f"🏴‍☠️ {crew_name} Crew", color=0xff8800)
        em.add_field(name="Leader", value=interaction.user.name, inline=True)
        em.add_field(name="Members", value="1 (You)", inline=True)
        await interaction.response.send_message(embed=em)


def setup(client):
    client.add_cog(Crew(client))

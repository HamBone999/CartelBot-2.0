import nextcord
from nextcord.ext import commands
import traceback
from base import Auth


class Events(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: nextcord.Interaction, error):
        if isinstance(error, nextcord.errors.ApplicationInvokeError):
            error = error.original
        # Always log to console so you can see what broke
        cmd_name = interaction.application_command.qualified_name if interaction.application_command else "?"
        print(f"\n❌ [ERROR] /{cmd_name} by {interaction.user} ({interaction.user.id}):")
        traceback.print_exception(type(error), error, error.__traceback__)
        # Try to inform the user
        try:
            await interaction.response.send_message(f"⚠️ Something went wrong: `{error}`", ephemeral=True)
        except nextcord.InteractionResponded:
            try:
                await interaction.followup.send(f"⚠️ Something went wrong: `{error}`", ephemeral=True)
            except Exception:
                pass
        except Exception:
            pass


def setup(client):
    client.add_cog(Events(client))

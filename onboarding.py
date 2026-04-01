import discord
from discord.ext import commands



class RoleSelectionView(discord.ui.View):
    
    
    
    def __init__(self, role_options: list[discord.Role], member: discord.Member):
        
        super().__init__(timeout=None) # Keeps the view active until the bot restarts
        self.selected_roles = []
        self.role_options = role_options
        self.member = member
        self.choose_roles.options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in role_options]

    # 1. The Dropdown (Select Menu)
    @discord.ui.select(
        placeholder="Choose regional channels",
        min_values=2,
        max_values=2,
    )
    async def choose_roles(self, interaction: discord.Interaction, select: discord.ui.Select):
        # This method can be used to trigger the dropdown if needed
        self.selected_roles = select.values
        await interaction.response.defer()
        

    # 2. The Confirm Button
    @discord.ui.button(label="Confirm Choices", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_roles:
            await interaction.response.send_message("Please pick your roles first!", ephemeral=True)
            return

        roles_to_add = [role for role in self.role_options if str(role.id) in self.selected_roles]
        role_names = [role.name for role in roles_to_add]
        # Apply the roles
        await self.member.add_roles(*roles_to_add)
     

        # 3. Final Step: "Remove" the dialog by editing the message to have NO View
        # This prevents them from clicking it again.
        await interaction.response.edit_message(
            content=f"✅ **Success!** I've added the following roles to your account: **{', '.join(role_names)}**.\nEnjoy!",
            view=None
        )







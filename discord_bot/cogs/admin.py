from typing import Dict, Optional

import discord as discord
from discord.ext import commands
import jsonpickle
import os

from discord_bot.bot import config
from discord_bot.subscription import Subscription, SubscriptionData


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.react_list = ["0⃣", "1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟", "#⃣", "*⃣"]
        self.categories = sorted(list(set(x for monitor in self.bot.monitors for x in monitor.product_categories)),
                                 key=lambda x: x.name)
        self.category_reacts = {self.react_list[i]: category for i, category in enumerate(self.categories)}
        self.subscription_message: Optional[discord.Message] = None
        self.subscriptions: Dict[discord.Member.id, Subscription]  # = {}
        self.save_dir = config["save_path"]
        self.save_file_name = "subscription_data.json"

        self.load_user_data()

    def serialize_user_data(self):
        return jsonpickle.encode(self.subscriptions)  # todo: save json to file

    def save_user_data(self):
        json = self.serialize_user_data()
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        with open(self.save_dir + "/" + self.save_file_name, "w+") as fp:
            fp.writelines(json)

    def load_user_data(self):
        data_path = self.save_dir + "/" + self.save_file_name
        if os.path.exists(data_path):
            with open(data_path) as fp:
                json = fp.read()
            self.subscriptions = jsonpickle.decode(json)
        else:
            self.subscriptions = {}

    @commands.command(name="subchannel", help="sets channel where users can subscribe to product notifications")
    @commands.has_any_role(config["admin_role"], config["mod_role"])
    async def set_subscription_channel(self, ctx):
        await ctx.message.delete()
        reacts_message = "\n".join(
            emoji + " " + category.name
            for emoji, category in self.category_reacts.items()
        )

        self.subscription_message = await ctx.channel.send(reacts_message)
        for react in self.category_reacts.keys():
            await self.subscription_message.add_reaction(react)

    @commands.command(name="sublist", help="displays a user's subscriptions")
    async def list_subscriptions(self, ctx):
        sub_emoji = "✅"
        nosub_emoji = "🟥"
        sender_id = str(ctx.message.author.id)
        embed = discord.Embed(title=f"{ctx.message.author} -- Active Subscriptions")
        for category in self.categories:
            category_name = category.name
            if sender_id in self.subscriptions and category_name in self.subscriptions[sender_id].products:
                embed.add_field(name=category_name, value=sub_emoji)
            else:
                embed.add_field(name=category_name, value=nosub_emoji)

        await ctx.channel.send(embed=embed)

    def add_sub(self, user_id: str, category_name: str, max_price: float = None):
        if category_name in [x.name for x in self.categories]:
            user_subscription = self.subscriptions.get(user_id)
            if user_subscription is None:
                self.subscriptions[user_id] = Subscription(products={
                    category_name: SubscriptionData(max_price=max_price)
                })
            else:
                user_subscription.products[category_name] = SubscriptionData(max_price=max_price)
            self.save_user_data()

    def remove_sub(self, user_id: str, category_name: str):
        del self.subscriptions[user_id].products[category_name]
        self.save_user_data()

    def clear_subs(self, user_id: str):
        """
        A function to clear all of a user's subscriptions
        """
        del self.subscriptions[user_id]

    @commands.command(name="addsub", help="subscribes a user to a product category")
    async def add_sub_command(self, ctx, arg):
        self.add_sub(str(ctx.message.author.id), arg, max_price=None)

    @commands.command(name="rmsub", help="unsubscribes a user from a product category")
    async def remove_sub_command(self, ctx, arg):
        self.remove_sub(str(ctx.message.author.id), arg)

    @commands.command(name="clearsubs", help="clears all of a user's subscriptions")
    async def clear_subs_command(self, ctx):
        self.clear_subs(str(ctx.message.author.id))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id == self.subscription_message.id and self.subscription_message.author.id != payload.user_id:
            product_category = self.category_reacts[payload.emoji.name]
            self.add_sub(str(payload.user_id), product_category.name, max_price=None)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        product_category = self.category_reacts[payload.emoji.name]
        self.remove_sub(str(payload.user_id), product_category.name)


def setup(bot):
    bot.add_cog(Admin(bot))

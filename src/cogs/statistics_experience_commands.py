import asyncio
import time

import discord
from discord.ext import commands, menus

from utils import checks, models
from utils.cog_class import Cog
from utils.ctx_class import MyContext
from utils.models import Player, get_player, get_from_db


class TopScoresSource(menus.ListPageSource):
    def __init__(self, ctx: MyContext, data, title):
        super().__init__(data, per_page=6)
        self.ctx = ctx
        self.title = title

    async def format_page(self, menu, entries):
        _ = await self.ctx.get_translate_function()
        e = discord.Embed()
        e.title = self.title
        offset = menu.current_page * self.per_page

        for i, item in enumerate(entries, start=offset):
            item:Player
            e.add_field(name=f"**{i + 1}** - {item.member.user.name}#{item.member.user.discriminator}", value=_("{exp} experience", exp=item.experience), inline=False)
        return e


async def show_topscores_pages(ctx, title: str):
    pages = menus.MenuPages(
        source=
        TopScoresSource(
            ctx,
            await Player
                .all()
                .filter(channel__discord_id=ctx.channel.id)
                .order_by('-experience')
                .prefetch_related("member__user"),
            title
        ),
        clear_reactions_after=True
    )
    await pages.start(ctx)

class StatisticsCommands(Cog):
    @commands.command(aliases=["quick_stats", "quickstats"])
    @checks.channel_enabled()
    async def me(self, ctx: MyContext, target: discord.Member = None):
        """
        Get some quickstats about yourself (or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} statistics.", target=target))

        level_info = db_hunter.level_info()

        embed.add_field(name=_("Bullets"), value=f"{db_hunter.bullets}/{level_info['bullets']}", inline=True)
        embed.add_field(name=_("Magazines"), value=f"{db_hunter.magazines}/{level_info['magazines']}", inline=True)
        embed.add_field(name=_("Experience"), value=db_hunter.experience, inline=True)
        embed.add_field(name=_("Level"), value=str(level_info['level']) + " - " + _(level_info['name']).title(), inline=True)
        embed.add_field(name=_("Accuracy"),
                        value=_("{level_reliability} % (Real: {real_reliability} %)", level_reliability=level_info['accuracy'], real_reliability=db_hunter.real_accuracy),
                        inline=True)
        embed.add_field(name=_("Reliability"),
                        value=_("{level_reliability} % (Real: {real_reliability} %)", level_reliability=level_info['reliability'], real_reliability=db_hunter.real_reliability),
                        inline=True)

        await ctx.send(embed=embed)

    @commands.command(aliases=["shoots", "shooting"])
    @checks.channel_enabled()
    async def shooting_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get shooting stats (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} shooting stats.", target=target))

        shooting_stats = db_hunter.shooting_stats

        shots_when_dead = shooting_stats.get('shots_when_dead', None)
        revives = shooting_stats.get('revives', 0)
        brains_eaten = shooting_stats.get('brains_eaten', 0)
        if shots_when_dead:
            embed.add_field(name=_("🧠"), value=_("{shots_when_dead} shots attempted when DEAD. "
                                                  "{target.mention} went back to life {revives} times eating a total of {brains_eaten} brains",
                                                  target=target,
                                                  shots_when_dead=shots_when_dead,
                                                  revives=revives,
                                                  brains_eaten=brains_eaten))

        shots_when_wet = shooting_stats.get('shots_when_wet', None)
        if shots_when_wet:
            embed.add_field(name=_("🚰"), value=_("{shots} shots attempted when wet.", shots=shots_when_wet))

        shots_when_confiscated = shooting_stats.get('shots_when_confiscated', None)
        if shots_when_confiscated:
            embed.add_field(name=_("⛔️"), value=_("{shots} shots attempted when {target.mention} gun was confiscated.", shots=shots_when_confiscated, target=target))

        shots_when_sabotaged = shooting_stats.get('shots_when_sabotaged', None)
        if shots_when_sabotaged:
            embed.add_field(name=_("💥"), value=_("{shots} shots attempted with a sabotaged gun.", shots=shots_when_sabotaged, target=target))

        shots_when_jammed = shooting_stats.get('shots_when_jammed', None)
        if shots_when_jammed:
            embed.add_field(name=_("☁"), value=_("{shots} shots attempted with a jammed weapon.", shots=shots_when_jammed, target=target))

        shots_with_empty_magazine = shooting_stats.get('shots_with_empty_magazine', None)
        if shots_with_empty_magazine:
            embed.add_field(name=_("🦉"), value=_("{shots} shots attempted without bullets.", shots=shots_with_empty_magazine, target=target))

        shots_jamming_weapon = shooting_stats.get('shots_jamming_weapon', None)
        if shots_jamming_weapon:
            embed.add_field(name=_("💥"), value=_("{shots} shots jamming {target.mention} weapon.", shots=shots_jamming_weapon, target=target))

        bullets_used = shooting_stats.get('bullets_used', None)
        if bullets_used:
            embed.add_field(name=_("🔫"), value=_("{bullets} bullets used in a duck killing madness.", bullets=bullets_used, target=target))

        missed = shooting_stats.get('missed', None)
        if missed:
            embed.add_field(name=_("🎯"), value=_("{shots} shots missing a target.", shots=missed, target=target))

        killed = shooting_stats.get('killed', None)
        murders = shooting_stats.get('murders', 0)
        if killed:
            embed.add_field(name=_("☠️"), value=_("{shots} shots killing someone ({murders} were murders).", shots=killed, murders=murders, target=target))

        got_killed = shooting_stats.get('got_killed', None)
        if got_killed:
            embed.add_field(name=_("🧟"), value=_("{target.mention} was killed {times} times.", times=got_killed, target=target))

        homing_kills = shooting_stats.get('homing_kills', None)
        if homing_kills:
            embed.add_field(name=_("🏆️"), value=_("{shots} shots using homing bullets.", shots=homing_kills, target=target))

        shots_with_duck = shooting_stats.get('shots_with_duck', None)
        if shots_with_duck:
            embed.add_field(name=_("🦆"), value=_("{shots} shots going towards ducks.", shots=shots_with_duck, target=target))

        shots_stopped_by_detector = shooting_stats.get('shots_stopped_by_detector', None)
        if shots_stopped_by_detector:
            embed.add_field(name=_("🕵"), value=_("{shots} shots stopped by the infrared detector.", shots=shots_stopped_by_detector, target=target))

        shots_without_ducks = shooting_stats.get('shots_without_ducks', None)
        if shots_without_ducks:
            embed.add_field(name=_("❓"), value=_("{shots} shots without any duck in sight.", shots=shots_without_ducks, target=target))

        await ctx.send(embed=embed)

    def add_fields_for_every_duck(self, _, embed, from_dict, not_found_message):
        fields = [
            (_("Normal ducks"), 'normal'),
            (_("Ghost ducks"), 'ghost'),
            (_("Professor ducks"), 'prof'),

            (_("Baby ducks"), 'baby'),
            (_("Golden ducks"), 'golden'),
            (_("Plastic ducks"), 'plastic'),

            (_("Kamikaze ducks"), 'kamikaze'),
            (_("Mechanical ducks"), 'mechanical'),
            (_("Super ducks"), 'super'),

            (_("Mother of all ducks"), 'moad'),
            (_("Armored ducks"), 'armored'),
        ]

        for field_name, field_key in fields:

            value = from_dict.get(field_key, None)
            if value:
                embed.add_field(name=field_name, value=str(value), inline=True)
            elif not_found_message:
                embed.add_field(name=field_name, value=str(not_found_message), inline=True)

    @commands.command(aliases=["times", "besttimes"])
    @checks.channel_enabled()
    async def best_times(self, ctx: MyContext, target: discord.Member = None):
        """
        Get best times to kill of ducks (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} best times.", target=target))

        bt = db_hunter.best_times

        bt = {k: str(round(v, 2)) + " s" for k, v in bt.items()}

        no_kill_message = _("Never killed any")

        self.add_fields_for_every_duck(_, embed, bt, no_kill_message)

        await ctx.send(embed=embed)

    @commands.command(aliases=["kills", "killsstats", "killcounts", "kills_count", "kill_count", "killed"])
    @checks.channel_enabled()
    async def kills_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get number of each type of duck killed (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} kill counts.", target=target))

        killed = db_hunter.killed

        no_kill_message = 0

        self.add_fields_for_every_duck(_, embed, killed, no_kill_message)

        await ctx.send(embed=embed)

    @commands.command(aliases=["hugs", "hugsstats", "hugged"])
    @checks.channel_enabled()
    async def hugs_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get number of each type of duck hugged (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} hugs counts.", target=target))

        self.add_fields_for_every_duck(_, embed, db_hunter.hugged, None)

        players = db_hunter.hugged.get('players', None)
        if players:
            embed.add_field(name=_("Players"), value=str(players), inline=True)

        hugged_dead = db_hunter.hugged.get('when_dead', None)
        if hugged_dead:
            embed.add_field(name=_("Hugs when dead"), value=str(hugged_dead), inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["hurted", "hurtstats"])
    @checks.channel_enabled()
    async def hurt_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get number of each type of duck hurted (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} hurt counts.", target=target))

        self.add_fields_for_every_duck(_, embed, db_hunter.hurted, None)

        await ctx.send(embed=embed)

    @commands.command(aliases=["resisted", "resiststats"])
    @checks.channel_enabled()
    async def resist_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get number of each type of duck that resisted a shot (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} resisted counts.", target=target))

        self.add_fields_for_every_duck(_, embed, db_hunter.resisted, None)

        await ctx.send(embed=embed)

    @commands.command(aliases=["fightened", "fightenstats", "fightened_stats", "fightenedstats", "frighten"])
    @checks.channel_enabled()
    async def frighten_stats(self, ctx: MyContext, target: discord.Member = None):
        """
        Get number of each type of duck that fled following a shot (for you or someone else).
        """
        if not target:
            target = ctx.author

        _ = await ctx.get_translate_function()
        db_hunter: Player = await get_player(target, ctx.channel)

        embed = discord.Embed(colour=discord.Color.blurple(),
                              title=_("{target.name} scared ducks.", target=target))

        self.add_fields_for_every_duck(_, embed, db_hunter.frightened, None)

        await ctx.send(embed=embed)

    @commands.command(aliases=["sendexp", "sendxp", "send_xp"])
    @checks.channel_enabled()
    async def send_exp(self, ctx: MyContext, target: discord.Member, amount: int):
        """
        Send some of your experience to another player.
        """
        _, db_channel, db_sender, db_reciver = await asyncio.gather(ctx.get_translate_function(), get_from_db(ctx.channel), get_player(ctx.author, ctx.channel),
                                                                    get_player(target, ctx.channel))

        if target.id == ctx.author.id:
            await ctx.reply(_("❌ You cant send experience to yourself."))
            return False

        elif target.bot:
            await ctx.reply(_("❌ I'm not sure that {target.mention} can play DuckHunt.", target=target))
            return False

        elif amount < 10:
            await ctx.reply(_("❌ You need to send more experience than this."))
            return False

        elif db_sender.experience < amount:
            await ctx.reply(_("❌ You don't have enough experience 🤣."))
            return False

        if amount >= 30 and db_reciver.is_powerup_active('confiscated'):
            db_sender.stored_achievements['gun_insurer'] = True

        tax = int(amount * (db_channel.tax_on_user_send / 100) + 0.5)

        await db_sender.edit_experience_with_levelups(ctx, -amount)
        await db_reciver.edit_experience_with_levelups(ctx, amount-tax)

        await asyncio.gather(db_sender.save(), db_reciver.save())

        await ctx.reply(_("🏦 You sent {recived} experience to {reciver.mention}. "
                          "A tax of {db_channel.tax_on_user_send}% was applied to this transaction (taking {tax} exp out of the total sent).",

                          amount=amount,
                          recived=amount - tax,
                          tax=tax,
                          reciver=target,
                          db_channel=db_channel))

    @commands.command(aliases=["giveexp", "givexp", "give_xp"])
    @checks.channel_enabled()
    @checks.needs_access_level(models.AccessLevel.ADMIN)
    async def give_exp(self, ctx: MyContext, target: discord.Member, amount: int):
        """
        Give some experience to another player. This is a cheat.
        """
        _, db_receiver = await asyncio.gather(ctx.get_translate_function(), get_player(target, ctx.channel))

        if target.bot:
            await ctx.reply(_("❌ I'm not sure that {target.mention} can play DuckHunt.", target=target))
            return False

        await db_receiver.edit_experience_with_levelups(ctx, amount)

        await db_receiver.save()

        await ctx.reply(_("💰️ You gave {amount} experience to {reciver.mention}. ",
                          amount=amount,
                          reciver=target, ))

    @commands.command(aliases=["best", "scores"])
    @checks.channel_enabled()
    async def top(self, ctx: MyContext):
        """
        Who's the best ?
        """
        _ = await ctx.get_translate_function()

        await show_topscores_pages(ctx, _("Top Scores on #{channel}", channel=ctx.channel.name))


setup = StatisticsCommands.setup
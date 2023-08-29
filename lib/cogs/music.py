import wavelink, re, asyncio, discord
from discord.ext import commands
from lib.btns.paging import Page

class Music(commands.Cog):

    def __init__(self, bot : commands.Bot):
        self.bot = bot
    

    @commands.command(name="play", aliases=['p', 's'])
    async def play(self, ctx: commands.Context, *, search: str) -> None:
        '''
        노래 재생 및 재생 목록에 노래 추가
        '''
        if not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        tracks = await wavelink.YouTubeTrack.search(search)
        if not tracks:
            return await ctx.send(f'다음 검색어로 결과를 찾지 못했습니다 : ``{search}``')


        result = await ctx.send(embed=discord.Embed(color=57855, title=f"``{search}`` 를(을) 검색한 결과입니다.",\
        description='\n'.join([f"{i+1}. {track.title}" for i, track in enumerate(tracks[:5])]))\
        .set_footer(text="※ 원하는 노래의 번호를 선택해주세요. (0 입력 시 취소)")
        .set_thumbnail(url='https://i.imgur.com/j6bC47r.png'))


        def check(m):
            if re.compile('[0-5]').match(m.content) != None and (m.author.bot or (m.channel == ctx.channel and m.author == ctx.author)):
                # 0~5 의 값이 입력되고 입력한 사람이 본인이거나 봇일 경우
                return True
    
        try:
            select : discord.Message = await self.bot.wait_for('message', timeout=15, check=check)
            if '0' in select.content:
                raise asyncio.TimeoutError
            
        except asyncio.TimeoutError:
            return await ctx.send(f"{ctx.author.mention} 노래 선택이 취소되었습니다.")
        
        finally:
            await result.delete()
            await ctx.message.delete()


        track = tracks[int(select.content)-1]

        if vc.current:
            vc.queue.put(track)
            await ctx.send(embed=discord.Embed(description=track.title, color=65280)\
                           .set_author(name="다음 곡이 재생 목록에 추가되었습니다.", icon_url='https://i.imgur.com/2JAfVhf.png'))
        else:
            vc.autoplay = True
            await vc.play(track, populate=True)


    @commands.command(name="skip", aliases=['ss'])
    async def skip(self, ctx : commands.Context) -> None:
        '''
        현재 곡 스킵
        '''
        vc: wavelink.Player = ctx.voice_client
        await ctx.send(embed=discord.Embed(description=f"{vc.current.title}", color=16759040).set_author(name="SKIP", icon_url='https://i.imgur.com/82VL1OJ.png'))
        await vc.seek(vc.current.duration)
    

    @commands.command(name="np")
    async def now_playing(self, ctx : commands.Context) -> None:
        '''
        현재 재생 중인 곡 확인
        '''
        vc: wavelink.Player = ctx.voice_client

        embed = self.create_np_embed(vc.current.title, self.format_milliseconds(vc.position), vc.current.uri)
        await ctx.send(embed=embed)



    @commands.command(name="aq")
    async def auto_queue(self, ctx : commands.Context) -> None:
        '''
        추천 곡 재생목록 확인
        '''
        vc: wavelink.Player = ctx.voice_client

        contents = self.queue_to_contents(vc.auto_queue)
        
        embed = discord.Embed(title="[추천곡 재생 목록]", color=16777215)

        message = await ctx.send(embed=embed)
        page = Page(message, embed, contents)
        await message.edit(view=page)
        await page.set_page()



    @commands.command(name="queue", aliases=['q'])
    async def queue(self, ctx : commands.Context) -> None:
        '''
        재생 목록 확인
        '''
        vc: wavelink.Player = ctx.voice_client
        
        await self.now_playing(ctx)

        if len(vc.queue) == 0:
            return await ctx.send("재생 목록이 비어있습니다.")

        contents = self.queue_to_contents(vc.queue)
        
        embed = discord.Embed(title="[재생 목록]", color=16732671)

        message = await ctx.send(embed=embed)
        page = Page(message, embed, contents)
        await message.edit(view=page)
        await page.set_page()




    @commands.command(name="leave", aliases=['l'])
    async def disconnect(self, ctx: commands.Context) -> None:
        '''
        퇴장 명령어
        '''
        vc: wavelink.Player = ctx.voice_client
        await vc.disconnect()
    






    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        await payload.player.channel.send(embed=self.create_np_embed(payload.track.title, self.format_milliseconds(payload.track.duration), payload.track.uri))





    def create_np_embed(self, title, duration, url) -> discord.Embed:
        return discord.Embed(description="{title} ({duration})".format(
            title=title,
            duration = duration
            ), color=65280)\
            .set_author(name='현재 재생 중인 곡', icon_url='https://i.imgur.com/hKL4A4z.png', url=url)



    def queue_to_contents(self, queue : list) -> list:
        return [{'name' : "{idx}. {title}".format(idx = i+1, title = title),
                        'description':''} 
            for i, title in enumerate(queue)]
    


    def format_milliseconds(self, milliseconds):
        '''
        밀리세컨드 -> 분:초
        '''
        seconds, milliseconds = divmod(int(milliseconds), 1000)
        minutes, seconds = divmod(seconds, 60)
        formatted_time = f"{minutes:02d}:{seconds:02d}"
        return formatted_time

async def setup(bot):
    await bot.add_cog(Music(bot))
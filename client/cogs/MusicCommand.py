import discord, asyncio
import re
import random
from discord.ext import commands
from discord.ext import tasks
from client.module.MusicHelper import MusicHelper
from client.module.Setting import *
from client.button.playlist import Playlist as PB


class MusicCommand(commands.Cog, name="노래"):

    def __init__(self, bot):
        self.bot = bot
        self._tasks = {} # 노래 프로세스
    
    @commands.command(name="join", aliases=['입장', 'j'], help="통화방에 봇을 입장시킵니다.", usage="-join")
    async def join(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
                await channel.connect()
            else:
                await ctx.send("음성 채널 안에서 명령어를 사용해주세요."); return 0

    @commands.command(name="leave", aliases=['퇴장'], help="봇을 통화방에서 퇴장시킵니다.", usage="-leave")
    async def leave(self, ctx):
        try:
            self._tasks[ctx.guild.id].cancel()
        except KeyError:
            pass
        await ctx.voice_client.disconnect()

    @commands.command(name="clear", help="재생 목록을 초기화 시킵니다.", usage="-clear")
    async def clear(self, ctx):
        MusicHelper(ctx).save_playlist([])
        
        await ctx.send("재생 목록을 초기화했습니다!")
        await self.leave(ctx)
        await self.join(ctx)

    @commands.command(name="play", aliases=['재생', 's', 'p'], help="``노래 제목``을 검색하여 플레이리스트에 추가하거나 노래를 재생 및 정지 시킵니다.\n(아무 입력도 안할 시 노래 재생/정지)", usage="-play ``[노래 제목]``")
    async def search(self, ctx, *title):

        if await self.join(ctx) == 0:
            return
        if not len(title):
            if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                self._tasks[ctx.guild.id] = tasks.loop(seconds=0.1)(self.search_wrapper)
                self._tasks[ctx.guild.id].start(ctx)

            if ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await ctx.send(embed=discord.Embed(description="노래를 일시정지 시켰습니다.", color=color['orange']).set_author(name="PAUSE", icon_url='https://i.imgur.com/GxOf2F3.png'))

            elif ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                embed = discord.Embed(description="노래를 다시 재생합니다.", color=color['green'])
                embed.set_author(name="RESUME",icon_url='https://i.imgur.com/QkOdud0.png')
                await ctx.send(embed=embed)
            return

        # 노래 검색
        title = ' '.join(list(title))
        MusicInfo = MusicHelper(ctx=ctx).Search(title)
        content = [f"{i+1}. {name}" for i, name in enumerate(MusicInfo.keys())]

        await ctx.send(embed=discord.Embed(title=f"``{title}`` 를(을) 검색한 결과입니다.", description='\n'.join(content), color=color['blue'])\
            .set_footer(text="※ 원하는 노래의 번호를 선택해주세요. (0 입력 시 취소)").set_thumbnail(url=icon['search']))

        try:
            msg = await self.bot.wait_for('message', timeout=15, check=lambda m : re.compile('[0-5]').match(m.content) != None and m.channel == ctx.channel and m.author == ctx.author)
            if '0' in msg.content: raise asyncio.TimeoutError
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} 노래 선택이 취소되었습니다.")
            return

        # 할당된 노래 code 불러오기 및 플레이리스트 추가
        _title = tuple(MusicInfo)[int(msg.content[0])-1]
        code = MusicInfo[_title]

        MusicHelper(ctx=ctx).add_playlist(songinfo=[code, _title])
        
        await ctx.send(embed=discord.Embed(description=_title, color=color['green']).set_author(name="다음 곡이 재생 목록에 추가되었습니다.", icon_url=icon['success'])\
            .set_footer(icon_url=ctx.author.avatar, text=str(ctx.author.name) + '#' + str(ctx.author.discriminator)))

        if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            self._tasks[ctx.guild.id] = tasks.loop(seconds=0.1)(self.search_wrapper)
            self._tasks[ctx.guild.id].start(ctx)
    
    async def search_wrapper(self, ctx):

        if ctx.voice_client is None:
            await ctx.send(embed=discord.Embed(description='음성 채널에 초대해야 노래 재생이 가능합니다.', color=color['yellow']).set_author(name="재생 불가", icon_url=icon['warning'])); self._tasks[ctx.guild.id].cancel()

        if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            playlist = MusicHelper(ctx=ctx).load_playlist()

            if not len(playlist):
                await ctx.send(embed=discord.Embed(description='재생 목록에 노래가 없습니다.', color=color['yellow']).set_author(name="재생 불가", icon_url=icon['warning'])); self._tasks[ctx.guild.id].cancel()

            msg = await ctx.send(embed=discord.Embed(description=playlist[0].split('---')[1], color=color['yellow']).set_author(name="다음 곡을 재생합니다. 잠시만 기다려주세요.", icon_url=icon['loading']))
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            ctx.voice_client.play(discord.FFmpegPCMAudio(source=MusicHelper(ctx=ctx).getLink(code=playlist[0].split('---')[0]), executable='./client/ffmpeg/bin/ffmpeg.exe', **FFMPEG_OPTIONS))
            # ctx.voice_client.play(discord.FFmpegPCMAudio(executable = './client/ffmpeg/bin/ffmpeg.exe', source=f'./{MusicHelper(ctx=ctx).songpath}{song}.mp3'))

            await self.nowplaying(ctx, msg_obj=msg)

            while ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                await asyncio.sleep(0.1)
            
            MusicHelper(ctx=ctx).recently_remove()





    # 재생 목록 확인
    @commands.command(name="queue", aliases=['목록', 'q'], help="서버의 재생 목록을 확인합니다.", usage="-queue")
    async def queue(self, ctx):

        await self.queue_wrapper(ctx=ctx)

            
    async def queue_wrapper(self, ctx, user_id=None):
        playlist = ["{0}. {1}".format(i+1, p.split('---')[1]) for i, p in enumerate(MusicHelper(ctx=ctx).load_playlist(user_id=user_id))]

        if len(playlist) == 0:
            await ctx.send("재생 목록이 비어있습니다!"); return
        

        embed = discord.Embed(title="{0}님의 재생 목록".format(ctx.author.name) if user_id != None else '재생 목록', description='\n'.join(playlist[:5]), color=color['sky'])\
            .set_thumbnail(url='https://i.imgur.com/nMxWMtB.png')

        page = int(len(playlist) / 5 + 1) if len(playlist)  > 5 and len(playlist) % 5 >= 1 else int(len(playlist) / 5)

        if page > 1:
            await ctx.send(embed = embed.set_footer(text=f"1/{page}"), view=PB(ctx=ctx, user_id=user_id))
        else:
            await ctx.send(embed=embed)
    



    @commands.command(name="shuffle", aliases=['셔플', 'sf'], help="재생 목록의 순서를 랜덤으로 섞습니다.", usage='-shuffle')
    async def shuffle(self, ctx):
        playlist = MusicHelper(ctx).load_playlist()
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            _p = playlist[0]
            playlist = playlist[1:]
            random.shuffle(playlist)
            playlist = [_p] + playlist
        else:
            random.shuffle(playlist)
        MusicHelper(ctx).save_playlist(playlist)
        await ctx.send(embed=discord.Embed(title="SHUFFLE", description="재생 목록의 순서를 랜덤으로 섞었습니다!", color=color['purple']).set_thumbnail(url='https://i.imgur.com/to24Xi1.png'))


    @commands.command(name="skip", aliases=['스킵', 'ss'], help="현재 재생 중인 노래를 다음 노래로 스킵합니다.", usage="-skip")
    async def skip(self, ctx):
        self._tasks[ctx.guild.id].cancel(); ctx.voice_client.stop()
        await ctx.send(embed=discord.Embed(description="{0}".format(MusicHelper(ctx).load_playlist()[0].split('---')[1]), color=color['orange'])\
            .set_author(name="SKIP", icon_url='https://i.imgur.com/82VL1OJ.png'))
        MusicHelper(ctx=ctx).recently_remove()
        self._tasks[ctx.guild.id].start(ctx)


    @commands.command(name='nowplay', aliases=['np'], help="재생 목록에서 ``번호``에 해당하는 노래를 맨 앞으로 가져옵니다.\n(아무 입력 없을 시 재생 중인 노래 확인)", usage="-nowplay ``[번호]``")
    async def nowplaying(self, ctx, number=0, msg_obj=None):
        if int(number) >= 2:
            playlist = MusicHelper(ctx).load_playlist()
            try:
                if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                    playlist.insert(1, playlist[int(number)-1])
                else:
                    playlist.insert(0, playlist[int(number)-1])
                playlist.pop(int(number))
            except IndexError:
                raise commands.ArgumentParsingError; return
            MusicHelper(ctx).save_playlist(playlist)
            if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                await self.skip(ctx)
            else:
                await ctx.send(embed=discord.Embed(description="{0}".format(playlist[0].split('---')[1]), color=color['green']).set_author(name="다음 곡을 맨 앞으로 가져왔습니다.", icon_url=icon['success']))

                
        elif ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            playlist = MusicHelper(ctx=ctx).load_playlist()

            embed=discord.Embed(description="{0}".format(playlist[0].split('---')[1]), color=color['green'])\
                .set_author(name='현재 재생 중인 곡', icon_url='https://i.imgur.com/hKL4A4z.png')

            if msg_obj != None:
                await msg_obj.edit(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            await ctx.send('재생 중인 곡이 없습니다!'); return
    
    @commands.command(name="remove", aliases=['삭제', 'r'], help="재생 목록에서 ``번호``에 해당하는 노래를 삭제합니다.", usage="-remove ``[번호]``")
    async def remove_playlist(self, ctx, number=None):
        playlist = MusicHelper(ctx=ctx).load_playlist()
        if ctx.voice_client:
            if (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()) and number == '1':
                await ctx.send(embed=discord.Embed(description=f"듣고 있는 노래는 삭제할 수 없습니다.", color=color['yellow']).set_author(name="삭제 불가", icon_url=icon['warning'])); return
        try:
            title = playlist[int(number)-1].split('---')[1]
            playlist.pop(int(number)-1)
            await ctx.send(embed=discord.Embed(description=f"재생 목록에서 ``{title}`` 를(을) 삭제했습니다.", color=color['red']).set_author(name="DELETE", icon_url=icon['minus']))
            MusicHelper(ctx=ctx).save_playlist(playlist=playlist)
        except IndexError:
            raise commands.ArgumentParsingError
    

    @commands.command(name="loop", aliases=['lp', '반복', '루프'], help="재생 목록의 반복을 ON/OFF 합니다.", usage="-loop")
    async def loop(self, ctx):

        config = MusicHelper(ctx=ctx).load_config()
        if config['LOOP']:
            await ctx.send(embed=discord.Embed(description="재생 목록의 노래 반복을 껐습니다.", color=color['red']).set_author(name="노래 반복 OFF").set_thumbnail(url='https://i.imgur.com/QRkc09a.png'))
        else:
            await ctx.send(embed=discord.Embed(description="재생 목록의 노래를 반복시킵니다.", color=color['green']).set_author(name="노래 반복 ON").set_thumbnail(url='https://i.imgur.com/QRkc09a.png'))
        
        config['LOOP'] = not config['LOOP']
        MusicHelper(ctx=ctx).save_config(config)
    

    @commands.command(name="playlist", aliases=['재생목록', '플레이리스트'], help="개인 재생 목록을 저장하거나 불러옵니다.", usage='-재생목록 [저장/불러오기/확인]')
    async def playlist(self, ctx, option):
        try:
            if option == '저장':
                MusicHelper(ctx=ctx).save_playlist(playlist=MusicHelper(ctx=ctx).load_playlist(), user_id=ctx.author.id)
                await ctx.send(embed=discord.Embed(description='현재 서버의 플레이리스트를 저장했습니다!', color=color['green']).set_author(name="PLAYLIST SAVED", icon_url=icon['success']))

            elif option == '불러오기':
                MusicHelper(ctx=ctx).save_playlist(playlist=MusicHelper(ctx=ctx).load_playlist(user_id=ctx.author.id))
                await ctx.send(embed=discord.Embed(description="개인 플레이리스트를 서버로 불러왔습니다!", color=color['green']).set_author(name="PLAYLIST LOADED", icon_url=icon['success'])\
                .set_footer(icon_url=ctx.author.avatar, text=str(ctx.author.name) + '#' + str(ctx.author.discriminator)))
            
            elif option == '확인':
                await self.queue_wrapper(ctx=ctx, user_id=ctx.author.id)
            else:
                raise commands.ArgumentParsingError
        except FileNotFoundError:
            await ctx.send(embed = discord.Embed(description=f"{ctx.author.name}님의 개인 재생목록을 찾지못했습니다.\n", color = color['red']).set_author(name="명령어 오류", icon_url=icon['error']))


async def setup(bot):
    await bot.add_cog(MusicCommand(bot))
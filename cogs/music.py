import discord, youtube_dl, re, asyncio, random
from discord.ext import commands, tasks
from youtubesearchpython import VideosSearch
from view.setting import *
from view.button.search_btn import search_btn
from view.button.queue_btn import queue_btn


class MusicCog(commands.Cog, name="노래"):

    def __init__(self, bot):
        self.bot = bot
        self.playlist = {} # 서버별 플레이리스트 {서버 아아디:[ 리스트 ]}
        self.config = {} # 서버별 설정 값
        self.music_tasks = {} # 서버별 노래 작업 목록
        self.leave_tasks = {} # 자동 퇴장 작업 목록 
        
        for guild in self.bot.guilds:
            self.playlist[guild.id] = []
            self.config[guild.id] = {'loop':False}


    def channel_checker(ctx): # 채널 체크
        return ctx.message.author.voice.channel.id == ctx.channel.id


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(embed = discord.Embed(description="통화방 채팅창으로 명령어를 입력해주세요.\n", color = color['red']).set_author(name="ERROR", icon_url=icon['error']), ephemeral=True)

    @commands.command(name='join', aliases=['j'], help='봇을 통화방에 입장시킵니다.')
    async def join(self, ctx):
        if ctx.author.voice is None: 
            await ctx.send("음성 채널 안에서 명령어를 사용해주세요."); return -1
        elif ctx.voice_client: # 채널 이동
            await self.leave(ctx)
        await ctx.author.voice.channel.connect()
    
    async def auto_leave(self, ctx):
        self.leave_tasks[ctx.guild.id][1] += 1

        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            self.leave_tasks[ctx.guild.id][0].cancel()

        if len(self.playlist[ctx.guild.id]) == 0 and self.leave_tasks[ctx.guild.id][1] > 5:
            await ctx.send("저를 장시간 사용하지 않으셔서 나가볼게요!")
            await self.leave(ctx); self.leave_tasks[ctx.guild.id][0].cancel()

    @commands.command(name="leave", aliases=['l'], help="봇을 통화방에서 퇴장시킵니다.")
    @commands.check(channel_checker)
    async def leave(self, ctx):
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop(); self.music_tasks[ctx.guild.id].cancel()

        await ctx.voice_client.disconnect()
        ctx.voice_client.cleanup()
    
    @commands.command(name="penguin", aliases=['ra'], help="재생 목록에 펭귄이 듣고싶은 노래를 추가합니다.")
    @commands.check(channel_checker)
    async def random_play(self, ctx):
        random_list = [['Sg9ZhQ1Fh_8', '윤하 - 별의 조각 / 가사'], ['kTVvtlfU-Ts', '윤하 (Younha) - 우산 (Umbrella) MV'], ['RbU15mACccA', '다시 사랑한다면 (니글니글 버터플라이)'], ['IYKWrrbTcoE', '부활 - 생각이나'], ['eN5mG_yMDiM', "BIGBANG - '봄여름가을겨울 (Still Life)' M/V"], ['yzqlG3H_y_0', 'V.O.S - 울어'], ['kQuxJbP6s8Y', '10CM – Gradation (그라데이션) / Kpop /OST /Lyrics / 가사 / 한글'], ['lAq9l8o6UXU', '주호 - 내가 아니라도 [가사]'], ['UcNLtxj6PA0', '[MV] NAMJAE(남재) - Late night(새벽)'], ['VNxUy2ua9AM', '부활 - 비밀'], ['GuxMQ0Nom7w', '성시경 - 거리에서 / 가사'], ['YRKR45rYoLg', "멜로망스 - 고백 (세 번째 '고백') / 가사"], ['iwgkwriv0OE', 'TOIL, Kid Wine - 네 옆에 그 사람은 내가 아닌 다른사람ㅣLyrics/가사'], ['iAfxyHOmHrM', '경서 - 나의 X에게 || 가사'], ['Fz8bjQZOrNw', '로시 (Rothy) - Stars MV'], ['1Mc-h-lLgH4', '길구봉구 바람이 불었 으면 좋겠어 - 01 바람이 불었으면 좋겠어'], ['LliTOhG60w4', '허각 - 그 시간, 그 공간 (안녕? 나야! OST) [Music Video]'], ['XyzaMpAVm3s', '[MV] DAVICHI(다비치) - This Love(이 사랑) l Descendants of the Sun 태양 의 후예 OST'], ['8WqEp8nbgPg', 'Ailee(에일리) _ Evening sky(저녁 하늘) MV'], ['M15SI00umn4', '[가사] 부활 - 네버엔딩스토리 (Never Ending Story)(lyrics)'], ['iZEXqZoIK_Q', 'BIG Naughty (서동현) - 정이라고 하자 (Feat. 10CM) [정이라고 하자]ㅣLyrics/가사']]
        
        song = random.sample(random_list, 1)
        self.playlist[ctx.guild.id] += song
        await ctx.send(embed=discord.Embed(description=song[0][1], color=color['green']).set_author(name="다음 곡이 재생 목록에 추가되었습니다.", icon_url=icon['success'])\
        .set_footer(icon_url=self.bot.user.avatar, text=str(self.bot.user.name) + '#' + str(self.bot.user.discriminator)))
        if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()): # 노래가 재생 중이지 않다면 새로운 루프로 노래 재생
            self.music_tasks[ctx.guild.id] = tasks.loop(seconds=0.1)(self.play_wrapper); self.music_tasks[ctx.guild.id].start(ctx)
    

    @commands.command(name="play", aliases=['p', 's'], help="노래를 재생시킵니다.")
    @commands.check(channel_checker)
    async def play(self, ctx, *title):
        if not ctx.voice_client: # 통화방에 없는 경우 join 함수 실행
            if await self.join(ctx) == -1: return

        title = ' '.join(list(title))

        if title == '': # 제목 없이 입력했을 경우 노래 재생/일시정지
            if ctx.voice_client.is_playing():
                ctx.voice_client.pause()
                await ctx.send(embed=discord.Embed(description="노래를 일시정지 시켰습니다.", color=color['orange']).set_author(name="PAUSE", icon_url='https://i.imgur.com/GxOf2F3.png'))
            elif ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                await ctx.send(embed=discord.Embed(description="노래를 다시 재생합니다.", color=color['green']).set_author(name="RESUME",icon_url='https://i.imgur.com/QkOdud0.png'))
            elif self.playlist[ctx.guild.id] != []:
                self.music_tasks[ctx.guild.id] = tasks.loop(seconds=0.1)(self.play_wrapper); self.music_tasks[ctx.guild.id].start(ctx)
            else:
                raise commands.ArgumentParsingError
        else:
            search_result = {i:None for i in range(5)}
            for idx, video in enumerate(VideosSearch(title, limit = 5).result()['result']):
                if video['duration'] == None: # 라이브 방송 중인 목록 재생 불가 처리
                    video['duration'] = '재생 불가'
                    video['title'] = f"~~{video['title']}~~"

                video['title'] += " (" + video['duration'] + ")"
                # [링크, 제목]
                search_result[idx] = [video['link'].replace('https://www.youtube.com/watch?v=', ''), \
                    video['title']]
            
            
            search_msg = await ctx.send(embed=discord.Embed(title=f"``{title}`` 를(을) 검색한 결과입니다.",\
                 description='\n'.join([f"{i+1}. {search_result[i][1]}" for i in range(5)]), color=color['blue'])\
                .set_footer(text="※ 원하는 노래의 번호를 선택해주세요. (0 입력 시 취소)").set_thumbnail(url=icon['search']), view=search_btn(ctx))


            def check(m):
                if re.compile('[0-5]').match(m.content) != None:
                    if m.author.bot or (m.channel == ctx.channel and m.author == ctx.author): # 채팅 입력한 사람이 본인이거나 봇일 경우
                        return True

            try:
                music_select = await self.bot.wait_for('message', timeout=15, check=check)
                if '0' in music_select.content: raise asyncio.TimeoutError
            except asyncio.TimeoutError:
                await ctx.send(f"{ctx.author.mention} 노래 선택이 취소되었습니다."); return
            finally:
                await search_msg.delete()

            
            self.playlist[ctx.guild.id] += [search_result[int(music_select.content)-1]]
            
            await ctx.send(embed=discord.Embed(description=search_result[int(music_select.content)-1][1], color=color['green']).set_author(name="다음 곡이 재생 목록에 추가되었습니다.", icon_url=icon['success'])\
                .set_footer(icon_url=ctx.author.avatar, text=str(ctx.author.name) + '#' + str(ctx.author.discriminator)))
            await music_select.delete()

            if not (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()): # 노래가 재생 중이지 않다면 새로운 루프로 노래 재생
                self.music_tasks[ctx.guild.id] = tasks.loop(seconds=0.1)(self.play_wrapper); self.music_tasks[ctx.guild.id].start(ctx)



    async def play_wrapper(self, ctx):
        try:
            now_playdata = self.playlist[ctx.guild.id][0] # 재생할 노래의 데이터 [코드, 제목]
        except IndexError:
            await ctx.send(embed=discord.Embed(description="모든 노래의 재생이 끝났습니다! 더 들으시려면 재생 목록을 추가해주세요!", color=color['green']).set_author(name="재생 종료", icon_url=icon['success']))
            self.leave_tasks[ctx.guild.id] = [tasks.loop(seconds=24)(self.auto_leave), 0]; self.leave_tasks[ctx.guild.id][0].start(ctx) # 자동 퇴장 활성화
            self.music_tasks[ctx.guild.id].cancel(); return
        
        play_msg = await ctx.send(embed=discord.Embed(description=now_playdata[1], color=color['yellow']).set_author(name="다음 곡을 재생합니다. 잠시만 기다려주세요.", icon_url=icon['loading']))

        with youtube_dl.YoutubeDL({'format': 'bestaudio'}) as ydl:
            audio_link = ydl.extract_info(f'https://www.youtube.com/watch?v={now_playdata[0]}', download=False)['formats'][0]['url'] # 영상의 오디오 링크 저장


        FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        ctx.voice_client.play(discord.FFmpegPCMAudio(audio_link, **FFMPEG_OPTIONS)) # 노래 재생
        
        await play_msg.edit(embed=discord.Embed(description=now_playdata[1], color=color['green'])\
            .set_author(name='현재 재생 중인 곡', icon_url='https://i.imgur.com/hKL4A4z.png', url='https://www.youtube.com/watch?v=' + now_playdata[0]))
            
        while ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            await asyncio.sleep(0.1)


        if self.config[ctx.guild.id]['loop']:
            self.playlist[ctx.guild.id] += [now_playdata]
        self.playlist[ctx.guild.id].remove(now_playdata)


    @commands.command(name="queue", aliases=['q'], help="서버의 재생 목록을 확인합니다.")
    @commands.check(channel_checker)
    async def queue(self, ctx):

        embed = discord.Embed(title="재생 목록", color=color['sky'])
        titles = [f"{i+1}. " + song[1] for i, song in enumerate(self.playlist[ctx.guild.id])]
        embed.description = '\n'.join(titles[:5])
        msg = await ctx.send(embed=embed)

        if len(titles) > 5:
            await msg.edit(view=queue_btn(ctx=ctx, msg=msg, embed=embed, playlist=titles, obj=self))

    

    @commands.command(name="remove", aliases=["r"], help="재생 목록의 노래를 삭제합니다.")
    @commands.check(channel_checker)
    async def remove_playlist(self, ctx, number:int):
        await ctx.send(embed=discord.Embed(description=f"재생 목록에서 ``{self.playlist[ctx.guild.id][number-1][1]}`` 를(을) 삭제했습니다.", color=color['red']).set_author(name="DELETE", icon_url=icon['minus']))
        self.playlist[ctx.guild.id].pop(number-1)
        

    @commands.command(name='nowplay', aliases=["np"], help="현재 재생 중인 곡을 확인하거나 바꿉니다.")
    @commands.check(channel_checker)
    async def nowplay(self, ctx, number:int = None):
        if not number is None:
            self.playlist[ctx.guild.id][0] = self.playlist[ctx.guild.id][number-1]
            self.playlist[ctx.guild.id].pop(number-1)
            await ctx.send(embed=discord.Embed(description=f"{self.playlist[ctx.guild.id][0][1]}", color=color['green']).set_author(name="다음 곡을 맨 앞으로 가져왔습니다.", icon_url=icon['success']))
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused(): # 노래를 듣는 중이였다면
                ctx.voice_client.stop(); self.music_tasks[ctx.guild.id].restart(ctx)
        else:
            if ctx.voice_client is None  or not ctx.voice_client.is_playing():
                await ctx.send("노래가 재생 중이지 않아요!")
            else: # elif ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
                await ctx.send(embed=discord.Embed(description=f"{self.playlist[ctx.guild.id][0][1]}", color=color['green'])\
                    .set_author(name='현재 재생 중인 곡', icon_url='https://i.imgur.com/hKL4A4z.png', url='https://www.youtube.com/watch?v='+self.playlist[ctx.guild.id][0][0]))

    @commands.command(name='loop', aliases=['lp'], help='재생목록 반복을 ON/OFF 합니다.')
    @commands.check(channel_checker)
    async def playlist_loop(self, ctx):
        self.config[ctx.guild.id]['loop'] = not self.config[ctx.guild.id]['loop']
        _set = ['켰', 'green', 'ON'] if self.config[ctx.guild.id]['loop'] else ['껐', 'red', 'OFF']
        await ctx.send(embed=discord.Embed(description=f"재생 목록 반복을 {_set[0]}습니다.", color=color[f'{_set[1]}'])\
            .set_author(name=f"노래 반복 {_set[2]}").set_thumbnail(url='https://i.imgur.com/QRkc09a.png'))


    @commands.command(name='skip', aliases=['ss'], help='현재 재생 중인 노래를 스킵합니다.')
    @commands.check(channel_checker)
    async def skip(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await ctx.send("노래가 재생 중이지 않아요!")
        else: # elif ctx.voice_client.is_playing() or ctx.voice_client.is_paused()
            await ctx.send(embed=discord.Embed(description=f"{self.playlist[ctx.guild.id][0][1]}", color=color['orange'])\
                .set_author(name="SKIP", icon_url='https://i.imgur.com/82VL1OJ.png'))
            if self.config[ctx.guild.id]['loop']:
                self.playlist[ctx.guild.id] += [ self.playlist[ctx.guild.id][0] ]
            self.playlist[ctx.guild.id].pop(0)
            ctx.voice_client.stop(); self.music_tasks[ctx.guild.id].restart(ctx)
    
    @commands.command(name='shuffle', aliases=['sf'], help='재생 목록을 랜덤으로 섞습니다.')
    @commands.check(channel_checker)
    async def shuffle(self, ctx):
        if len(self.playlist[ctx.guild.id]) == 0:
            await ctx.send('재생 목록이 비어있습니다!'); return
        now_playdata = self.playlist[ctx.guild.id][0]; self.playlist[ctx.guild.id].pop(0)
        random.shuffle(self.playlist[ctx.guild.id]); self.playlist[ctx.guild.id].insert(0, now_playdata)
        await ctx.send(embed=discord.Embed(title="SHUFFLE", description="재생 목록의 순서를 랜덤으로 섞었습니다!", color=color['purple']).set_thumbnail(url='https://i.imgur.com/to24Xi1.png'))


    @commands.command(name='clear', help='재생 목록을 초기화합니다.')
    @commands.check(channel_checker)
    async def clear(self, ctx):
        self.playlist[ctx.guild.id] = []
        await ctx.send('재생 목록을 초기화했습니다!')
        ctx.voice_client.stop(); self.music_tasks[ctx.guild.id].cancel()
        
async def setup(bot):
    await bot.add_cog(MusicCog(bot))
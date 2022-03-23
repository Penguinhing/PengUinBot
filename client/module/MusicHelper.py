from youtubesearchpython import VideosSearch
import youtube_dl
import glob
import os
import pickle

class MusicHelper:

    def __init__(self, ctx):
        self.songpath = 'data/music/songs/'
        self.server_playpath = 'data/music/playlist/server/'
        self.configpath = 'data/music/config/'
        self.server_id = ctx.guild.id
        try:
            os.listdir(self.server_playpath).index(f"{self.server_id}.txt")
        except ValueError:
            with open(self.server_playpath + f"{self.server_id}.txt", 'wb') as FILE:
                pickle.dump([], FILE)
            with open(self.configpath + f"{self.server_id}.txt", 'wb') as FILE:
                pickle.dump({"LOOP":False}, FILE)

    def Search(self, title):
        videosSearch = VideosSearch(title, limit = 5).result()
        return {video['title']:video['link'].replace('https://www.youtube.com/watch?v=', '') for video in videosSearch['result']}
    
    def getLink(self, code):
        ydl_opts = {
            'format': 'bestaudio',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f'https://www.youtube.com/watch?v={code}', download=False)
            return info['formats'][0]['url']
    
    # 플레이리스트 추가 songinfo = [code, title]
    def add_playlist(self, songinfo):        
        playlist = self.load_playlist()
        playlist += [f"{songinfo[0]}---{songinfo[1]}"]
        self.save_playlist(playlist=playlist)
    
    # 플레이리스트 불러오기
    def load_playlist(self):
        with open(f"{self.server_playpath}{self.server_id}.txt", 'rb') as FILE:
            return pickle.load(FILE)

    # 플레이리스트 저장
    def save_playlist(self, playlist):
        with open(self.server_playpath + f"{self.server_id}.txt", 'wb') as FILE:
            pickle.dump(playlist, FILE)

    
    def load_config(self):
        with open(f"{self.configpath}{self.server_id}.txt", 'rb') as FILE:
            return pickle.load(FILE)

    def save_config(self, config):
        with open(self.configpath + f"{self.server_id}.txt", 'wb') as FILE:
            pickle.dump(config, FILE)
    
    # 가장 첫번째 플레이리스트 삭제
    def recently_remove(self):

        config = self.load_config()
        playlist = self.load_playlist()

        if config['LOOP']:
            playlist += [ playlist[0] ]

        playlist.pop(0)
        
        self.save_playlist(playlist=playlist)
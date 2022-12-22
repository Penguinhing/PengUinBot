import pymysql
from discord.ext import commands

class MySQL(commands.Cog, name='mysql'):
    def __init__(self, bot):
        self.conn = pymysql.connect(host='127.0.0.1', user='root', password='password', db='penguin')

    def __del__(self):
        self.conn.close()

    async def _execute(self, context): # 반환값 X
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(context); self.conn.commit(); cur.close()

    async def fetch_all_data(self, context):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(context); self.conn.commit(); cur.close()
            return cur.fetchall()

    async def fetch_one_data(self, context):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(context); self.conn.commit(); cur.close()
            return cur.fetchone()


async def setup(bot):
    await bot.add_cog(MySQL(bot))
    
    

'''
CREATE TABLE user_info(SERVER_ID CHAR(18), MEMBER_ID CHAR(18), UUID CHAR(25) UNIQUE, VOICE_TIME INT DEFAULT 0, EXP INT DEFAULT 0,TOTAL_EXP INT DEFAULT 0, CURRENT_LEVEL INT DEFAULT 0); # 유저 정보 테이블
CREATE TABLE level_up(SERVER_ID CHAR(18) NOT NULL PRIMARY KEY, CHANNEL_ID CHAR(18)); # 레벨업 알림 테이블
CREATE TABLE level_role(SERVER_ID CHAR(18) NOT NULL, ROLE_ID CHAR(24) UNIQUE, CURRENT_LEVEL INT); # 레벨 역할 테이블
'''
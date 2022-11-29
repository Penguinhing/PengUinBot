import pymysql
from discord.ext import commands

class MySQL(commands.Cog, name='mysql'):
    def __init__(self, bot):
        self.conn = pymysql.connect(host='localhost', user='root', password='your password', db='penguin')

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
 CREATE TABLE voice_rank_notice(SERVER_ID VARCHAR(25) NOT NULL PRIMARY KEY, CHANNEL_ID VARCHAR(25));
 CREATE TABLE voice_rank(SERVER_ID VARCHAR(25) NOT NULL, ROLE_ID VARCHAR(25), TIME INT);
 CREATE TABLE voice_ranker(SERVER_ID VARCHAR(25) NOT NULL, ROLE_ID VARCHAR(25)); (ALTER TABLE voice_ranker ADD UNIQUE (SERVER_ID);)
  CREATE TABLE voice_time(SERVER_ID VARCHAR(25) NOT NULL, MEMBER_ID VARCHAR(25), TIME INT);

'''
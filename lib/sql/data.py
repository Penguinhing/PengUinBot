import pymysql

class Query:
    

    def create_connection(self):
        self.conn = pymysql.connect(host='127.0.0.1', user='a', password='b', db='c', autocommit=True)
        self.cur = self.conn.cursor(pymysql.cursors.DictCursor)

    def __init__(self) -> None:
        self.create_connection()

    def connection(function):
        def wrapper(self, query):
            try:
              result = function(self, query)

            except pymysql.err.OperationalError as e:
                print('try reconnect')
                self.conn.close()
                self.create_connection()
                result = function(self, query)
            
            return result
        return wrapper

    @connection
    def execute(self, query):
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
          cur.execute(query)

    @connection
    def fetchOne(self, query) -> dict:
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
          cur.execute(query)
          return cur.fetchone()
    
    @connection
    def fetchAll(self, query) -> dict:
        with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
          cur.execute(query)
          return cur.fetchall()

'''
CREATE TABLE `s1025_peng`.`server_info` (
  `SERVER_ID` VARCHAR(45) NOT NULL,
  `LOG_CHANNEL` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`SERVER_ID`),
  UNIQUE INDEX `LOG_CHANNEL_UNIQUE` (`LOG_CHANNEL` ASC) VISIBLE);


CREATE TABLE `s1025_peng`.`member_info` (
  `SERVER_ID` VARCHAR(45) NOT NULL,
  `MEMBER_ID` VARCHAR(45) NOT NULL,
  `VOICE_TIME` INT NULL DEFAULT 0,
  `EXP` INT NULL DEFAULT 0,
  PRIMARY KEY (`SERVER_ID`, `MEMBER_ID`));



  
CREATE TABLE `s1025_peng`.`ranks` (
  `RANK_ID` BIGINT NOT NULL AUTO_INCREMENT,
  `SERVER_ID` VARCHAR(45) NOT NULL,
  `LEVEL` INT NOT NULL DEFAULT 0,
  `ROLE_ID` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`RANK_ID`));


  CREATE TABLE `s1025_peng`.`level_info` (
  `LEVEL` INT NOT NULL,
  `EXP` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`LEVEL`),
  UNIQUE INDEX `EXP_UNIQUE` (`EXP` ASC) VISIBLE);

'''
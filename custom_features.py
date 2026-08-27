# custom_features.py 扩展_自定义功能 每当产生新的日志，都会调用这里。可以用来定制功能
import re
import __main__


def 扩展_自定义功能(line):
    """ 当有玩家发送违规词语[Meteor on Crack] 那么就直接/ban-ip """
    if "Meteor on Crack" in line:
        rcon = getattr(__main__, 'rcon_client', None)
        if rcon is None:return
        player = None
        
        match1 = re.search(r'<([a-zA-Z0-9_]+)>', line)  # 格式1：<玩家名>
        if match1:
            player = match1.group(1)
        else:
            match2 = re.search(r'\|\s*([a-zA-Z0-9_]+)§7:', line)  # 格式2：| 玩家名§7:
            if match2:
                player = match2.group(1)
        
        if player is None:return  # 两种格式都没匹配到，放弃
        

        print(f"[CHEAT] 封禁作弊玩家: {player}")
        rcon.send_command(f"ban-ip {player} 因使用作弊客户端被封禁")
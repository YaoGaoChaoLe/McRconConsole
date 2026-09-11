# custom_features.py
import re
import __main__

def 扩展_自定义功能(line, server_name):
    """ 当有玩家发送违规词语[Meteor on Crack] 那么就直接/ban-ip """
    if "Meteor on Crack" in line:
        return 0 # 不启用喵 ovo

        rcon_manager = getattr(__main__, 'rcon_manager', None)
        if rcon_manager is None:
            return

        player = None
        match1 = re.search(r'<([a-zA-Z0-9_]+)>', line)
        if match1:
            player = match1.group(1)
        else:
            match2 = re.search(r'\|\s*([a-zA-Z0-9_]+)§7:', line)
            if match2:
                player = match2.group(1)

        if player is None:
            return

        print(f"[CHEAT] 在 [{server_name}] 封禁作弊玩家: {player}")
        rcon_manager.send_command(server_name, f"ban-ip {player} 因为发送了某些消息，被封禁")
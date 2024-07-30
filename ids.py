from pagermaid.listener import listener
from pagermaid.utils import alias_command
from pyrogram.errors import PeerIdInvalid, UsernameNotOccupied
from pyrogram.types import User

# DC编号到国家的映射
dc_country_mapping = {
    1: "Miami, USA",
    2: "Amsterdam, NLD",
    3: "Miami, USA",
    4: "Amsterdam, NLD",
    5: "Singapore",
    # 在这里添加更多的映射
}

def estimate_level(id):
    if id == 2075484113:
        return "正国级"
    elif id > 7000000000:
        return "普通科员"
    elif id >= 6000000000:
        return "副科级"
    elif id >= 5000000000:
        return "正科级" 
    elif id >= 4000000000:
        return "副处级" 
    elif id >= 3000000000:
        return "正处级"  
    elif id >= 2000000000:
        return "副厅级"  
    elif id >= 1000000000:
        return "正厅级"  
    elif id >= 500000000:
        return "副部级" 
    elif id >= 100000000:
        return "正部级" 
    elif id >= 50000000:
        return "副国级" 
    else:
        return "正国级" 

@listener(is_plugin=True, outgoing=True, command=alias_command("ids"))
async def ids_handler(client, message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        if len(message.command) == 1:
            user = message.command[0]
            if user.isdigit():
                user = int(user)
        else:
            user = await client.get_me()

        if message.entities is not None:
            if message.entities[0].type == 'text_mention':
                user = message.entities[0].user
            if message.entities[0].type == 'phone_number':
                user = int(message.command[0])
        if not isinstance(user, User):
            try:
                user = await client.get_users(user)
            except PeerIdInvalid:
                return await message.edit('输入的用户ID无效。')
            except UsernameNotOccupied:
                return await message.edit('用户名无效或者并未被使用。')
            except Exception as e:
                raise e

    id = user.id
    nickname = user.first_name or ""
    nickname += f" {user.last_name}" if user.last_name else ""
    username = f"@{user.username}" if user.username else "无"
    user_level = estimate_level(id)
    dc = user.dc_id if user.dc_id else "N/A"
    country = dc_country_mapping.get(dc, "未知")

    # 获取共同群组数量
    try:
        common_chats = await client.get_common_chats(user.id)
        common_chats_count = len(common_chats)
    except Exception as e:
        common_chats_count = "获取共同群组时出错"
        print(f"Error: {e}")

    await message.edit(
        f"ID: {id}\n"
        f"DC{dc}: {country}\n"
        f"昵称: [{nickname}](tg://user?id={id})\n"
        f"等级: {user_level}\n"
        f"用户名: {username}\n"
        f"共同群: {common_chats_count} 个\n"
        f"TG链接: tg://user?id={id}"
    )
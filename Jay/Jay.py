# 歌词猫&PagerMaid-Pyro
# 名字加粗表示未成功连接到API
from secrets import choice

from pagermaid import log, Config
from pagermaid.listener import listener
from pagermaid.enums import Message
from pagermaid.services import client as request, scheduler
from pagermaid.hook import Hook


class FaDian:
    def __init__(self):
        self.data = {
            "data": [
"乌云在我们心里搁下一块阴影☁️\n我聆听沉寂已久的心情👂\n清晰透明 就像美丽的风景🏞️\n总在回忆里才看得清🔍",
"被伤透的心能不能够继续爱我💔\n我用力牵起没温度的双手🤲\n过往温柔 已经被时间上锁🔒\n只剩挥散不去的难过😞",
"缓缓飘落的枫叶像思念🍁\n为何挽回要赶在冬天来之前❄️\n爱**{name}**穿越时间⏳\n两行来自秋末的眼泪😢\n让爱渗透了地面💧\n我要的只是**{name}**在我身边👫",
"缓缓飘落的枫叶像思念🍁\n我点燃烛火温暖岁末的秋天🕯️\n极光掠夺天边🌌\n北风掠过想**{name}**的容颜🌬️\n我把爱烧成了落叶🔥\n却换不回熟悉的那张脸😔",
"久未放晴的天空☁️\n依旧留着**{name}**的笑容🌈\n哭过 却无法掩埋歉疚💧",
"风筝在阴天搁浅🪁\n想念还在等待救援🆘\n我拉着线 复习**{name}**给的温柔📚",
"曝晒在一旁的寂寞☀️\n笑我给不起承诺😅\n怎么会 怎么会🤔\n**{name}**竟原谅了我🕊️",
"我只能永远读着对白📜\n读着我给**{name}**的伤害💔\n我原谅不了我🚫\n就请**{name}**当作我已不在👻",
"我睁开双眼 看着空白👀\n忘记**{name}**对我的期待🚶‍♂️\n读完了依赖 我很快就离开✈️",
"怎么隐藏 我的悲伤😢\n失去**{name}**的地方📍\n**{name}**的发香 散的匆忙💨\n我已经跟不上🏃‍♂️",
"闭上眼睛 还能看见👀\n**{name}**离去的痕迹👣\n在月光下 一直找寻🌙\n那想念的身影👤",
"如果说分手是苦痛的起点🍂\n那在终点之前⏳\n我愿意再爱一遍💔\n想要对**{name}**说的\n不敢说的爱💬\n会不会有人可以明白👥",
"我会发着呆 然后忘记**{name}**😶\n接着紧紧闭上眼🙈\n想着那一天 会有人代替🔄\n让我不再想念**{name}**💔",
"我会发着呆 然后微微笑😊\n接着紧紧闭上眼🙈\n又想了一遍 **{name}**温柔的脸😌\n在我忘记之前🍂",
"又想了一遍 **{name}**温柔的脸😌\n在我忘记之前🍂\n心里的眼泪😢\n模糊了视线🌫️\n**{name}**已快看不见🚶‍♂️",
"糖果罐里好多颜色🍬\n微笑却不甜了😞\n**{name}**的某些快乐😄\n在没有我的时刻⏳",
"中古世纪的城市里🏰\n我想就走到这🚶‍♂️\n海鸥不再眷恋大海🌊\n可以飞更远🕊️",
"远方传来风笛🎶\n我只在意有**{name}**的消息💌\n城堡为爱守着秘密🏰\n而我为**{name}**守着回忆🔒",
"明明就不习惯牵手🚶‍♂️\n为何却主动把手勾🤝\n**{name}**的心事太多🤐\n我不会戳破🚫",
            ],
            "date": 0,
        }
        self.api = f"https://raw.githubusercontent.com/cc63/PagerMaid-Pyro/main/Jay/Jay.json"

    async def fetch(self):
        try:
            req = await request.get(self.api, follow_redirects=True)
            assert req.status_code == 200
            self.data = req.json()
        except Exception as e:
            await log(f"Warning: plugin fadian failed to refresh data. {e}")


fa_dian = FaDian()


@Hook.on_startup()
async def init_data():
    await fa_dian.fetch()


@scheduler.scheduled_job("cron", hour="2", id="plugins.fa_dian.refresh")
async def fa_dian_refresher_data():
    await fa_dian.fetch()


@listener(command="jay", description="快速对着某人哼唱周杰伦", parameters="[query]")
async def fa_dian_process(message: Message):
    if fa_dian.data.get("date") == 0:
        await fa_dian.fetch()
    if not (query := message.arguments):
        if user := message.from_user:
            query = "死号" if user.is_deleted else user.first_name
        elif channel := message.sender_chat:
            query = channel.title
        else:
            return await message.edit("请指定哼唱对象")
    if not query:
        return await message.edit("请指定哼唱对象")
    if data := fa_dian.data.get("data"):
        return await message.edit(choice(data).format(name=query))
    else:
        return await message.edit("哼唱数据为空")

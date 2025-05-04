import time
import re
import asyncio
from json.decoder import JSONDecodeError
from datetime import datetime
from zoneinfo import ZoneInfo
from pagermaid.utils import alias_command, execute
from pagermaid.enums import Message
from pagermaid.services import client, scheduler
from pagermaid.hook import Hook
from pagermaid.listener import listener
from pagermaid.config import Config
from pagermaid.utils.bot_utils import log


class Rate:
    def __init__(self, app_ids: list, base: str = "USD", cache_duration: int = 7200):
        # app_ids: 从 openexchangerates 获取的多个 app_id 列表
        # base: 基准币种（OpenExchangeRates默认是USD）
        # cache_duration: 缓存持续时间（秒），默认两小时7200秒
        self.app_ids = app_ids
        self.current_api_index = 0  # 当前使用的API索引
        self.base = base
        self.cache_duration = cache_duration
        
        self.lang_rate = {
            "des": "汇率转换工具",
            "arg": "[from_] [to_] [NUM]",
            "help": "**汇率转换工具**\n\n"
            f"使用示例: `,{alias_command('rate')} usd cny 37.95*12` \n",
            "nc": "不是支持的货币。\n\n**支持货币:** \n",
            "notice": "数据来源: Open Exchange Rates \n\n⌛️ 数据每两小时更新一次",
            "warning": "⌛️ 数据每两小时更新一次",
            "error": "❌ **错误:**",
            "calc_error": "❌ **计算错误:**",
            "api_error": "⚠️ **无法获取汇率数据，请稍后重试。**",
            "cache_cleared": "🧹 **缓存已清除，下次查询将获取最新数据。**"
        }
        
        self.api_base_url = "https://openexchangerates.org/api/latest.json?app_id="
        self.last_update = 0
        self.rates = {}
        self.currencies = []
        self.currencies_set = set()  # 用于快速查找的集合
        self.data_timestamp = 0  # 原始时间戳
        self.tz = ZoneInfo("Asia/Shanghai")  # 使用上海时区
        self.failed_apis = set()  # 记录失败的API
        self.backoff_times = {}  # 记录每个API的下次尝试时间
        self.request_timeout = 10  # API请求超时时间（秒）
        
        # Currency symbols mapping
        self.currency_symbols = {
            "AED": "د.إ", "AFN": "؋", "ALL": "Lek", "AMD": "֏", "ANG": "ƒ",
            "AOA": "Kz", "ARS": "$", "AUD": "A$", "AWG": "ƒ", "AZN": "₼",
            "BAM": "KM", "BBD": "$", "BDT": "৳", "BGN": "лв", "BHD": ".د.ب",
            "BIF": "FBu", "BMD": "$", "BND": "$", "BOB": "Bs.", "BRL": "R$",
            "BSD": "$", "BTC": "₿", "BTN": "Nu.", "BWP": "P", "BYN": "Br",
            "BZD": "BZ$", "CAD": "C$", "CDF": "FC", "CHF": "SFr.", "CLF": "UF",
            "CLP": "$", "CNH": "¥", "CNY": "¥", "COP": "$", "CRC": "₡",
            "CUC": "$", "CUP": "$", "CVE": "$", "CZK": "Kč", "DJF": "Fdj",
            "DKK": "kr", "DOP": "RD$", "DZD": "دج", "EGP": "£", "ERN": "Nfk",
            "ETB": "Br", "EUR": "€", "FJD": "$", "FKP": "£", "GBP": "£",
            "GEL": "₾", "GGP": "£", "GHS": "₵", "GIP": "£", "GMD": "D",
            "GNF": "FG", "GTQ": "Q", "GYD": "$", "HKD": "HK$", "HNL": "L",
            "HRK": "kn", "HTG": "G", "HUF": "Ft", "IDR": "Rp", "ILS": "₪",
            "IMP": "£", "INR": "₹", "IQD": "ع.د", "IRR": "﷼", "ISK": "kr",
            "JEP": "£", "JMD": "J$", "JOD": "د.ا", "JPY": "¥", "KES": "KSh",
            "KGS": "сом", "KHR": "៛", "KMF": "CF", "KPW": "₩", "KRW": "₩",
            "KWD": "د.ك", "KYD": "$", "KZT": "₸", "LAK": "₭", "LBP": "ل.ل",
            "LKR": "Rs", "LRD": "$", "LSL": "L", "LYD": "ل.د", "MAD": "د.م.",
            "MDL": "L", "MGA": "Ar", "MKD": "ден", "MMK": "Ks", "MNT": "₮",
            "MOP": "MOP$", "MRU": "UM", "MUR": "₨", "MVR": "Rf", "MWK": "MK",
            "MXN": "$", "MYR": "RM", "MZN": "MT", "NAD": "$", "NGN": "₦",
            "NIO": "C$", "NOK": "kr", "NPR": "₨", "NZD": "NZ$", "OMR": "ر.ع.",
            "PAB": "B/.", "PEN": "S/", "PGK": "K", "PHP": "₱", "PKR": "₨",
            "PLN": "zł", "PYG": "₲", "QAR": "ر.ق", "RON": "L", "RSD": "дин",
            "RUB": "₽", "RWF": "FRw", "SAR": "ر.س", "SBD": "$", "SCR": "₨",
            "SDG": "ج.س.", "SEK": "kr", "SGD": "S$", "SHP": "£", "SLL": "Le",
            "SOS": "S", "SRD": "$", "SSP": "£", "STD": "Db", "STN": "Db",
            "SVC": "₡", "SYP": "£", "SZL": "E", "THB": "฿", "TJS": "ЅМ",
            "TMT": "m", "TND": "د.ت", "TOP": "T$", "TRY": "₺", "TTD": "$",
            "TWD": "NT$", "TZS": "TSh", "UAH": "₴", "UGX": "USh", "USD": "$",
            "UYU": "$", "UZS": "сўм", "VES": "Bs.", "VND": "₫", "VUV": "VT",
            "WST": "T", "XAF": "FCFA", "XAG": "Ag", "XAU": "Au", "XCD": "$",
            "XDR": "SDR", "XOF": "CFA", "XPD": "Pd", "XPF": "₣", "XPT": "Pt",
            "YER": "﷼", "ZAR": "R", "ZMW": "ZK", "ZWL": "Z$"
        }
        
    def is_cache_valid(self):
        """检查缓存是否仍然有效"""
        return time.time() - self.last_update < self.cache_duration and self.rates
        
    def _get_next_api_id(self):
        """获取下一个可用的API ID，考虑失败历史和退避时间"""
        current_time = time.time()
        
        # 先轮换到下一个API
        self._rotate_api()
        
        # 从当前位置开始尝试找到一个可用的API
        original_index = self.current_api_index
        while True:
            api_id = self.app_ids[self.current_api_index]
            
            # 检查API是否在退避时间内
            if api_id in self.backoff_times and current_time < self.backoff_times[api_id]:
                # 这个API还在退避时间内，移动到下一个
                pass
            # 如果这个API没有失败记录，就使用它
            elif api_id not in self.failed_apis:
                return api_id
            
            # 移动到下一个API
            self.current_api_index = (self.current_api_index + 1) % len(self.app_ids)
            
            # 如果已经检查了所有API，清空失败记录并重试
            if self.current_api_index == original_index:
                # 所有API都不可用，重置失败记录并返回一个
                self.failed_apis.clear()
                self.backoff_times.clear()
                return api_id
            
    def _rotate_api(self):
        """轮换到下一个API"""
        self.current_api_index = (self.current_api_index + 1) % len(self.app_ids)
        
    def _mark_api_failed(self, api_id):
        """标记API失败并设置退避时间"""
        self.failed_apis.add(api_id)
        
        # 设置指数退避
        backoff_time = 60  # 初始退避1分钟
        if api_id in self.backoff_times:
            # 已经失败过，增加退避时间，最多到30分钟
            backoff_time = min(1800, self.backoff_times.get(api_id, 60) * 2)
            
        self.backoff_times[api_id] = time.time() + backoff_time
        
    async def get_data(self, force: bool = False):
        """获取汇率数据，当force为False时使用缓存"""
        try:
            # 当force为False时，如果数据仍在缓存时间内，则不重复获取
            if not force and self.is_cache_valid():
                return
            
            current_time = time.time()
            
            # 尝试所有API直到成功
            for _ in range(len(self.app_ids)):
                api_id = self._get_next_api_id()
                api_url = f"{self.api_base_url}{api_id}"
                
                try:
                    # 添加超时参数
                    req = await client.get(api_url, follow_redirects=True, timeout=self.request_timeout)
                    assert req.status_code == 200
                    data = req.json()
                    self.rates = data.get("rates", {})
                    self.data_timestamp = data.get("timestamp", 0)
                    self.currencies = sorted(list(self.rates.keys()))
                    self.currencies_set = set(self.currencies)  # 更新集合以加速查询
                    self.last_update = current_time
                    
                    # 成功获取数据，从失败列表中移除此API（如果存在）
                    self.failed_apis.discard(api_id)
                    if api_id in self.backoff_times:
                        del self.backoff_times[api_id]
                    return
                except (JSONDecodeError, AssertionError, asyncio.TimeoutError) as e:
                    # 记录失败的API并应用退避策略
                    self._mark_api_failed(api_id)
                    await log(f"⚠️ 警告: API {api_id} 获取汇率数据失败。{e}")
                    
            # 如果所有API都失败了，记录错误
            await log("❌ 严重错误: 所有API都无法获取汇率数据。")
        except Exception as e:
            # 捕获所有可能的异常，确保函数不会完全崩溃
            await log(f"❌ 严重错误: 获取汇率数据时发生未预期的错误: {e}")
    
    def is_currency(self, value: str) -> bool:
        """检查值是否为有效货币代码，优化版本"""
        if not value or len(value) != 3 or not value.isalpha():
            return False
        return value.upper() in self.currencies_set
    
    def get_symbol(self, currency_code: str) -> str:
        """获取货币符号"""
        return self.currency_symbols.get(currency_code.upper(), "")
    
    def convert_rate(self, from_: str, to_: str, amount: float):
        """转换货币汇率，带错误处理"""
        try:
            from_ = from_.upper()
            to_ = to_.upper()
            if from_ not in self.rates or to_ not in self.rates:
                return None
            
            from_rate = self.rates[from_]
            to_rate = self.rates[to_]
            
            # 防止除零错误
            if from_rate == 0:
                return None
                
            result = amount * (to_rate / from_rate)
            return round(result, 4)
        except (KeyError, ZeroDivisionError, TypeError) as e:
            # 记录错误并返回None
            return None
    
    def format_timestamp(self):
        """将时间戳格式化为上海时间"""
        if not self.data_timestamp:
            return ""
        dt = datetime.fromtimestamp(self.data_timestamp, self.tz)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    async def get_rate(self, from_: str, to_: str, amount: float, expression: str = None):
        """获取并格式化汇率信息"""
        # 在获取汇率前确保数据是最新的(或仍在缓存有效期内)
        await self.get_data()
        res = self.convert_rate(from_, to_, amount)
        if res is None:
            return f"❌ 无法转换 {from_} 到 {to_}"
        
        date_str = self.format_timestamp()
        symbol_from = self.get_symbol(from_)
        symbol_to = self.get_symbol(to_)
        
        # 如果有表达式，计算并显示
        evaluated_str = ""
        if expression:
            evaluated_str = f"`金额计算: {expression} = {amount}`\n"
            
        # 显示数据来源和本地化的更新时间
        return (
            f"**{from_}** ➜ **{to_}**\n\n"
            f"`{symbol_from}{amount:.2f} = {symbol_to}{res:.2f}`\n\n"
            f"{evaluated_str}"
            f"`更新时间: {date_str}`"
        )
    
    def clear_cache(self):
        """清除缓存数据"""
        self.last_update = 0
        self.rates = {}
        self.currencies = []
        self.currencies_set = set()
        self.data_timestamp = 0
        self.failed_apis.clear()  # 同时清除失败的API记录
        self.backoff_times.clear()  # 清除退避时间
        
    async def calculate_expression(self, expr_str):
        """计算表达式并返回结果"""
        try:
            if re.fullmatch(r'^\d+(\.\d+)?$', expr_str):
                # 纯数字，直接转换
                return float(expr_str), None
            else:
                # 使用bc计算表达式
                cmd = f'echo "scale=4;{expr_str}" | bc'
                result = await execute(cmd)
                return float(result.strip()), expr_str
        except Exception as e:
            return None, str(e)


# 初始化带有多个API key的Rate实例
rate_data = Rate(
    app_ids=[
        "🔴这里填写app_id 1",
        "🔴这里填写app_id 2"
    ],
    cache_duration=7200  # 两小时 = 7200秒
)


@Hook.on_startup()
async def init_rate():
    """启动时初始化汇率数据"""
    try:
        await rate_data.get_data(force=True)
    except Exception as e:
        await log(f"⚠️ 启动时获取汇率数据失败: {e}")
    
    
@scheduler.scheduled_job("cron", hour="*/2", minute="8", id="refresher_rate")
async def refresher_rate():
    """定时刷新汇率数据，每2小时执行一次"""
    try:
        # 强制刷新数据
        await rate_data.get_data(force=True)
        await log("✅ 汇率数据已定时更新")
    except Exception as e:
        await log(f"⚠️ 定时更新汇率数据失败: {e}")


# 拆分逻辑为更小的函数
async def handle_rate_command(message, params):
    """处理汇率命令的主要逻辑"""
    # 默认值
    from_ = "USD"
    to_ = "CNY"
    amount = 100.0
    expression = None
    
    try:
        # 根据参数数量处理不同情况
        if len(params) == 1:
            from_ = params[0].upper().strip()
            
        elif len(params) == 2:
            from_ = params[0].upper().strip()
            to_or_expr = params[1].strip()
            
            if rate_data.is_currency(to_or_expr):
                to_ = to_or_expr.upper()
            else:
                # 第二个参数是金额或表达式
                amount, expression = await rate_data.calculate_expression(to_or_expr)
                if amount is None:
                    return f"{rate_data.lang_rate['calc_error']} {expression}"
                
        elif len(params) == 3:
            from_ = params[0].upper().strip()
            to_ = params[1].upper().strip()
            
            # 先检查目标货币是否合法
            if not rate_data.is_currency(to_):
                return f"❌ `{to_}` {rate_data.lang_rate['nc']}`{', '.join(rate_data.currencies)}`"
            
            # 处理第三个参数(金额/表达式)
            amount, expression = await rate_data.calculate_expression(params[2].strip())
            if amount is None:
                return f"{rate_data.lang_rate['calc_error']} {expression}"
        else:
            # 参数不符合要求，显示帮助
            return f"{rate_data.lang_rate['help']}\n\n{rate_data.lang_rate['notice']}"
        
        # 检查币种是否合法
        if not rate_data.is_currency(from_):
            return f"❌ `{from_}` {rate_data.lang_rate['nc']}`{', '.join(rate_data.currencies)}`"
        
        # 执行转换
        return await rate_data.get_rate(from_, to_, amount, expression=expression)
    except Exception as e:
        return f"{rate_data.lang_rate['error']} {e}"


@listener(
    command="rate",
    description=rate_data.lang_rate["des"],
    parameters=rate_data.lang_rate["arg"],
)
async def rate(message: Message):
    """汇率命令入口点"""
    global rate_data
    
    try:
        # 增加清除缓存的命令: rate cc
        if message.arguments and message.arguments.strip().lower() == "cc":
            rate_data.clear_cache()
            await message.edit(rate_data.lang_rate["cache_cleared"])
            return
        
        # 确保数据存在
        if not rate_data.rates:
            await rate_data.get_data(force=True)
            
        if not rate_data.rates:
            await message.edit(rate_data.lang_rate["api_error"])
            return
        
        # 如果没有参数则显示帮助
        if not message.arguments:
            await message.edit(
                f"{rate_data.lang_rate['help']}\n"
                f"{rate_data.lang_rate['notice']}"
            )
            return
        
        # 处理命令
        result = await handle_rate_command(message, message.parameter)
        await message.edit(result)
        
    except Exception as e:
        # 捕获所有异常，确保命令不会崩溃
        await message.edit(f"{rate_data.lang_rate['error']} {e}")
        await log(f"❌ 汇率命令执行失败: {e}")

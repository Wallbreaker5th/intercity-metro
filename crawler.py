import requests
import json
import time
from fnmatch import fnmatchcase


def getjson(url):
    r = requests.get(url)
    r.encoding = "utf-8"
    return json.loads(r.text)


"""
{
    "x号线":{
        "stations":{
            "xx站" : { (空，未来可能有过往站名等信息) }
        },
        "color":"xxxxxx"
    } 
}
"""


def getlines(data):
    lines = {}
    for i in data["l"]:
        if not i["kn"] in lines:
            lines[i["kn"]] = {"stations": {}, "color": i["cl"]}
        for j in i["st"]:
            lines[i["kn"]]["stations"][j["n"]] = {}
    return lines


def is_kana(ch):
    # 平假名、片假名（含 ヶ、长音符ー、中点・）、半角片假名
    return (
        "\u3040" <= ch <= "\u309f"
        or "\u30a0" <= ch <= "\u30ff"
        or "\uff66" <= ch <= "\uff9f"
    )


# 日文汉字 -> 简体中文汉字 对照表（只收录与简体中文写法不同的字，
# 与简体中文相同的字（如 学、国、体、会、恋、浅、狭 等）无需收录；
# 无对应汉字的日本国字（込、喰、笹、畑、糀、狛 等）按中文惯例保留原字）
JP2SC = {
    "両": "两", "亀": "龟", "仏": "佛", "伝": "传", "倉": "仓", "備": "备",
    "東": "东", "岡": "冈", "師": "师", "篠": "筱", "円": "圆", "勝": "胜",
    "動": "动", "園": "园", "宮": "宫", "塚": "冢",
    "増": "增", "島": "岛", "嶽": "岳", "庁": "厅", "広": "广", "庫": "库",
    "後": "后", "徳": "德", "恵": "惠", "戸": "户", "拝": "拜", "栄": "荣",
    "桜": "樱", "楽": "乐", "橋": "桥", "歳": "岁", "沢": "泽", "浜": "滨",
    "淵": "渊", "渋": "涩", "湯": "汤", "滝": "泷", "濃": "浓", "瀬": "濑",
    "氷": "冰", "烏": "乌", "無": "无", "窪": "洼", "競": "竞", "築": "筑",
    "経": "经", "給": "给", "綾": "绫", "緑": "绿", "練": "练", "線": "线",
    "習": "习", "聖": "圣", "臨": "临", "芸": "艺", "舎": "舍", "蓮": "莲",
    "蔵": "藏", "薬": "药", "見": "见", "親": "亲", "調": "调", "議": "议",
    "護": "护", "豊": "丰", "賀": "贺", "蹟": "迹", "車": "车", "軍": "军",
    "軒": "轩", "輪": "轮", "辺": "边", "遊": "游", "郷": "乡", "鉄": "铁",
    "銀": "银", "錦": "锦", "鐘": "钟", "長": "长", "門": "门", "間": "间",
    "関": "关", "陰": "阴", "陽": "阳", "際": "际", "雑": "杂", "雲": "云",
    "電": "电", "霊": "灵", "領": "领", "頭": "头", "願": "愿", "飛": "飞",
    "飯": "饭", "館": "馆", "馬": "马", "駄": "驮", "駅": "站", "駒": "驹",
    "鮫": "鲛", "鳥": "鸟", "鳩": "鸠", "鴨": "鸭", "鵜": "鹈", "鶯": "莺",
    "鶴": "鹤", "鷹": "鹰", "鷺": "鹭", "黒": "黑", "巣": "巢", "稲": "稻",
    "葉": "叶", "場": "场",
    # 以下为本数据集中未出现、但常见且转换无歧义的字，以防数据更新
    "読": "读", "売": "卖", "実": "实", "変": "变", "専": "专", "図": "图",
    "価": "价", "気": "气", "産": "产", "満": "满", "悪": "恶", "応": "应",
    "帰": "归", "県": "县", "歴": "历", "環": "环", "険": "险", "験": "验",
    "剣": "剑", "業": "业", "極": "极", "様": "样", "斎": "斋", "並": "并",
    "龍": "龙", "竜": "龙", "呉": "吴", "圏": "圈", "鶏": "鸡", "亜": "亚",
    "塁": "垒", "壊": "坏",
}

# 各类括号统一转换为中文圆括号（保留括号内的内容）
BRACKET_OPEN = "（(〈《「『【〔"
BRACKET_CLOSE = "）)〉》」』】〕"

# 全角数字 -> 半角
FW2HW = {chr(0xFF10 + i): str(i) for i in range(10)}

# 假名词汇 -> 中文对照表，分两类：
# 1) 种类词：设施/交通等类别词（如 センター=中心、ターミナル=航站楼、エアポート=机场）；
# 2) 有固定汉字写法或固定中文译名的假名地名（如 みなみ=南、スカイツリー=晴空塔，
#    译名参考中文维基百科：東あずま=东吾嬬、東京テレポート=东京电讯 等）。
# 未收录的假名中，属格助词 ノ/の 按惯例译为“之”，其余（ヶ/ケ/ツ/が、敬称前缀 お 等）直接去掉。
KANA2SC = {
    # 种类词
    "センター": "中心",
    "ターミナル": "航站楼",
    "ビル": "大楼",
    "エアポート": "机场",
    "シーサイド": "海滨",
    "テレポート": "电讯",
    "テレコムセンター": "电信中心",
    "ゲートウェイ": "门户",
    "スカイツリー": "晴空塔",
    "アイル": "岛",
    "ふ頭": "埠头",
    "テニス": "网球",
    "ランド": "乐园",
    "スクエア": "广场",
    "タウン": "新城",
    "パーク": "公园",
    # 有固定写法/译名的假名地名
    "とうきょう": "东京",
    "よみうり": "读卖",
    "みなみ": "南",
    "ときわ": "常盘",
    "ひばり": "云雀",
    "つつじ": "杜鹃",
    "めじろ": "目白",
    "つくし": "土笔",
    "すずかけ": "铃悬",
    "あずま": "吾嬬",
    "どき": "哄",  # 勝どき＝勝鬨
}
KANA2SC_KEYS = sorted(KANA2SC, key=len, reverse=True)


def process_station_name(name):
    # 括号统一为中文圆括号
    name = "".join(
        "（" if c in BRACKET_OPEN else "）" if c in BRACKET_CLOSE else c
        for c in name
    )
    result = []
    i = 0
    while i < len(name):
        # 先做假名词汇最长匹配（种类词等译为中文，键也可能包含汉字如“ふ頭”）
        for key in KANA2SC_KEYS:
            if name.startswith(key, i):
                result.append(KANA2SC[key])
                i += len(key)
                break
        else:
            ch = name[i]
            if ch == "・":  # 日文中点转换为中文间隔号
                result.append("·")
            elif is_kana(ch):
                if ch in ("ノ", "の"):
                    # 属格助词按中文惯例译为“之”（如 井の頭=井之头、御茶ノ水=御茶之水）
                    result.append("之")
                # 其余未收录假名（助词 ヶ/ケ/ツ/が、敬称前缀 お 等）去掉
                pass
            elif ch == "々":  # 叠字符号重复前一个汉字，如“代々木”->“代代木”
                if result and result[-1] not in "（）·":
                    result.append(result[-1])
            else:
                result.append(FW2HW.get(ch, JP2SC.get(ch, ch)))
            i += 1
    converted = "".join(result)
    # 纯假名站名去掉假名后为空时保留原名
    return converted if converted else name


# 东京线路颜色来自 railmapgen/rmg-palette 的东京调色板。
# 注意：调色板中 colour 带“#”前缀，而 metro.json 中颜色不带（前端展示时自动补上）
RMG_PALETTE_URL = (
    "https://github.com/railmapgen/rmg-palette/raw/main"
    "/public/resources/palettes/tokyo.json"
)

# 与调色板条目名称形式不同、无法自动对齐的线路，映射到调色板条目 id。
# 使用 fnmatch 通配符（* 匹配任意字符串），按顺序取首个命中；
# 规则在自动匹配（line_name_variants）之后应用，只兜底自动匹配不到的线路，
# 因此支线通配符（如“京王*線”）不会误伤可精确命中的线路（如 京王井の頭線）。
PALETTE_OVERRIDE = [
    # 与调色板条目名称形式不同的线路
    ("JR常磐線(上野～取手)", "jl"),  # 常磐線各駅停車
    ("小田急*線", "oh"),  # rmg 统称“小田急線”
    ("西武拝島線", "ss"),  # rmg 并入“西武新宿線・拝島線”（组件名不带“西武”前缀）
    ("都電荒川線", "sa"),  # 東京さくらトラム（都電荒川線）
    ("*日暮里・舎人ライナー", "nt"),
    ("*つくばエクスプレス", "tx"),
    ("ゆりかもめ*", "u"),  # 新交通ゆりかもめ
    ("*りんかい線", "r"),
    ("北総鉄道*", "hs"),
    # rmg 未收录的支线，沿用所属本线的颜色
    ("JR成田エクスプレス", "jo"),  # 特急服务，经由横须贺・总武快速通道
    ("東武*線", "ti"),  # 伊势崎线系支线（亀戸線・大師線）
    ("西武有楽町線", "si"),  # 池袋线系支线
    ("西武豊島線", "si"),
    ("西武西武園線", "ss"),  # 新宿线系支线
    ("京成*線", "ks"),  # 京成本线系支线（押上線・金町線）
    ("京王*線", "ko"),  # 京王线系支线（相模原・高尾・競馬場・動物園・新線）
    ("京急*線", "kk"),  # 京急本线系支线（空港線）
]


def build_palette_index(palette):
    """调色板 -> ({条目id: 颜色}, {日文线路名: 条目id})，合并条目按・拆分"""
    id2color, name2id = {}, {}
    for p in palette:
        id2color[p["id"]] = p["colour"].lstrip("#")
        for name in p["name"]["ja"].split("・"):
            name2id.setdefault(name, p["id"])
    return id2color, name2id


def drop_bracket_sections(s):
    """去掉括号及其中的内容（区间限定等），如 東海道本線(東京～熱海)->東海道本線"""
    result, depth = [], 0
    for c in s:
        if c in BRACKET_OPEN:
            depth += 1
            continue
        if c in BRACKET_CLOSE:
            depth -= 1
            continue
        if depth == 0:
            result.append(c)
    return "".join(result)


def line_name_variants(name):
    """生成与调色板线路名对齐的候选形式，按优先级排列"""
    variants = [name]
    if name.startswith("JR"):
        name = name[2:]
        variants.append(name)
    # 去掉括号字符但保留内容：中央線(快速)->中央線快速
    for v in (
        "".join(c for c in name if c not in BRACKET_OPEN + BRACKET_CLOSE),
        drop_bracket_sections(name),
    ):
        if v and v not in variants:
            variants.append(v)
    # 東武東上本線 -> 東武東上線、東海道本線 -> 東海道線
    for v in list(variants):
        if v.endswith("本線"):
            w = v[:-2] + "線"
            if w not in variants:
                variants.append(w)
    # 调色板中东京地下铁/都营线路不带公司前缀
    for pre in ("東京メトロ", "都営地下鉄"):
        if name.startswith(pre) and name[len(pre):] not in variants:
            variants.append(name[len(pre):])
    # “中央・総武線”类并列名拆分（前半补“線”）
    if "・" in name:
        for v in name.split("・"):
            v = v if v.endswith(("線", "ライン")) else v + "線"
            if v not in variants:
                variants.append(v)
    return variants


def find_line_color(name, id2color, name2id):
    """在调色板中查找线路颜色：先按名称变体精确匹配（结果更准确，
    如 京成成田空港線 有独立条目），失败后再按通配符规则兜底
    （支线沿用本线色），仍找不到返回占位色 ff00ff"""
    for v in line_name_variants(name):
        if v in name2id:
            return id2color[name2id[v]]
    for pattern, pid in PALETTE_OVERRIDE:
        if fnmatchcase(name, pattern):
            return id2color[pid]
    return "ff00ff"


def gettokyo():
    # 东京轨道交通数据来自 https://github.com/piuccio 的日本铁道开放数据
    # 线路：prefectures 数组中包含 "13"（东京都）
    # 车站通过 ekidata_line_id 与线路的 ekidata_id 对应
    stations = getjson(
        "https://raw.githubusercontent.com/piuccio/open-data-jp-railway-stations/master/stations.json"
    )
    time.sleep(1)
    lines = getjson(
        "https://raw.githubusercontent.com/piuccio/open-data-jp-railway-lines/master/lines.json"
    )
    time.sleep(1)
    palette = getjson(RMG_PALETTE_URL)
    id2color, name2id = build_palette_index(palette)
    result = {}
    id2name = {}
    for i in lines:
        if "13" in i["prefectures"]:
            if not i["name_kanji"] in result:
                # 从 rmg-palette 调色板取色，未收录的线路以 ff00ff 占位
                result[i["name_kanji"]] = {
                    "stations": {},
                    "color": find_line_color(i["name_kanji"], id2color, name2id),
                }
            id2name[i["ekidata_id"]] = i["name_kanji"]
    for i in stations:
        for j in i["stations"]:
            line_name = id2name.get(j["ekidata_line_id"])
            if line_name:
                # 站名去掉假名并转换为简体中文汉字，原名存入 displayName；
                # 线路名称不做处理
                name = process_station_name(j["name_kanji"])
                result[line_name]["stations"][name] = {
                    "displayName": j["name_kanji"]
                }
    return result


def fix(city, line, wrong_name, correct_name):
    try:
        data[city][line]["stations"][correct_name] = data[city][line]["stations"].pop(
            wrong_name
        )
        print(f"将{city}{line}的“{wrong_name}”修正为“{correct_name}”")
    except KeyError:
        print(f"找不到{city}{line}下的“{wrong_name}”")

def virt_link(station1, station2):
    if "virtual_links" not in data or data["virtual_links"] is None:
        data["virtual_links"] = []
    data["virtual_links"].append([station1, station2])
    print(f"已创建虚拟链接，连接站点 {station1} 和 {station2}")


cities = [
    {"name": "北京", "id": "1100", "name_en": "beijing"},
    {"name": "长春", "id": "2201", "name_en": "changchun"},
    {"name": "长沙", "id": "4301", "name_en": "changsha"},
    {"name": "常州", "id": "3204", "name_en": "changzhou"},
    {"name": "成都", "id": "5101", "name_en": "chengdu"},
    {"name": "重庆", "id": "5000", "name_en": "chongqing"},
    {"name": "大连", "id": "2102", "name_en": "dalian"},
    {"name": "东莞", "id": "4419", "name_en": "dongguan"},
    {"name": "佛山", "id": "4406", "name_en": "foshan"},
    {"name": "福州", "id": "3501", "name_en": "fuzhou"},
    {"name": "贵阳", "id": "5201", "name_en": "guiyang"},
    {"name": "广州", "id": "4401", "name_en": "guangzhou"},
    {"name": "哈尔滨", "id": "2301", "name_en": "haerbin"},
    {"name": "合肥", "id": "3401", "name_en": "hefei"},
    {"name": "呼和浩特", "id": "1501", "name_en": "huhehaote"},
    {"name": "杭州", "id": "3301", "name_en": "hangzhou"},
    {"name": "济南", "id": "3701", "name_en": "jinan"},
    {"name": "昆明", "id": "5301", "name_en": "kunming"},
    {"name": "兰州", "id": "6201", "name_en": "lanzhou"},
    {"name": "洛阳", "id": "4103", "name_en": "luoyang"},
    {"name": "宁波", "id": "3302", "name_en": "ningbo"},
    {"name": "南昌", "id": "3601", "name_en": "nanchang"},
    {"name": "南京", "id": "3201", "name_en": "nanjing"},
    {"name": "南宁", "id": "4501", "name_en": "nanning"},
    {"name": "青岛", "id": "3702", "name_en": "qingdao"},
    {"name": "上海", "id": "3100", "name_en": "shanghai"},
    {"name": "石家庄", "id": "1301", "name_en": "shijiazhuang"},
    {"name": "沈阳", "id": "2101", "name_en": "shenyang"},
    {"name": "深圳", "id": "4403", "name_en": "shenzhen"},
    {"name": "苏州", "id": "3205", "name_en": "suzhou"},
    {"name": "太原", "id": "1401", "name_en": "taiyuan"},
    {"name": "天津", "id": "1200", "name_en": "tianjin"},
    {"name": "武汉", "id": "4201", "name_en": "wuhan"},
    {"name": "乌鲁木齐", "id": "6501", "name_en": "wulumuqi"},
    {"name": "无锡", "id": "3202", "name_en": "wuxi"},
    {"name": "西安", "id": "6101", "name_en": "xian"},
    {"name": "厦门", "id": "3502", "name_en": "xiamen"},
    {"name": "徐州", "id": "3203", "name_en": "xuzhou"},
    {"name": "郑州", "id": "4101", "name_en": "zhengzhou"},
    {"name": "香港", "id": "8100", "name_en": "xianggang"},
    {"name": "澳门", "id": "8200", "name_en": "aomen"},
    {"name": "台北", "id": "7101", "name_en": "taibei"},
    {"name": "高雄", "id": "7102", "name_en": "gaoxiong"},
    {"name": "台中", "id": "7104", "name_en": "taizhong"},
    {"name": "桃园", "id": "7106", "name_en": "taoyuan"},
]

data = {}
for i in cities:
    print(i["name"], i["id"], i["name_en"])
    data[i["name"]] = getlines(
        getjson(
            "http://map.amap.com/service/subway?srhdata=%s_drw_%s.json"
            % (i["id"], i["name_en"])
        )
    )
    time.sleep(1)

print("东京", "", "tokyo")
data["东京"] = gettokyo()

fix("广州", "地铁9号线", "清布", "清㘵")
virt_link("落马洲", "福田口岸")

json.dump(data, open("metro.json", "w", encoding="utf8"), ensure_ascii=False)

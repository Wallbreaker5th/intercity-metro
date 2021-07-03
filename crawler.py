import requests
import json
import time


def getjson(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
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
    for i in data['l']:
        if not i['kn'] in lines:
            lines[i['kn']] = {'stations':{},'color':i['cl']}
        for j in i['st']:
            lines[i['kn']]['stations'][j['n']] = {}
    return lines


cities = [
    {
        "name": "北京",
        "id": "1100",
        "name_en": "beijing"
    }, {
        "name": "长春",
        "id": "2201",
        "name_en": "changchun"
    }, {
        "name": "长沙",
        "id": "4301",
        "name_en": "changsha"
    }, {
        "name": "常州",
        "id": "3204",
        "name_en": "changzhou"
    }, {
        "name": "成都",
        "id": "5101",
        "name_en": "chengdu"
    }, {
        "name": "重庆",
        "id": "5000",
        "name_en": "chongqing"
    }, {
        "name": "大连",
        "id": "2102",
        "name_en": "dalian"
    }, {
        "name": "东莞",
        "id": "4419",
        "name_en": "dongguan"
    }, {
        "name": "佛山",
        "id": "4406",
        "name_en": "foshan"
    }, {
        "name": "福州",
        "id": "3501",
        "name_en": "fuzhou"
    }, {
        "name": "贵阳",
        "id": "5201",
        "name_en": "guiyang"
    }, {
        "name": "广州",
        "id": "4401",
        "name_en": "guangzhou"
    }, {
        "name": "哈尔滨",
        "id": "2301",
        "name_en": "haerbin"
    }, {
        "name": "合肥",
        "id": "3401",
        "name_en": "hefei"
    }, {
        "name": "呼和浩特",
        "id": "1501",
        "name_en": "huhehaote"
    }, {
        "name": "杭州",
        "id": "3301",
        "name_en": "hangzhou"
    }, {
        "name": "济南",
        "id": "3701",
        "name_en": "jinan"
    }, {
        "name": "昆明",
        "id": "5301",
        "name_en": "kunming"
    }, {
        "name": "兰州",
        "id": "6201",
        "name_en": "lanzhou"
    }, {
        "name": "洛阳",
        "id": "4103",
        "name_en": "luoyang"
    }, {
        "name": "宁波",
        "id": "3302",
        "name_en": "ningbo"
    }, {
        "name": "南昌",
        "id": "3601",
        "name_en": "nanchang"
    }, {
        "name": "南京",
        "id": "3201",
        "name_en": "nanjing"
    }, {
        "name": "南宁",
        "id": "4501",
        "name_en": "nanning"
    }, {
        "name": "青岛",
        "id": "3702",
        "name_en": "qingdao"
    }, {
        "name": "上海",
        "id": "3100",
        "name_en": "shanghai"
    }, {
        "name": "石家庄",
        "id": "1301",
        "name_en": "shijiazhuang"
    }, {
        "name": "沈阳",
        "id": "2101",
        "name_en": "shenyang"
    }, {
        "name": "深圳",
        "id": "4403",
        "name_en": "shenzhen"
    }, {
        "name": "苏州",
        "id": "3205",
        "name_en": "suzhou"
    }, {
        "name": "太原",
        "id": "1401",
        "name_en": "taiyuan"
    }, {
        "name": "天津",
        "id": "1200",
        "name_en": "tianjin"
    }, {
        "name": "武汉",
        "id": "4201",
        "name_en": "wuhan"
    }, {
        "name": "乌鲁木齐",
        "id": "6501",
        "name_en": "wulumuqi"
    }, {
        "name": "无锡",
        "id": "3202",
        "name_en": "wuxi"
    }, {
        "name": "西安",
        "id": "6101",
        "name_en": "xian"
    }, {
        "name": "厦门",
        "id": "3502",
        "name_en": "xiamen"
    }, {
        "name": "徐州",
        "id": "3203",
        "name_en": "xuzhou"
    }, {
        "name": "郑州",
        "id": "4101",
        "name_en": "zhengzhou"
    },
]

data = {}
for i in cities:
    print(i['name'],i["id"],i["name_en"])
    data[i['name']] = getlines(getjson(
        "http://map.amap.com/service/subway?srhdata=%s_drw_%s.json" % (i["id"], i["name_en"])))
    time.sleep(1)

json.dump(data,open("metro.json","w",encoding='utf8'),ensure_ascii=False)

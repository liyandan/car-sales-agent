#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author   : liyandan  
# @Date     : 2026-03-07
# @Description: 车况公用数据结构、验证签名、通用数据解析函数等公共部分
import json
import hmac,hashlib,base64
from datetime import datetime  # datetime 此时是类

def validate_clue_id(clue_id):
    """验证clue_id格式"""
    if clue_id == "":
        return True
    if clue_id.isdigit() and len(clue_id) == 9:
        return True
    return False

def validate_tag_id(tag_id):
    """验证tag_id格式"""
    if tag_id == "":
        return True
    if tag_id.isdigit() and len(tag_id) == 4:
        return True
    return False

COLOR_DICT = {
    "1": "黑色", "2": "白色", "3": "银灰色", "4": "深灰色", "5": "咖啡色",
    "6": "红色", "7": "蓝色", "8": "绿色", "9": "黄色", "10": "橙色",
    "11": "香槟色", "12": "紫色", "13": "多彩色", "14": "其他",
}
# 车源基本信息字段
CAR_BASIC_INFO_COLS = [
    "has_shelf",
    "create_time",
    "title",
    "minor_category_name",
    "tag_name",
    "car_id",  # 车型
    "car_year",
    "license_full_date",
    "road_haul",  # 29: 质疑里程  37 ： 里程多影响
    "transfer_num",  # 9:  过户次数和原因
    "fuel_type",
    "car_keys",
    "evaluate_score",
    "evaluate_level",
    "vin_encrypt",
    "attr_carsource_insurance_record_id",  # 出险记录G3订单号
    "emission_standard",  # 11： 排放标准查询
    "attr_carsource_battery_owner_type",  # 3: 是否租用电池
    # "attr_carsource_battery_inspection_health" ,    # 27：电池状态查询：  电池健康度SO H值
    "attr_carsource_battery_inspection_report",  # 27：电池检测报告
    "attr_carsource_battery_inspection_commit_time",  # 27：电池报告检测时间
    "audit_full_date",  # 4 年检
    "strong_insurance_full_date",  # 4 交强险年月日
    "business_insurance_full_date",  # 4 商业险
    "car_owner_type",  # 公户私户
    "car_color",
    # 车身颜色，映射表：1	"黑色";2	"白色";3	"银灰色";4"深灰色";5"咖啡色";6"红色";7"蓝色";8"绿色";9"黄色";10"橙色";11"香槟色";12"紫色";13"多彩色";14"其他"
    "store_id",  # 门店id
    "attr_opl_interior_color",  # 内饰颜色
]

CAR_TYPE_INFO_FIELD_DICT = {
    # "id": "ID",
    # "autohomeId": "汽车之家ID",
    "niankuan": "年款",
    "xiaoshoumingcheng": "销售名称",
    # "zhidaojiage": "指导价格",
    # "changshangId": "厂商ID",
    "changjia": "厂家",
    "pinpai": "品牌",
    "chexi": "车系",
    "cheshenwendingkongzhi": "车身稳定控制",
    "bingxianfuzhu": "并线辅助",
    "chedaojuzhongbaochi": "车道居中保持",
    "chedaopianliyujingxitong": "车道偏离预警系统",
    "zhudongshacheZhudonganquanxitong": "主动刹车主动安全系统",
    "daocheshipinyingxiang": "倒车视频影像",
    "quanjingshexiangtou": "全景摄像头",
    "zidongbocheruwei": "自动泊车入位",
    "dingsuxunhang": "定速巡航",
    "zishiyingxunhang": "自适应巡航",
    "quanjingtianchuang": "全景天窗",
    "wuyaoshiqidongxitong": "无钥匙启动系统",
    "ganyinghoubeixiang": "感应后备箱",
    "duogongnengfangxiangpan": "多功能方向盘",
    "diandongxihemen": "电动吸合门",
    "hudtaitoushuzixianshi": "HUD抬头数字显示",
    "zishiyingyuanjinguang": "自适应远近光",
    "diandongtianchuang": "电动天窗",
    "yundongfenggezuoyi": "运动风格座椅",
    "tianchuangleixing": "天窗类型",
    "xunhangxitong": "巡航系统",
    "chundianxuhanglicheng": "纯电续航里程",
    "wltcchundianxuhanglicheng": "WLTC纯电续航里程",
    "cltczonghexuhang": "CLTC综合续航",
    "pailiang": "排量",
    "zuoweishu": "座位数",
    "qigangshu": "气缸数",
    "cheliangleixing": "车辆类型",
    "nedcchundianxuhanglicheng": "NEDC纯电续航里程",
    "wltpchundianxuhanglicheng": "WLTP纯电续航里程",
    "cltcchundianxuhanglicheng": "CLTC纯电续航里程",
    "epachundianxuhanglicheng": "EPA纯电续航里程",
    "nedczonghexuhang": "NEDC综合续航",
    "wltczonghexuhang": "WLTC综合续航",
    "gongxinbuxuhanglicheng": "工信部续航里程",
    "ranyouleixing": "燃油类型",
    "kuaichongshijian": "快充时间",
    "manchongshijian": "慢充时间",
    "dianchileixing": "电池类型",
    # "dianchileixing_code": "电池类型_代码",
    "zuidamali": "最大马力",
    "kuaichonggongneng": "快充功能",
    # "kuaichonggongneng_code": "快充功能_代码",
    "chang": "长",
    "kuan": "宽",
    "gao": "高",
    "sandianxitongzhibao": "三电系统质保",
    "sandianxitongzhibaolicheng": "三电系统质保里程",
    "sandianxitongzhibaonianxian": "三电系统质保年限",
    "sandianshourenchezhuzhibaozhengce": "三电首任车主质保政策",
    "chexing": "车型",
    "guobie": "国别",
    # "guobie_code": "国别_代码",
    "paifangbiaozhun": "排放标准",
    "cheliangjibie": "车辆级别",
    "qigangrongji": "气缸容积",
    "jinqixingshi": "进气形式",
    "ranyoubiaohao": "燃油标号",
    "zuidagonglv": "最大功率",
    "zuidagonglvzhuansu": "最大功率转速",
    "zuidaniuju": "最大扭矩",
    "zuidaniujuzhuansu": "最大扭矩转速",
    "qigangpailiexingshi": "气缸排列形式",
    "meigangqimenshu": "每缸气门数",
    "yasuobi": "压缩比",
    "gongyoufangshi": "供油方式",
    "gongxinbuzongheyouhao": "工信部综合油耗",
    "jiasushijian": "加速时间",
    "zuigaochesu": "最高车速",
    "biansuqimiaoshu": "变速器描述",
    "biansuxiangleixing": "变速箱类型",
    "dangweishu": "档位数",
    "qianzhidongqileixing": "前制动器类型",
    "houzhidongqileixing": "后制动器类型",
    "qianxuangualeixing": "前悬挂类型",
    "houxuangualeixing": "后悬挂类型",
    "zhulileixing": "助力类型",
    "zuixiaolidijianxi": "最小离地间距",
    "qudongfangshi": "驱动方式",
    # "qudongfangshi_code": "驱动方式_代码",
    "zhouju": "轴距",
    "qianlunju": "前轮距",
    "houlunju": "后轮距",
    "zhengbeizhiliang": "整备质量",
    "youxiangrongji": "油箱容积",
    "xinglixiangrongji": "行李箱容积",
    "chemenshu": "车门数",
    "qianluntaiguige": "前轮胎规格",
    "houluntaiguige": "后轮胎规格",
    "xibuqinang": "膝部气囊",
    "taiyajiancezhuangzhi": "胎压检测装置",
    "lingtaiyajixuxingshi": "零胎压继续行驶",
    "anquandaiweixitishi": "安全带未系提示",
    "isofixertongzuoyijiekou": "ISOFIX儿童座椅接口",
    "fadongjidianzifangdao": "发动机电子防盗",
    "zhongkongsuo": "中控锁",
    "yaokongyaoshi": "遥控钥匙",
    "absfangbaosi": "ABS防抱死",
    "zhidonglifenpei": "制动力分配",
    "chachefuzhu": "刹车辅助",
    "qianyinlikongzhi": "牵引力控制",
    "doupohuanjiang": "陡坡缓降",
    "toumingdipan": "透明底盘",
    "kebianxuangua": "可变悬挂",
    "kongqixuangua": "空气悬挂",
    "kebianzhuanxiangbi": "可变转向比",
    "zhenpifangxiangpan": "真皮方向盘",
    "fangxiangpandiandongdiaojie": "方向盘电动调节",
    "fangxiangpanhuandang": "方向盘换挡",
    "zuoyigaodidiaojie": "座椅高低调节",
    "yaobuzhichengdiaojie": "腰部支撑调节",
    "jianbuzhichengdiaojie": "肩部支撑调节",
    "dierpaikaobeijiaodudiaojie": "第二排靠背角度调节",
    "dierpaizuoyiyidong": "第二排座椅移动",
    "houpaizuoyidiandongdiaojie": "后排座椅电动调节",
    "diandongzuoyijiyi": "电动座椅记忆",
    "zuoyitongfeng": "座椅通风",
    "zuoyianmo": "座椅按摩",
    "houpaibeijia": "后排靠背",
    "cheneifenweideng": "车内氛围灯",
    "houfengdangzheyanglian": "后风挡遮阳帘",
    "houpaicezheyanglian": "后排侧遮阳帘",
    "zheyangbanhuazhuangjing": "遮阳板化妆镜",
    "diandonghoubeixiang": "电动后备箱",
    "yundongwaiguantaojian": "运动外观套件",
    "rijianxingchedeng": "日间行车灯",
    "zidongtoudeng": "自动头灯",
    "zhuanxiangtoudeng": "转向头灯",
    "qianwudeng": "前雾灯",
    "dadenggaodukediao": "大灯高度可调",
    "dadengqingxizhuangzhi": "大灯清洗装置",
    "chechuangfangjiashougongneng": "车窗防夹手功能",
    "houshijingdiandongdiaojie": "后视镜电动调节",
    "houshijingjiare": "后视镜加热",
    "houshijingdiandongzhedie": "后视镜电动折叠",
    "houshijingjiyi": "后视镜记忆",
    "houyushua": "后雨刷",
    "ganyingyushua": "感应雨刷",
    "xingchediannaoxianshiping": "行车电脑显示屏",
    "gpsdaohang": "GPS导航",
    "dingweihudongfuwu": "定位互动服务",
    "zhongkongtaicaisedaping": "中控台彩色大屏",
    "lanyaChezaidianhua": "蓝牙车载电话",
    "chezaidianshi": "车载电视",
    "houpaiyejingping": "后排液晶屏",
    "yangshengqishuliang": "扬声器数量",
    "houpaidulikongdiao": "后排独立空调",
    "houzuochufengkou": "后座出风口",
    "wendufenqukongzhi": "温度分区控制",
    "kongqidiaojieHuafenguolv": "空气调节花粉过滤",
    "chezaibingxiang": "车载冰箱",
    "yeshixitong": "夜视系统",
    "zhongkongyejingpingfenpingxianshi": "中控液晶屏分屏显示",
    "daocheleida": "倒车雷达",
    "qianleida": "前雷达",
    "chetijiegou": "车体结构",
    "qianpaitoubuqinang": "前排头部气囊",
    "houpaitoubuqinang": "后排头部气囊",
    "zhuchezhidongleixing": "驻车制动类型",
    "houpaizuoyifangdaofangshi": "后排座椅放倒方式",
    "qianpaiceqinang": "前排侧气囊",
    "houpaiceqinang": "后排侧气囊",
    "fangziwaixianGereboli": "防紫外线玻璃",
    "houpaiceyinsiboli": "后排侧隐私玻璃",
    "qianHouzhongyangfushou": "前后中央扶手",
    "shicelidijianxi": "实测离地间距",
    "lvhejinlunquan": "铝合金轮圈",
    "ganggaicailiao": "钢盖材料",
    "neiWaihoushijingzidongfangxuanmu": "内外后视镜自动防眩目",
    "cdMp3Wma": "CD/MP3/WMA",
    "zidongzhuche": "自动驻车",
    "qianqiaoxianhuachasuqiChasusuo": "前桥限滑差速器/差速锁",
    "fadongji": "发动机",
    "shangpofuzhu": "上坡辅助",
    "duomeitixitong": "多媒体系统",
    "fadongjiqitingjishu": "发动机启停技术",
    "zhengchezhibao": "整车质保",
    "zhengchezhibaonianxian": "整车质保年限",
    "zhengchezhibaolicheng": "整车质保里程",
    "biansuxiang": "变速箱",
    "jiashizuozuoyidiandongdiaojie": "驾驶座座椅电动调节",
    "fujiashizuozuoyidiandongdiaojie": "副驾驶座座椅电动调节",
    "gangticailiao": "钢体材料",
    "fadongjixinghao": "发动机型号",
    "zhengtizhudongzhuanxiangxitong": "整体主动转向系统",
    "shiceZhidong": "实测制动",
    "fangxiangpandiaojie": "方向盘调节",
    "zhuanxiangfuzhudeng": "转向辅助灯",
    "houqiaoxianhuachasuqiChasusuo": "后桥限滑差速器/差速锁",
    "zuoyicaizhi": "座椅材质",
    "fadongjiteyoujishu": "发动机特有技术",
    "jinguangdeng": "近光灯",
    "jiashizuoanquanqinang": "驾驶座安全气囊",
    "fujiashianquanqinang": "副驾驶安全气囊",
    "fangxiangpanjiare": "方向盘加热",
    "gangjing": "钢径",
    "guanfangJiasu": "官方加速",
    "cheshenxingshi": "车身形式",
    "cehuamen": "侧滑门",
    "shiceyouhao": "实测油耗",
    "qianpaizuoyijiare": "前排座椅加热",
    "houpaizuoyijiare": "后排座椅加热",
    "beitaiguige": "备胎规格",
    "zhongyangchasuqisuozhigongneng": "中央差速器锁止功能",
    "peiqijigou": "配气机构",
    "kongtiaokongzhifangshi": "空调控制方式",
    "yangshengqipinpai": "扬声器品牌",
    "wuyaoshijinruxitong": "无钥匙进入系统",
    "yuanchengqidonggongneng": "远程启动功能",
    "qiandiandongchechuang": "前电动车窗",
    "houdiandongchechuang": "后电动车窗",
    "qudongxingshi": "驱动形式",
    # "qudongxingshi_code": "驱动形式_代码",
    "waijieyinyuanjiekou": "外接音源接口",
    "disanpaizuoyi": "第三排座椅",
    "dianyuan": "电源",
    "quanyejingyibiaopan": "全液晶仪表盘",
    "chedingxinglijia": "车顶行李架",
    "fangxiangpanjiyi": "方向盘记忆",
    "zhongyangchasuqijiegou": "中央差速器结构",
    "yuanguangdeng": "远光灯",
    "dianchizuzhibao": "电池组质保",
    "dianchizuzhibaonianxian": "电池组质保年限",
    "dianchizuzhibaolicheng": "电池组质保里程",
    "dianxinpinpai": "电芯品牌",
    "dianchilengquefangshi": "电池冷却方式",
    "dianchinengliangmidu": "电池能量密度",
    "huoxiangchicun": "货箱尺寸",
    "houpaichemenkaiqifangshi": "后排车门开启方式",
    "dianchichongdianshijian": "电池充电时间",
    "houdiandongjizuidaniuju": "后电动机最大扭矩",
    "qiandiandongjizuidagonglv": "前电动机最大功率",
    "zuidazaizhongzhiliang": "最大载重质量",
    "qiandiandongjizuidaniuju": "前电动机最大扭矩",
    "houdiandongjizuidagonglv": "后电动机最大功率",
    "dianchirongliang": "电池容量",
    "chongdianzhuangjiage": "充电桩价格",
    "diandongjizongmali": "电动机总马力",
    "diandongjizongniuju": "电动机总扭矩",
    "diandongjizonggonglv": "电动机总功率",
    "dianjileixing": "电机类型",
    "xitongzonghegonglv": "系统综合功率",
    "xitongzongheniuju": "系统综合扭矩",
    "baigonglihaodianliang": "百公里耗电量",
    "kuaichongdianliang": "快充电量",
    "bodyColor": "车身颜色",
    "interiorColor": "内饰颜色",
    "guochanhezijinkou": "国产和自进口",
    # "guochanhezijinkou_code": "国产和自进口_代码",
    "disabled": "禁用",
    # "createdAt": "创建时间",
    # "updatedAt": "更新时间",
    "shangshishijian": "上市时间",
    "yijianshengjiang": "一键升降",
    "shoujihulian": "手机互联",
    "chelianwang": "车联网",
    "fujiahoupaitiaojie": "副驾后排调节",
    "qudongdianjishu": "驱动电机数",
    # "qudongdianjishu_code": "驱动电机数_代码",
    "dianjibuju": "电机布局",
    "daochezidongxiafan": "倒车自动下翻",
    "suochezidongzhedie": "锁车自动折叠",
    # "isEnable": "是否启用",
    "zuoyibujv": "座椅布局",
    # "xuanzhuangbao": "选装包",
    "pingxingjinkou": "平行进口",
    "dianchikuaichongdianliangfanwei": "电池快充电量范围",
    "wltczongheyouhuao": "WLTC综合油耗",
    "lunquancaizhi": "轮圈材质",
    "zhongkongpingmuchicun": "中控屏幕尺寸",
    "qianpaizuoyigongneng": "前排座椅功能",
    "dierpaizuoyigongneng": "第二排座椅功能",
    "disanpaizuoyigongneng": "第三排座椅功能",
    "yuyinshibiekongzhixitong": "语音识别控制系统",
    "yincangdiandongmenbashou": "隐藏电动门把手",
    "shoujiwuxianchongdiangongneng": "手机无线充电功能",
    "otashengji": "OTA升级",
    "fuzhujiashidengji": "辅助驾驶等级",
    "fuzhujiashixitong": "辅助驾驶系统",
    # "fuzhujiashixitong_code": "辅助驾驶系统_代码",
    "haomiboleidashuliang": "毫米波雷达数量",
    "shexiangtoushuliang": "摄像头数量",
    "chaoshengboleidashuliang": "超声波雷达数量",
    "qianfangpengzhuangyujing": "前方碰撞预警",
    "houfangpengzhuangyujing": "后方碰撞预警",
    "daochecheceyujingxitong": "倒车车侧预警系统",
    "dowkaimenyujing": "DOW开门预警",
    "daolujiaotongbiaoshishibie": "道路交通标识识别",
    "duiwaifangdian": "对外放电",
    "duiwaijiaofangdiangonglv": "对外交流放电功率",
    "chejizhinengxinpian": "车机智能芯片",
    # "chejizhinengxinpian_code": "车机智能芯片_代码",
    "fuzhujiashixinpian": "辅助驾驶芯片",
    "xinpianzongsuanli": "芯片总算力",
    "fujiayuleping": "副驾雨帘屏",
    "yejingyibiaochicun": "液晶仪表尺寸",
    "shoushikongzhi": "手势控制",
    "kejianjikeshuo": "可见即可说",
    "motanzhinengxuanjia": "模拟智能选驾",
    "pilaojiashitishi": "疲劳驾驶提示",
    "zhongkongcaisepingmu": "中控彩色屏幕",
    "yuyinzhushouhuanxingci": "语音助手唤醒词",
    "shoujiAPPyuanchenggongneng": "手机APP远程功能",
    "chezaizhinengxitong": "车载智能系统",
    "weixingdaohangxitong": "卫星导航系统",
    "daohanglukuangxinxixianshi": "导航路况信息显示",
    "gaoyakuaichong": "高压快充",
    "gaoyapingtai": "高压平台",
    "zhuntuoguachezongzhiliang": "准拖挂车总质量",
    "kuaichongjiekouweizhi": "快充接口位置",
    "chongdianzhan": "充电站",
    "chongdianzhuang": "充电桩",
    "huandianzhan": "换电站",
    "quanguofugaichengshi": "全国覆盖城市",
    "shaobingmoshi": "烧饼模式",
    # "spec_xuanzhuangbao": "选装包",
    "spec_waiguanyanse": "外观颜色",
    "spec_neishiyanse": "内饰颜色",
    # "xuanzhuangpeizhixiang": "选装配置项",
    "new_chexing": "新车型",
    # "brand_id": "品牌ID",
    # "tag_id": "标签ID",
    # "newtag_id": "新标签ID",
    "new_chexi": "新车系",
    "newtag_name": "新标签名称",
    # "brand_english": "品牌英文",
    "brand_chinese": "品牌中文",
    # "tag_url": "标签URL",
    # "tag_pinyin": "标签拼音",
    # "tag_first_char": "标签首字符",
    "tag_guochanhezijinkou": "标签国产和自进口",
    "tagSimpleName": "标签简称",
    # "add_type": "添加类型"
}


CAR_BASIC_INFO_MAP = {
    # "has_shelf": "是否上架",
    # "create_time": "创建时间",
    "title": "车型名称",
    # "minor_category_name": "子类目名称",
    "tag_name": "车系名称",
    # "car_id": "车型ID",
    "car_year": "车款年份",
    "license_full_date": "上牌日期",
    "road_haul": "行驶里程",  # 特殊标注业务含义
    "transfer_num": "过户次数",
    # "fuel_type": "燃油类型",
    "car_keys": "车钥匙数量",
    # "evaluate_score": "评估分数",
    # "evaluate_level": "评估等级",
    # "vin_encrypt": "VIN码密文",
    # "attr_carsource_insurance_record_id": "出险记录订单号",
    # "emission_standard": "排放标准",
    "attr_carsource_battery_owner_type": "电池租用状态",
    # "attr_carsource_battery_inspection_health": "电池健康度",
    # "attr_carsource_battery_inspection_report": "电池检测报告",
    # "attr_carsource_battery_inspection_commit_time": "电池报告检测时间",
    "audit_full_date": "年检到期日",
    "strong_insurance_full_date": "交强险到期日",
    "business_insurance_full_date": "商业险到期日",
    "car_owner_type": "公户私户类型",  # 公户私户
    "car_color": "车身颜色",
    "attr_opl_interior_color": "内饰颜色",
}

BATTERY_REPORT_MAP = {
    "dataUpdateDate": "数据更新日期",
    "manufacturers": "车辆厂家",
    "warrantyPeriod": "整车质保",
    "batterySoh": "电池健康度(SOH)",
    "batterySohLvStr": "电池健康状态等级",
    "referenceEndurance": "当前参考续航(km)",
    "volumeScoreRecessionNarrate": "安全风险水平-解析",
    "batteryHabitAssess": "电池健康检测",
    "totalChargeCount": "总充电次数",
    "totalChargeSoc": "总充电量以循环圈数累计",
    "theoreticalChargeCount": "理论循环次数",
    "fastRatio": "快充占比(%)",
    "fastRatioAssess": "快充效率评估",
    "suspectedAdjust": "是否疑似调表",
    "batteryManufacturer": "电池厂商",
    "batteryType": "电池类型",
    "rateCapacity": "标称电池容量(Ah)",
    "rateMileage": "标称续航里程(km)",
    "nominalEnergy": "系统标称能量(kwh)",
    "dischargingAttention": "车辆充放电模块-注意",
    "dischargingSuggest": "车辆充放电模块-建议",
    "firstChargeDate": "首次充电时间",
    "slowChargeCount": "慢充次数",
    "volumeScoreRecession": "电池衰退速率",
    "firstDrivingDate": "首次行使时间",
    "displayMileage": "当前表显里程",
    "latestChargeDate": "最后一次充电时间",
    "fullChargedDrivingMile": "当前满电续航里程",
    "brand": "品牌",
    "batterylevel": "电池综合评估等级",
    "yearAvgMileage": "年均行驶里程"
}
# 对车型信息进行解析
def car_type_info_parser(car_type_info):
    """车型库配置项解析"""
    car_type_info_parser_result = {}
    for key in car_type_info:
        if key in CAR_TYPE_INFO_FIELD_DICT and car_type_info[key] not in ["", None, "null", "-"]:
            if key == "interiorColor":
                print(f"car type info key: {key},value: {car_type_info[key]}")
            car_type_info_parser_result[CAR_TYPE_INFO_FIELD_DICT[key]] = car_type_info[key]
    return car_type_info_parser_result

# 删除包含'首任车主' 等信息的键值对
def remove_owner_info(data):
    """删除包含'首任车主'的键值对"""
    return {
        key: value
        for key, value in data.items()
        if "首任车主" not in str(value)
    }

# 解析检测报告的缺陷信息
def parse_check_report_defects(content_list: list) -> list:
    """
    解析检测报告缺陷数据

    Args:
        content_list: 原始缺陷数据列表

    Returns:
        list: 解析后的缺陷数据
    """
    result = []

    for category in content_list:
        try:
            # 创建主分类对象，保留key字段
            processed_category = {
                "检测项": category["name"],
                "检测项瑕疵数量": category["defectNum"],
                "历史修复数量": category["repairNum"],
                "middleItemList": []
            }

            # 处理中间分类
            if "middleItemList" in category and category["middleItemList"]:
                for middle_item in category["middleItemList"]:
                    processed_middle = {
                        "检测项": middle_item["name"],
                        "检测项瑕疵数量": middle_item["defectNum"],
                        "历史修复数量": middle_item["repairNum"],
                        "itemList": []
                    }

                    # 处理具体检测项
                    if "itemList" in middle_item and middle_item["itemList"]:
                        for item in middle_item["itemList"]:
                            if "defectList" in item and item["defectList"]:
                                for defect in item["defectList"]:
                                    # 处理缺陷项，即使没有图片也要处理
                                    defect_result = defect.get("firstLevelResult", "") + defect.get("secondLevelResult",
                                                                                                    "") + defect.get(
                                        "thirdLevelResult", "")
                                    processed_item = {
                                        "检测项": item["name"],
                                        "瑕疵名称": defect.get("defectName", ""),
                                        "检测结果": defect_result,
                                    }

                                    # 如果有图片，使用第一张图片的信息
                                    if "imageList" in defect and defect["imageList"] and len(defect["imageList"]) > 0:
                                        first_image = defect["imageList"][0]
                                        image_url_name = item["name"] + "_" + defect.get("defectName", "") + "图片链接"
                                        processed_item[image_url_name] = first_image.get("url", "")

                                    processed_middle["itemList"].append(processed_item)

                    # 添加所有中间分类，不管是否有缺陷项
                    processed_category["middleItemList"].append(processed_middle)

            # 添加所有主分类，不管是否有中间分类
            result.append(processed_category)

        except Exception as e:
            print("处理分类 %s 时出错: %s", category.get('name', 'unknown'), str(e))

    return result


def parse_response_data(response):
    if response.status_code != 200:
        raise Exception(f"response status code 非200：{response.status_code}")
    response_json = response.json()
    code = response_json.get("code")
    if code != 0:
        raise Exception(f"response code 非0：{code}")
    return response_json.get("data")

# ======================= 通用签名函数 =======================

def compute_sign_carsource(params: dict, app_secret: str) -> str:
    """计算车源API签名"""
    from urllib.parse import quote_plus
    tmp_str = '&'.join(key + '=' + quote_plus(str(params[key])) for key in sorted(params))
    sign = hashlib.md5(base64.encodebytes(
        hmac.new(app_secret.encode('utf8'), tmp_str.encode('utf8'), hashlib.sha256).digest()
    ).rstrip()).hexdigest()
    return sign[5:15]

def calc_interval_months(date1_str, date2_str, date_format="%Y-%m-%d"):
    date1 = datetime.strptime(date1_str, date_format)
    date2 = datetime.strptime(date2_str, date_format)
    if date1 > date2:
        date1, date2 = date2, date1
    total_months = (date2.year - date1.year) * 12 + (date2.month - date1.month)
    years = total_months // 12
    months = total_months % 12
    return years, months


def insurance_report_parser(insurance_report):
    """出险记录解析"""
    if not insurance_report:
        return "", "", ""

    car_source_info_content, insurance_report_content = "", ""
    car_source_info = insurance_report["car_source_info"]
    car_source_info_content += "车型年款：" + car_source_info["title"] + "\t" + "车辆颜色：" + car_source_info[
        "car_color"] + "\t" + "排量：" + str(car_source_info["air_displacement"]) + "\t" + "生产日期：" + car_source_info[
                                   "production_date"]

    if (insurance_report["transfer_info_summary"]["transfer_num"] == 0):
        insurance_report_content += "过户次数：" + "\t" + "没转过户"  "\n"
    else:
        insurance_report_content += "过户次数：" + "\t" + str(
            insurance_report["transfer_info_summary"]["transfer_num"]) + "\n"
    plate_date = insurance_report["transfer_info_summary"]["first_time_plate_date"][:10]

    current_date = datetime.now().strftime("%Y-%m-%d")
    car_age_years, car_age_months = calc_interval_months(plate_date, current_date)

    if car_age_years > 0 and car_age_months > 0:
        car_age = f"{car_age_years}年{car_age_months}个月"
    elif car_age_years > 0 and car_age_months == 0:
        car_age = f"{car_age_years}年"
    else:
        car_age = f"{car_age_months}个月"

    insurance_report_content += "车龄：" + str(car_age) + "\n"
    history_insurance_records_result = ""
    for history_insurance_record in insurance_report["history_insurance_records"]:
        history_insurance_record["maintenance_projects"] = history_insurance_record["maintenance_projects"] or ""
        if history_insurance_record["maintenance_projects_dict_mapping"]:
            repair_part = '\t'.join(["维修项目名称：" + item[
                "maintenance_project_name"] + "\t" + "修复部件名称：" + item.get("repair_part_name",
                                                                                item["maintenance_project_name"]) for
                                     item in history_insurance_record["maintenance_projects_dict_mapping"]])
        else:
            repair_part = " "
        history_insurance_records_result += "出险时间：" + history_insurance_record["date"] + "\t" + "出险金额：" + (
            history_insurance_record["insurance_amount"] if history_insurance_record[
                "insurance_amount"] else "") + "\t" + "维修项：" + history_insurance_record[
                                                "maintenance_projects"] + "\t" + "修复部位记录：" + repair_part + "\n"
    insurance_report_content += history_insurance_records_result
    if (len(insurance_report["history_insurance_records"]) == 0):
        insurance_report_content += '出险次数：没出过险'
    else:
        insurance_report_content += '出险次数：' + str(len(insurance_report["history_insurance_records"])) + "次\n"
    return car_source_info_content, insurance_report_content, car_age

def car_basic_info_parser(car_basic_info_multi_clue_id, clue_id, battery_report):
    """车辆基本信息解析"""
    if not car_basic_info_multi_clue_id:
        return "", "", "", ""

    car_basic_info_data = car_basic_info_multi_clue_id.get(str(clue_id), {})
    try:
        date_obj = datetime.strptime(str(car_basic_info_data["license_full_date"]), "%Y%m%d")
        plate_date = date_obj.strftime("%Y-%m-%d")
        current_date = datetime.now().strftime("%Y-%m-%d")
        car_age_years, car_age_months = calc_interval_months(plate_date, current_date)

        if car_age_years > 0 and car_age_months > 0:
            car_age = f"{car_age_years}年{car_age_months}个月"
        elif car_age_years > 0 and car_age_months == 0:
            car_age = f"{car_age_years}年"
        elif car_age_years == 0 and car_age_months == 0:
            car_age = "不到1个月"
        else:
            car_age = f"{car_age_months}个月"
    except Exception as e:
        car_age = ""

    car_owner_type = car_basic_info_data["car_owner_type"]
    if car_owner_type in ("1", "2"):
        car_owner_type = "公户" if car_owner_type == "1" else "私户"
    else:
        car_owner_type = ""

    store_id = car_basic_info_data.get("store_id", "")

    car_basic_info = {}
    for key in car_basic_info_data:
        if key in CAR_BASIC_INFO_MAP:
            if key == "audit_full_date" and str(car_basic_info_data[key]) == "19700101":
                car_basic_info.update({CAR_BASIC_INFO_MAP[key]: ""})
            elif key == "road_haul" and str(car_basic_info_data[key]) != "":
                car_basic_info.update({CAR_BASIC_INFO_MAP[key]: str(car_basic_info_data[key]) + "公里"})
            elif key == "car_owner_type" and str(car_basic_info_data[key]) in ("1", "2"):
                car_basic_info.update(
                    {CAR_BASIC_INFO_MAP[key]: "公户" if str(car_basic_info_data[key]) == "1" else "私户"})
            elif key == "car_color" and str(car_basic_info_data[key]) in COLOR_DICT:
                car_basic_info.update({CAR_BASIC_INFO_MAP[key]: COLOR_DICT[str(car_basic_info_data[key])]})
            elif key == "attr_carsource_battery_owner_type":
                if str(car_basic_info_data[key]) == "1":
                    car_basic_info.update({CAR_BASIC_INFO_MAP[key]: "电池买断（车主所有）"})
                elif str(car_basic_info_data[key]) == "2":
                    car_basic_info.update({CAR_BASIC_INFO_MAP[key]: "电池租用"})
                else:
                    car_basic_info.update({CAR_BASIC_INFO_MAP[key]: "查询不到"})
            else:
                # logger.info("key: %s,value: %s", key, car_basic_info_data[key])
                car_basic_info.update({CAR_BASIC_INFO_MAP[key]: str(car_basic_info_data[key])})

    car_basic_info.update({"电池检测报告": battery_report})

    # 增加车辆
    car_basic_info["车龄"]      = car_age
    car_basic_info["所在门店id"] = store_id
    return json.dumps(car_basic_info, ensure_ascii=False), car_age, car_owner_type, store_id


def convert_keys_to_chinese(data_dict):
    """
    将字典中的英文key转换为中文key

    Args:
        data_dict: 原始数据字典，key为英文

    Returns:
        转换后的字典，key为中文
    """
    result = {}

    for eng_key, value in data_dict.items():
        if eng_key in BATTERY_REPORT_MAP:
            chinese_key = BATTERY_REPORT_MAP[eng_key]
            result[chinese_key] = value
        else:
            # 如果映射表中没有对应的key，保持原样
            result[eng_key] = value

    return result

CAR_SOURCE_MAP_FILTER = {
    "clueId":"clue_id",
    "fullImageUrl":"全车图片链接",
    "attrOplCarTakeLookVideoUrl":"看车视频链接"
}


def car_source_other_info_parser(car_source_other_info):
    """车源其他信息解析"""
    if not car_source_other_info:
        return {}

    result = {}
    try:
        for key in car_source_other_info:
            if key in CAR_SOURCE_MAP_FILTER:
                result[CAR_SOURCE_MAP_FILTER[key]] = car_source_other_info[key]
        return result
    except Exception as e:
        return result
    return result

CAR_TYPE_REPUTATION_MAP_FILTER = {
    #"brand_id": "品牌ID",
    "brand_name": "品牌名称",
    #"caokong": "操控口碑",
    #"car_id": "车型ID",
    "cartype_name": "车型名称",
    #"doc_count": "车主评价数量",
    #"dongli": "动力性能口碑",
    #"jiashiganshou": "驾驶感受口碑",
    #"kongjian": "空间口碑",
    "koubei": "车主整体评价口碑",
    #"liangdian": "亮点车主口碑",
    "model_name": "车系名称",
    #"neishi": "内饰口碑",
    #"peizhi": "配置口碑",
    #"quedian": "缺点和不足口碑",
    #"shushixing": "舒适性口碑",
    #"tag_id": "车系ID",
    #"usage": "车辆用途场景",
    #"waiguan": "外观口碑",
    #"xingjiabi": "性价比口碑",
    #"xuancheliyou": "车主给出的选车理由",
    #"xvhang": "续航口碑",
    #"youhao": "油耗口碑",
    #"zhinenghua": "智能化口碑"
}


def car_type_reputation_info_parser(car_type_reputation_info):
    """车主的车型口碑信息解析"""
    if not car_type_reputation_info or not isinstance(car_type_reputation_info, dict):
        return {}

    result = {}
    try:
        for key in car_type_reputation_info:
            if key in CAR_TYPE_REPUTATION_MAP_FILTER:
                result[CAR_TYPE_REPUTATION_MAP_FILTER[key]] = car_type_reputation_info[key]
        return result
    except Exception as e:
        return result
    return result
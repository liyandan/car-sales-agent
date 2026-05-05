import re
import copy
import base64
import os
import time
import requests
import json
import concurrent.futures
from langchain_openai import ChatOpenAI

def removequotationmarks(question:str):
    if question is None or len(question) == 0:
        return ""
    else:
        # 将单引号替换为空
        remove_single_marks = question.replace("\'", "")

        # 将双引号替换为空
        remove_double_marks = remove_single_marks.replace("\"", "")

        # 所有都替换完毕以后返回拷贝后的question
        return copy.deepcopy(remove_double_marks)

def BochaSearch(query:str,topk:int=10,web_search_api_key:str=""):
    if query is None or len(query) == 0:
        return [],0.0

    #web_search_api_key =  "sk-af67cc86c92d40aeac7823293aab4524"
    websearch_url      =  "https://api.bochaai.com/v1/web-search"
    headers            = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {web_search_api_key}',
                          }
    time_begin = time.time()
    try:
        params = {
                "query": f"{query}",
                "summary": True,
                "freshness": "oneYear",
                "count": topk,
                "include":"autohome.com.cn|dongchedi.com|xin.com|renrenche.com",
                "page": 1
            }
        time_start = time.time()
        response = requests.post(websearch_url, headers=headers, data=json.dumps(params))
        time_end = time.time()
        json_data = response.json()
        return json_data,(time_end-time_start)*1000
    except Exception as e:
        time_error_end = time.time()
        return [],(time_error_end-time_begin)*1000

def BochaSearch_(query:str,topk:int=10,web_search_api_key:str=""):
    if query is None or len(query) == 0:
        return [],0.0

    #web_search_api_key =  "sk-af67cc86c92d40aeac7823293aab4524"
    websearch_url      =  "https://api.bochaai.com/v1/web-search"
    headers            = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {web_search_api_key}',
                          }
    time_begin = time.time()
    try:
        params = {
                "query": f"{query}",
                "summary": True,
                "freshness": "oneYear",
                "count": topk,
                "include":"autohome.com.cn|dongchedi.com|xin.com|renrenche.com",
                "page": 1
            }
        time_start = time.time()
        response = requests.post(websearch_url, headers=headers, data=json.dumps(params))
        time_end = time.time()
        json_data = response.json()
        return json_data,(time_end-time_start)*1000
    except Exception as e:
        time_error_end = time.time()
        return [],(time_error_end-time_begin)*1000

def getBoChaFinalResult_(status_code: int, body) -> dict:
    if status_code is None:
        return {
            "result": "[]",
            "retrieve_type": "联网检索"
        }
    if status_code != 200:
        return {
            "result": "[]",
            "retrieve_type": "联网检索"
        }
    else:
        try:
            search_result = body
            search_pages = search_result["data"]["webPages"]["value"]

            content = []
            for page in search_pages:
                summary = page["summary"]
                content.append(copy.deepcopy(summary))
            json_str = json.dumps(content, ensure_ascii=False)
            return {
                "result": json_str,
                "retrieve_type": "联网检索"
            }
        except:
            return {
                "result": "[]",
                "retrieve_type": "联网检索"
            }



def extract_clean_json(response):
    """
    从可能包含额外标记的响应中提取并解析JSON
    
    参数:
        response: 模型返回的原始字符串响应
        
    返回:
        解析后的JSON对象
    """
    # 尝试直接解析（如果返回的是干净的JSON）
    try:
        return json.loads(response)
    except:
        pass
    
    # 尝试移除代码块标记和多余引号
    # 匹配```json 和 ``` 之间的内容或 ```和``` 之间的内容
    code_block_pattern = r'```(?:json)?(.*?)```'
    match = re.search(code_block_pattern, response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except:
            pass
    
    # 尝试处理被引号包裹的JSON字符串
    if response.startswith('"') and response.endswith('"'):
        # 去除外层引号并处理转义引号
        unquoted = response[1:-1].replace('\\"', '"')
        try:
            return json.loads(unquoted)
        except:
            pass
    
    # 使用正则表达式尝试提取JSON对象
    json_pattern = r'({.*?})'
    match = re.search(json_pattern, response, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # 所有方法都失败时
    raise ValueError("无法解析JSON响应: " + response)

def websearch_car_config_result(question:str,websearch_topk:int =10,web_searh_api_key:str="sk-c12f4e3162ad493e83fdb50511d4660f"):
    # return {
    #              "websearch_knowledge_base" : "[]",
    #              "websearch_time" : 0.0,
    #              "retrieve_type": "联网检索"

    #     }
    if question is None or len(question) == 0:
        return {
                 "websearch_knowledge_base" : "[]",
                 "websearch_time" : 0.0,
                 "retrieve_type": "联网检索"

        }
    else:
        #联网检索，拿到结果、处理异常，并且组装得到的知识库
        # 1. 数据处理 ，去除单、双引号
        clean_question = removequotationmarks(question)
        # 2. 判断是否为空串
        if len(clean_question) == 0:
            return {
                "websearch_knowledge_base" : "[]",
                 "websearch_time" : 0.0,
                 "retrieve_type": "联网检索"
            }
        else:
            # 3. 联网检索车型配置，拿到结果
            rewrite_question = clean_question + "的配置"

            websearch_result,time_elapsed = BochaSearch_(rewrite_question,4,web_searh_api_key)
            if websearch_result is None or len(websearch_result) == 0:
                return {
                    "websearch_knowledge_base" : "[]",
                    "websearch_time" : time_elapsed,
                    "retrieve_type": "联网检索"
                }
            else:
                status_code = websearch_result["code"]
                websearch_final_result = getBoChaFinalResult_(status_code, websearch_result)["result"]
                return  {
                    "websearch_knowledge_base" : copy.deepcopy(websearch_final_result),
                    "websearch_time"           : time_elapsed,
                    "retrieve_type": "联网检索"
                }
def websearch_result(question:str,websearch_topk:int =10,web_searh_api_key:str="sk-c12f4e3162ad493e83fdb50511d4660f"):
    # return {
    #             "websearch_knowledge_base" : "[]",
    #             "websearch_time"           : 0.0,
    #             "retrieve_type"            : "联网检索"
    #     }

    if question is None or len(question) == 0:
        return {
                 "websearch_knowledge_base" : "[]",
                 "websearch_time" : 0.0,
                 "retrieve_type": "联网检索"
        }
    else:
        #联网检索，拿到结果、处理异常，并且组装得到的知识库
        # 1. 数据处理 ，去除单、双引号
        clean_question = removequotationmarks(question)
        # 2. 判断是否为空串
        if len(clean_question) == 0:
            return {
                "websearch_knowledge_base" : "[]",
                 "websearch_time" : 0.0,
                 "retrieve_type": "联网检索"
            }
        else:
            # 3. 联网检索，拿到结果
            websearch_result,time_elapsed = BochaSearch_(clean_question,4,web_searh_api_key)
            if websearch_result is None or len(websearch_result) == 0:
                return {
                    "websearch_knowledge_base" : "[]",
                    "websearch_time" : time_elapsed,
                    "retrieve_type": "联网检索"
                }
            else:
                status_code = websearch_result["code"]
                websearch_final_result = getBoChaFinalResult_(status_code, websearch_result)["result"]
                return  {
                    "websearch_knowledge_base" : copy.deepcopy(websearch_final_result),
                    "websearch_time"           : time_elapsed,
                    "retrieve_type": "联网检索"
                }

reason_prompt_dict =[{"question": "给我说说小鹏G6", "answer": "小鹏G6是一款科技感十足的纯电SUV，主打智能驾驶和长续航。从车主反馈来看，它的优势非常突出：\n1. **智能科技**：标配高阶智驾系统，高速NGP和自动泊车很实用，语音交互灵敏\n2. **续航充电**：625km长续航+超快充技术，10分钟能充200多公里\n3. **空间表现**：后排宽敞，后备箱能装，适合家庭出行\n4. **性价比高**：20万左右价位，配置比同级更丰富\n 不过也有车主提到高速风噪偏大、内饰储物设计不够人性化等小缺点。整体来看，G6特别适合追求科技体验和实用性的家庭用户。", "strategy": "1.直接一句话总结给出用户所指车型的主要优点。\n2.若有可参考知识库，基于知识库总结用户所提车型的各方面口碑亮点。\n3.简单总结一下用户所指车型的缺点和不足。\n4.真诚地向用户介绍这款车适合的人群和用途。"}, {"question": "特斯拉model Y适合二胎家庭吗？", "answer": "特斯拉Model Y作为一款中型纯电SUV，从空间和实用性来看，是比较适合二胎家庭的。以下是平台的分析：\n1. 空间表现：Model Y拥有宽敞的后排和后备箱空间，可以轻松容纳两个儿童安全座椅，后备箱容积达到854升（放倒后排可达2158升），婴儿车等大件物品也能放下。\n2. 便利性：全景玻璃车顶让车内更通透，后排乘客不会感到压抑；电动尾门方便开关；前后备箱设计增加了储物灵活性。\n3. 安全性：特斯拉的主动安全配置齐全，碰撞测试成绩优秀，对家庭用车很重要。\n 不过需要注意：\n 如果经常长途出行，要考虑充电便利性\n 后排座椅角度较直，长时间乘坐舒适性一般\n总体来说，Model Y能满足大多数二胎家庭的日常需求，建议您可以到店体验实车空间。", "strategy": "1.直接回答用户问题\n2.若有可参考知识库，基于知识库总结用户所提车型的各方面口碑亮点\n3.提醒用户在用车过程中需要注意的事项\n4.总结强调回答的原因，并真诚为用户提供建设性意见。"}, {"question": "奔驰B级操控性能如何？", "answer": "奔驰B级的操控性能表现相当出色：\n\n1. 转向系统：方向盘低速轻盈高速沉稳，指向精准且虚位小，城市驾驶非常灵活；\n2. 底盘调校：兼顾运动与舒适，过弯支撑稳定，高速行驶扎实感强；\n3. 车身设计：紧凑的车身配合小转弯半径，泊车和窄路调头都很方便。\n4. 同级对比：悬架支撑性优于奥迪A3 Sportback，比宝马2系旅行版转向精准度稍弱\n\n特别值得一提的是怀挡设计操作便捷，适应后体验很好。虽然防爆胎在颠簸路面会稍显硬朗，但整体操控优于同级平均水平，既能满足日常通勤也能带来轻度驾驶乐趣。", "strategy": "1.直接回答用户问题\n2.若有可参考知识库，基于知识库针对用户问题进行详细分析和总结\n3. 给出总结性回复，并真诚为用户提供意见。"}, {"question": "宝马2系 225i 敞篷轿跑车（2020款）", "answer": "您好，平台为您介绍2020款宝马2系225i敞篷轿跑车的关键信息：\n\n1. 动力配置：2.0T涡轮增压发动机，184马力，8AT变速箱，后驱布局，0-100km/h加速7.7秒\n2. 敞篷特点：软顶设计，开闭时间约20秒（可在50km/h以下操作）\n3. 实用空间：后备厢容积280-335L（敞篷开闭状态不同），后排可比例放倒\n4. 配置亮点：标配LED大灯、电动折叠后视镜、氛围灯，高配可选装哈曼卡顿音响\n\n该车型当年新车指导价约30-37万元，目前二手车市场价根据车况约20-25万元。敞篷机构建议重点检查，注意是否有异响或渗水痕迹。需要具体车源检测报告可以告诉平台哦。", "strategy": "1. 若有可参考知识库，基于知识库总结用户所问车型的关键配置信息\n2.为用户提供新车裸车指导报价范围\n3.为用户介绍二手车的报价范围\n4.提示用户在购买该车型时需要注意的检查点和其他帮助。"}, {"question": "车尾equus什么车", "answer": "根据您提到的\"Equus\"标识，这应该是现代汽车的雅科仕（Hyundai Equus）车型。雅科仕是现代汽车旗下的高端豪华轿车，主要特点包括：\n\n1. 定位：现代品牌的旗舰车型，竞争对手为奔驰S级、宝马7系等\n2. 动力：通常搭载大排量V8发动机3. 配置：配备豪华内饰及高科技配置\n4. 市场：主要面向韩国本土及部分海外市场\n\n该车型现已停产，被现代雅尊(Genesis)系列取代。如需了解具体车况信息，建议提供车辆识别代码或详细检测报告。", "strategy": "1. 直接回答用户问题\n2.介绍用户所提车型的配置亮点\n3.介绍用户所提车型的当前市场状态\n4.友善提醒用户如何进一步详细了解该车信息。"}, {"question": "理想L6算中型还是中大型车？", "answer": "根据厂商数据，理想L6的轴距达到2920mm，车身尺寸为4925×1960×1735mm（长×宽×高），属于中大型SUV级别。其空间表现和配置也符合这一级别的定位，例如五座布局、双叉臂+五连杆悬架等。如果您对具体空间体验有疑问，平台可以帮您进一步分析实车数据。", "strategy": "1.若有可参考知识库，基于知识库介绍和用户问题相关的参数\n2.直接回答用户问题\n3. 给出其他可以佐证答案的理由。\n4.友善提醒用户需要进一步帮助可分析实车数据。"}, {"question": "极氪X和欧拉好猫GT都是什么牌子？", "answer": "极氪X是吉利汽车旗下高端新能源品牌极氪的车型，定位为紧凑型纯电SUV，主打科技感和性能。欧拉好猫GT则是长城汽车旗下欧拉品牌的一款小型纯电动车，偏向时尚运动风格，适合城市代步。两个品牌都专注于新能源领域，但定位和风格有所不同。", "strategy": "1.分别针对用户问题中的不同车型给出答案\n2.再介绍每款车型的定位和主打方向\n3. 最后介绍两款车型的共同点和不同点。"}, {"question": "传祺M6的空间与舒适性", "answer": "传祺M6作为一款家用MPV，在空间和舒适性方面表现非常出色。空间上采用灵活座椅布局，前两排宽敞，180cm乘客可轻松翘腿，第三排170cm成人乘坐无压力，后备箱下沉式设计实用，魔术翻转后容积达1100L。舒适性方面，第二排独立座椅支持多角度调节，底盘调校偏向家用，能有效过滤细碎震动，NVH控制良好，中低速静谧性优异。整体来看，传祺M6以亲民价格提供了越级的空间和舒适体验，特别适合家庭出行需求。", "strategy": "1.直接回答用户问题\n2.若有可参考知识库，基于知识库分别回答用户提问中的每个口碑方面\n3.总结口碑表现，友善提醒用户该车型的主要用途和适合的应用场景。"}, {"question": "小鹏P5：高阶智能驾驶辅助", "answer": "小鹏P5的高阶智能驾驶辅助主要体现在550P和510E车型上，搭载了XPILOT系统，支持全速自适应巡航、车道保持、自动泊车等功能。硬件方面配备了5个毫米波雷达、13个摄像头和12个超声波雷达，芯片算力达30TOPS。不过这些功能需要选装智能辅助驾驶包才能完全解锁。", "strategy": "1.首先介绍用户问题关联的车型\n2.若有可参考知识库，再基于知识库介绍用户关注的车型配置详情\n3. 最后提醒用户哪些是正常配置，哪些是选装配置。"}, {"question": "远景X3（2020款 1.5L CVT尊贵型）", "answer": "感谢您关注远景X3这款车型！2020款1.5L CVT尊贵型是款非常实用的精品小型SUV，我来为您详细介绍它的核心亮点：\n\n车型配置亮点：\n动力系统：搭载1.5L四缸发动机（109马力）+模拟8速CVT变速箱，百公里综合油耗仅6.1L，平顺省油\n智能配置：配备8英寸中控屏+GKUI吉客智能系统，支持语音控制/车载WiFi/高德导航\n安全防护：标配博世9.3版ESP+胎压监测，尊贵型独有前排侧气囊和360°全景影像\n舒适配置：皮质座椅+电动天窗+自动空调，后排座椅支持4/6比例放倒（容积扩展至1150L）\n新车指导价：6.89万元（2020年款）\n这款车特别适合城市通勤，小巧车身（4005mm长度）方便停车，172mm离地间隙又能应对复杂路况。需要我为您查询具体车源信息吗？", "strategy": "1. 首先重复用户用户关注的提问车型\n2. 然后，若有可参考知识库，基于知识库介绍该车型的核心参数配置\n包括：动力系统、智能配置、安全防护配置和舒适配置等\n3. 接着介绍该车型的参考新车指导报价\n4. 诚恳地为用户提供该车的适合用途和使用场景建议。"}, {"question": "小鹏保养成本高不高", "answer": "小鹏作为新能源车，保养成本相比燃油车要低很多。保养周期通常为1年或1万公里，单次基础保养费用约300-500元，仅为传统燃油车的1/3左右。\n主要保养项目包括三电系统检测、底盘检查、轮胎轮毂检查等。由于没有发动机、变速箱等复杂部件，省去了机油、机滤、火花塞等费用，且制动系统损耗小。\n需要注意的是，电池健康度检测建议每2年做一次约200元，空调滤芯更换频率较高约150元/年，轮胎更换成本与燃油车相当。\n总体来说，相比同价位燃油车，小鹏5年保养成本可节省约6000-8000元。具体费用会因车型和地区略有差异，建议通过小鹏APP获取定制化保养计划。", "strategy": "1. 首先介绍用户所问车型是什么能源类型车型\n2. 然后直接回答用户提问\n3. 介绍主要的保养项目有哪些\n4. 介绍单次保养费用范围\n5. 提醒用户不同的车型、不同的地区存在差异\n6. 提示用户除了回答的建议外，还应该关注官方渠道的最新保养价目表"}, {"question": "五菱怎么热车？", "answer": "关于五菱的热车操作，平台为您整理以下专业建议：\n\n1. 基础热车：\n 冷启动后先怠速2-3分钟（冬季适当延长）\n 转速稳定后低速行驶热车，避免原地长时间怠速\n\n2. 冬季特别提醒：\n 北方地区建议热车1.5-2分钟\n 热车期间不要开启暖风\n 前3公里保持平缓驾驶\n\n3. 注意事项：\n 避免高转速热车\n 水温达80-90℃后再正常行驶\n 长时间停放后需重新热车\n\n平台提醒：需要了解您的具体车型（如五菱宏光/荣光/缤果等），不同车型可能有细微差异，我可以提供更精准的建议。", "strategy": "1. 首先按操作流程回答用户问题\n2. 然后提示用户特殊注意事项，可以针对不同发动机类型、燃油标准类型、动力类型、\n季节等进行详细讲解。\n3. 友情提示用户在操作过程中需要注意的其他事项。"}, {"question": "宝马x3 2021款有几个配置", "answer": "2021款宝马X3共有4个配置：\nxDrive25i 豪华套装：搭载2.0T 184马力发动机，最大功率135kW，0-100km/h加速8.9秒\n改款 xDrive25i 豪华套装：配置与基础版相同\nxDrive28i 豪华套装：搭载2.0T 224马力发动机，最大功率165kW，0-100km/h加速7.6秒\n改款 xDrive28i 豪华套装：配置与28i基础版相同\n小贴士：\n所有版本均配备xDrive四驱系统，匹配8AT变速箱。全系标配全景天窗、电动后备厢等配置。2021款中期改款后全系标配LED大灯，高配版本带蓝色激光模组。\n主要区别在于动力参数，25i和28i版本在功率和加速性能上有所差异。在二手车市场上，28i版本流通量较大，性价比较高。", "strategy": "1.直接回复用户问题\n2.简单列出车型年款下的所有配置\n3.若有可参考知识库，基于知识库分别针对每一款配置介绍核心参配信息，\n包括发动机、变速箱、零百加速时间、油耗等信息。"}, {"question": "智能化配置和续航（零跑T03）", "answer": "零跑T03的智能化配置和续航表现如下：\n智能化配置：\n全系标配10.1英寸中控屏+GPS导航，支持车联网和OTA升级。\n高配版配备L2级辅助驾驶，包含自适应巡航和车道保持功能。\n全系标配倒车雷达，部分车型带倒车影像。\n支持手机互联，APP远程控制，可查看电量、预约充电、空调预启动。\n续航表现：\n403km版本实际续航城市通勤约350km，高速约280km。\n快充0.6小时可充至80%，慢充需3.5-6.5小时。\n电池组质保8年/15万公里。\n建议城市代步选择403km轻享版（5.99万），智能化配置够用且续航实在。北方用户建议加装电池保温套件（约2000元），能有效改善冬季表现。", "strategy": "1. 首先重复用户提问中的车型名称\n2. 若有可参考知识库，基于知识库总结用户所问车型在不同方面的口碑\n3.总结用户所问车型口碑带给用户的好处或便利性。"}, {"question": "捷豹xe是国几？", "answer": "关于捷豹XE的排放标准，需要根据具体年份和版本来判断：\n\n1. **2015-2018款进口XE**：\n 多为国五排放标准（部分2015款可能是国四）\n 2.0T和3.0T机械增压版本均符合国五\n\n2. **2019款及之后**：\n 部分车型升级到国六标准\n 尤其2019年7月后生产的车型（国内实施国六后）\n\n小贴士：国五车在非一线城市仍可正常过户，但北上广深等限迁城市需国六标准。需要帮您查具体车源信息吗？", "strategy": "1. 若有可参考知识库，基于知识库直接回答用户问题\n2. 进一步说明是否符合主流排放标准要求。"}, {"question": "宝马X3开起来爽吗？", "answer": "根据宝马X3 2020款和2021款xDrive25i豪华套装的口碑反馈，这款车在驾驶体验上确实能带来“爽快感”，主要体现在以下几个方面：\n\n1. **操控精准灵活**  \n    方向盘指向无虚位，底盘调校扎实，高速过弯时侧倾控制优秀，转弯半径接近轿车水平（操控性评分4.7-5.0分）。\n    车主反馈“过弯道和超车时灵活稳定”“高速行驶车身平稳”，甚至有“能纠正不良驾驶习惯”的评价。\n\n2. **动力响应积极**  \n    2.0T低功率发动机（xDrive25i）实际表现超出预期：市区加速轻快，运动模式推背感明显，中段加速（80-120km/h）尤为顺畅。\n    2021款车主提到“动力随叫随到”“标准模式下响应迅速”，但高速130km/h后提速会稍显乏力。\n\n3. **驾驶质感突出**  \n    四驱系统提供良好稳定性，底盘保留运动基因的同时兼顾舒适性，滤震表现优秀（防爆胎在细碎路面偶有震动）。\n    2020款车主特别称赞“驾驶感接近轿车”，2021款则强调“刹车线性”“减震效果优秀”。\n\n**需注意的短板**：  \n 低速20km/h左右变速箱偶发顿挫（尤其拥堵路段）  \n 防爆胎导致高速风噪/胎噪较明显（100km/h以上）  \n 运动调校的悬挂过减速带时路感偏硬  \n\n总结来说，宝马X3在同级豪华SUV中属于驾驶乐趣第一梯队的车型，适合追求操控精准度和动力响应速度的用户。如果偏好“人车合一”的驾驶体验，它的表现绝对能让你感到“爽”，但若更注重极致平顺性，可能需要适应低速时的轻微顿挫感。", "strategy": "1. 首先直接回答用户问题\n2.然后，若有可参考知识库，基于知识库从操控性、动力、驾驶感受等方面详细介绍\n关于这款车的用户口碑反馈\n3.最后善意提醒用户留意该车型的一些短板或缺点\n4.结合用户提问，给到用户选择该车的理由。"}, {"question": "奥迪A4好在什么地方？", "answer": "奥迪A4作为经典豪华车型，其优势主要体现在以下几个方面：\n\n1. **动力性能卓越**\n    3.0L V6版本（2004款）动力储备充足，加速强劲，低速响应迅捷，中高速段超车轻松，被车主誉为\"驾驶者之车\"\n    1.8T涡轮增压版本（2004款）在1800-4000转区间动力充沛，涡轮介入后加速迅猛，市区超车游刃有余\n\n2. **操控体验突出**\n    quattro四驱系统（3.0L版本）提供优秀的弯道稳定性\n    底盘调校扎实精准，高速行驶稳定性强\n    转向反馈清晰，运动化调校带来丰富驾驶乐趣（1.8T版本高速方向盘力度适中，低速稍重）\n\n3. **豪华品质与耐用性**\n    内饰做工精良，采用桃木饰板、软质塑料等高级材质（3.0L版本）\n    德系工艺扎实，车身结构坚固，配件使用寿命长（1.8T版本耐用性可达10年以上）\n    经典外观设计历久弥新，圆润造型至今仍显时尚\n\n4. **性价比优势（二手市场）**\n    当年近60万的新车价，现二手仅5-7.5万即可拥有3.0L quattro四驱系统\n    1.8T版本维护成本合理，主要更换老化部件即可长期使用\n\n5. **细分场景优势**\n    城市驾驶：车身尺寸适中，窄路行驶和侧方停车方便\n    长途出行：高速巡航油耗优化明显（3.0L高速8-10L/100km，1.8T高速8L/100km）\n    驾驶乐趣：手动挡版本（1.8T）提供更直接的操控体验\n\n需注意的不足：3.0L版本市区油耗较高（12-14L/100km），后排空间相对局促；1.8T版本存在机油消耗现象。但整体而言，A4在动力、操控和豪华感方面的表现使其成为二手市场中性价比突出的豪华车型选择。", "strategy": "1. 若有可参考知识库，基于知识库从多个口碑角度总结用户所问车型的优势和亮点\n2. 总结整理哪些方面是凸显该车的优势。"}, {"question": "卡罗拉双擎多长时间保养一次？", "answer": "根据参考信息，卡罗拉双擎的保养周期如下：\n\n1. **常规保养周期**\n    **基础周期**：每1万公里或6个月保养一次（以先到者为准）。\n    **首保**：建议在购车后3000公里或3个月内进行首次检查（部分官方提供免费首保）。\n    **二保**：1万公里或1年时进行第二次保养（部分车型享受免费二保）。\n\n2. **特殊情况调整**  \n    **恶劣环境**：若经常在灰尘多、路况差的地方行驶，需缩短保养周期（可能需提前至8000公里或更短）。\n    **良好路况**：若行驶路段干净且用车频率低，可适当延长至1万公里以上。\n\n3. **大保养建议**  \n    行驶6万公里后需进行大保养，包括更换机油、三滤（机油滤芯、空气滤芯、燃油滤清器）、刹车片，以及清洗喷油嘴、进排气系统等。\n\n4. **其他注意事项**  \n    混合动力电池享受8年/20万公里免费维护，常规保养无需额外关注电池。\n    建议严格遵循《保养手册》的官方要求，不同年份车型可能存在细微差异。\n\n**总结**：常规情况下按1万公里/6个月保养即可，具体需结合实际用车环境和手册说明调整。", "strategy": "1. 若有可参考知识库，基于知识库直接回答用户问题\n2. 给出有哪些特殊情况需要注意\n3. 说明大的保养的策略\n4. 给出其他需要注意的地方\n5. 善意地从朋友的角度给到用户剪短总结性的实用的建议。"}, {"question": "五菱宏光怎么换备用胎", "answer": "以下是五菱宏光更换备胎的详细步骤及注意事项，结合了多个权威来源的指导：\n\n### **更换备胎步骤**\n1. **安全准备**  \n    将车辆停放在**平坦、稳固且远离车流**的地方（如紧急停车带）。\n     打开**双闪警示灯**，拉起手刹，挂入P挡（自动挡）或倒挡（手动挡）。\n     在车后**50-100米处**放置三角警示牌，提醒后方车辆。\n\n2. **取出工具和备胎**  \n    打开后备箱，掀开地板找到备胎（通常位于后备箱下方）。\n     用轮胎扳手**逆时针拧松备胎中间的固定螺丝**，取下备胎。\n     从副驾驶座位下或后备箱取出工具包（含千斤顶、摇把、轮胎扳手）。\n\n3. **松动故障轮胎螺丝**  \n    用轮胎扳手**对角线顺序**稍微松动轮胎螺栓（先别完全拧下，防止车轮倾斜）。\n\n4. **顶升车辆**  \n    找到车辆底部的**千斤顶支撑点**（侧裙下方有标记，避免顶错位置损坏底盘）。\n     用摇把**顺时针转动千斤顶**，缓慢顶起车辆，直到故障轮胎离地约2-3厘米。\n\n5. **更换轮胎**  \n    完全拧下螺栓，取下故障轮胎。\n     将备胎对准轮毂螺栓孔，**手动预紧所有螺栓**（确保贴合到位）。\n     **对角线顺序**用扳手初步拧紧螺栓（避免受力不均）。\n\n6. **降车并紧固**  \n    缓慢逆时针降下千斤顶，使备胎完全着地。  \n    再次用扳手**对角线顺序**全力紧固螺栓（确保牢固）。\n\n### **关键注意事项**\n  **备胎仅限应急**：备胎（通常为非全尺寸）最高时速不超过80km/h，需尽快更换正规轮胎。\n  **千斤顶安全**：必须顶在专用支撑点，避免车辆滑落或侧倾。  \n **螺栓顺序**：务必按对角线紧固，防止轮毂变形（如左上→右下→右上→左下）。\n  **斜坡风险**：严禁在斜坡或松软地面操作，必要时呼叫专业救援。\n\n### **常见问题**\n  **备胎取不下？**：检查固定螺丝是否完全松开，必要时喷涂润滑剂辅助。\n  **工具找不到？**：参考手册确认存放位置（部分车型工具在座椅下方或后备箱暗格）。  ", "strategy": "1. 若有可参考知识库，基于知识库回答用户问题2. 提醒用户注意事项3. 耐心跟用户解释常见问题。"}, {"question": "宝来前翼子板刮蹭怎么修？", "answer": "宝来前翼子板刮蹭修复方案需根据损伤程度选择：\n轻微刮蹭（仅伤清漆层）：采用局部抛光+点漆，费用100-300元，美容店即可处理，施工约1小时，能保留原厂漆。\n中度刮蹭（露底漆但无变形）：可选择整面喷漆（4S店500-800元，路边店300-500元）或局部补漆（费用约传统方案60%）。注意宝来糖果白/魔力灰等颜色容易有色差，要求店家做色差测试。\n严重变形+掉漆：必须钣金修复（200-400元）+整面喷漆，需检查大灯支架是否移位（宝来通病）。\n建议先到一汽大众4S店做免费损伤评估，使用BASF鹦鹉漆匹配度最高。尽量避免整个翼子板更换，保留施工照片和用料清单有助保值。", "strategy": "1. 车况较好的车源，总体评价车况状态\n2. 概括性描述瑕疵内容，提供场景化解读打消用户顾虑\n3. 从用户角度出发，提供共情化解读"}, {"question": "小米SU7 Ultra有哪些配置", "answer": "小米SU7 Ultra作为小米汽车的旗舰车型，配置非常豪华。以下是它的主要配置信息：\n\n核心参数配置：\n 动力系统：双电机四驱，最大功率673kW，峰值扭矩838N·m\n 续航里程：800km（CLTC工况） 0-100km/h加速：2.78秒\n 最高车速：265km/h\n 电池容量：101kWh三元锂电池\n\n外观和内饰：\n 21英寸运动轮毂\n 电动升降尾翼\n Brembo高性能制动系统\n 全景天幕\n 高级Nappa真皮座椅\n 16.1英寸3K中控屏\n 56英寸HUD抬头显示\n\n驾驶辅助和安全技术：\n 小米Pilot Max高阶智能驾驶辅助系统\n 激光雷达\n 11个高清摄像头\n 3个毫米波雷达\n 12个超声波雷达\n 全场景自动泊车\n\n科技配置：\n 骁龙8295智能座舱芯片\n 25扬声器音响系统\n 车载冰箱\n 智能香氛系统\n 五屏联动系统\n\nSU7 Ultra代表了小米汽车的最高技术水平，无论是性能、科技还是豪华感都达到了顶级水准。", "strategy": "1.如果有知识库，基于知识库从核心参数配置、外观和内饰、驾驶辅助技术和安全技术、科技配置等方面进行回答。\n2.对整体配置的亮点进行总结。 "}, {"question": "买你们车充电桩怎么解决", "answer": "您好！关于购买电动车后的充电桩问题：\n目前车辆和充电桩通常是分开销售的，一般不会赠送充电桩，建议您咨询车商或专属顾问了解具体情况。\n充电解决方案有几种：\n1. 如果您有固定车位，可以申请安装家用充电桩，需要准备车位产权证明、租赁合同等材料，向物业和国家电网申请安装。\n2. 如果没有固定车位，可以使用附近的公共充电桩进行快充，或选择配备充电桩的停车场，很多停车场都提供充电服务。\n建议根据您的居住环境和使用需求来选择最适合的充电方式", "strategy": ""}, {"question": "高合还能买吗", "answer": "高合汽车购买需要非常谨慎，平台为您分析几点关键信息：\n企业现状方面，高合汽车母公司华人运通陷入债务危机并大规模裁员，2023年销量仅4829辆，市场表现不佳，曾出现停工停产、拖欠交付等问题，售后服务体系存在中断风险。\n主要风险包括：维修配件供应和OTA升级难以保证，品牌若退出市场二手车贬值幅度较大，质保承诺履行存疑。\n优势是设计独特，如鸥翼门、智能展翼门等科技感强，配置丰富，但存在技术成熟度不足、车机卡顿、智能驾驶功能落后等问题，性价比与定价不匹配。\n如果必须购买，建议选择现车、核实手续完整、购买第三方延保并及时上牌。更建议考虑售后体系稳定的替代品牌，如蔚来ET5、极氪001、宝马i3、奔驰EQE等同级别车型。", "strategy": ""}, {"question": "跑了3至4年的二手电动车能买吗会不会毛病频出", "answer": "跑了3-4年的二手电动车可以考虑购买，但需要重点关注电池状况。\n电池健康度是关键因素，这个车龄段电池容量衰减通常在15-25%左右，若低于70%健康度续航会明显缩水。建议优先查看官方电池检测报告，做满充满放测试验证实际续航。\n相比燃油车，电动车机械结构简单，没有发动机、变速箱等复杂部件，传统意义上的\"大修\"问题较少。常见问题主要是充电接口氧化、悬挂衬套老化、车机系统卡顿、空调压缩机故障等，维修费用相对可控。\n建议满足以下条件再考虑入手：电池健康≥80%，剩余保修期＞3年，车价低于新车50%，有完整保养记录。重点关注主流品牌如比亚迪、特斯拉等有8年15万公里电池质保的车型。寒冷地区使用的车辆电池衰减更快，需额外注意", "strategy": ""}, {"question": "2024款小鹏P7充电多久", "answer": "2024款小鹏P7的充电时间因充电方式不同而有差异：\n快充方面，使用第三方快充桩从10%-80%约需30分钟，充至100%约需1-1.5小时。使用小鹏自营超充桩可缩短至40分钟左右。部分支持800V高压平台的车型配合S4超充桩，10%-80%充电时间可缩短至12分钟，5分钟可补充200公里续航。\n慢充方面，使用7kW家用充电桩约需6-10小时充满，11kW充电桩可缩短至5-8小时。随车充（便携式）约需18-20小时。\n充电时间会受多种因素影响：电池容量（长续航版80.9kWh比标准续航版60.2kWh时间更长）、环境温度（低温会延长20%-30%充电时间）、充电桩功率等。\n建议日常使用家用慢充，长途出行选择小鹏超充站或高功率快充桩。", "strategy": ""}, {"question": "新能源二手车电池健康度怎么查", "answer": "您好，我是平台。查询新能源二手车电池健康度，可以尝试以下方法：\n1、您可以直接向平台提问查询具体车源的电池健康度信息。\n2、查看瓜子二手车检测报告中的电池健康度数据。\n3、联系联系专属客服或者进入直播间咨询车上，获取更详细的电池健康报告。\n其他公开的检测方法还包括：\n联系品牌4S店或官方售后用专业设备读取电池数据，费用200-500元，能获取实际容量百分比、循环次数等核心数据。通过专业诊断仪连接车辆OBD接口，重点看SOH值，健康度＞85%算良好。\n在瓜子二手车平台购车时，优先选择带“100天电池保障”的车辆，若发现异常，可受到瓜子权益保障。", "strategy": ""}, {"question": "理论510实际能跑多少公里", "answer": "理论续航510km的电动车，实际续航表现如下：\n春秋季（20℃左右）：约430-460km，能达到理论续航的85-90%。\n夏季开空调：约380-420km，打75-85折，空调制冷对续航影响相对较小。\n冬季（0℃以下）：约300-350km，打6-7折，暖风耗电量大是主要原因。\n具体影响因素包括：驾驶习惯（急加速/超速减少15-20%续航）、路况条件（高速100km/h以上减少约25%）、电池衰减（2年后可能衰减5-8%）。\n真实案例显示，城市通勤均速40km/h可达450km，高速110km/h约350km，冬季-10℃约280km。\n建议按以下规划：城市通勤可按400km+计算，高速长途按350km规划补电，冬季按300km规划。优化续航可保持30-80%电量使用、冬季预热电池、使用ECO模式等。", "strategy": ""}, {"question": "租用电池是什么概念", "answer": "租用电池是指购买电动车时，电池以租赁方式使用，车价不含电池费用，用户按月支付电池租金的模式。电池产权属于车企，用户获得使用权。\n主要优势包括：降低购车门槛，车价立减7-10万元（如70kWh电池约少付7万）；灵活升级，可根据需求租用不同容量电池；免除电池衰减焦虑，性能下降时可申请更换；电池维护由车企承担。\n需注意的问题：租金成本较高，70kWh电池约980元/月；长期使用更贵，10年租金约11.7万，比买断多花约4万；带租赁协议的二手车转售价格可能较低。\n适合短期换车用户（3-5年内换车）、追求低首付的消费者、常需电池升级的用户如网约车司机。\n目前蔚来BaaS、北汽、东风等品牌提供该模式。如果计划长期持有车辆建议买断电池，想体验新技术或资金有限则租赁更灵活。", "strategy": ""}, {"question": "一般。宝马X一几个油市区跑。", "answer": "关于宝马X1的市区油耗表现，平台为您总结不同版本的实际反馈：\n1.5T三缸版本（B38发动机）：市区综合油耗约8.5-10L/100km，这是最经济的燃油版本。\n2.0T四缸版本（B48发动机）：市区综合油耗约9-11L/100km，动力更强但油耗稍高。\n插电混动版（xDrive25e）：纯电模式可行驶50-60km，混动模式下油耗约2-3L/100km，是最省油的选择。\n市区油耗会受多种因素影响：拥堵程度严重时油耗可能增加15-20%，急加速急刹车会使油耗增加1-3L，夏季开空调会增加0.5-1.5L油耗。\n真实车主反馈显示，2022款sDrive25Li在纯市区（如上海）平均油耗约9.8L/100km。\n如果主要城市通勤，1.5T版本经济性更佳；预算充足可考虑插混版显著降低燃油成本。", "strategy": ""}, {"question": "我想了解传奇商务车", "answer": "传奇商务车（如广汽传祺M8）是广汽传祺旗下的高端MPV车型，主打商务接待和家庭出行双重场景，与别克GL8、本田奥德赛等车型竞争。\n核心优势包括：空间表现出色，轴距通常超3米，三排座椅灵活布局；舒适配置丰富，配备航空级座椅、后排隐私帘、多区空调；搭载ADiGO智驾系统，支持L2级辅助驾驶；提供2.0T燃油版和混动版双动力选择。\n如果考虑二手车，需重点检查底盘悬挂（商务车使用强度较大）、电动侧滑门轨道机构、座椅调节功能及皮质损耗情况。市场行情显示，3年车龄保值率约65%-70%，混动版比燃油版溢价约1.5-2万元。\n适合中小企业主接待用车、多孩家庭出行需求、高端网约车服务场景等用户群体。\n建议根据具体使用需求，重点关注车辆保养记录和内饰成色。如需了解具体车源信息，可提供预算范围进一步分析。", "strategy": ""}, {"question": "首任车主与非首任车主质保有区别吗？", "answer": "首任车主与非首任车主在质保权益上确实存在明显差异：\n首任车主专属权益：多数品牌（如蔚来、小鹏等）为首任车主提供终身质保或更长年限保障，包括三电系统终身保修、免费道路救援、车机流量终身免费等增值服务，但这些权益通常随车过户自动失效。\n非首任车主保障：可享受厂家基础质保（如3年/10万公里），但剩余保修期按首任车主购车时间起算，需提供完整保养记录，改装过核心部件可能影响保修资格。\n特殊案例：蔚来首任车主享电池组终身质保，二手车主无法继承；理想ONE首任车主有电池终身保修和免费充电权益，二手车主仅保留1年保修；特斯拉例外，全系跟随车辆不跟人，二手车主可继承剩余质保，官方认证二手车还能获得额外1年/2万公里延保。\n建议购买二手车时详细了解具体品牌的质保政策。", "strategy": ""}, {"question": "Model 3常见维修项目有哪些？", "answer": "Model 3常见维修项目主要包括：\n电池系统维护：电池健康度检测（建议每年1次）、高压线路检查（2年或4万公里）、充电口维护清洁氧化触点。\n电机系统：电机轴承更换（约10万公里后可能出现）、冷却液更换（每4年/8万公里）。\n电子系统高频问题：中控屏触控失灵、车门电子开关故障（冬季高发）、传感器误报需校准。\n常规维护：轮胎每1万公里检查换位和四轮定位、制动液每2年检测更换、空调滤清器每年更换、干燥剂6年更换。\n车身相关：无框车门密封条更换（3-5年）、全景天窗排水管疏通。\n特色部件：充电线缆总成（频繁使用易损）、热泵系统冷媒补充（寒冷地区）、自动驾驶摄像头校准。\nModel 3的维修主要集中在轮胎、制动系统、空调和电子设备，相比燃油车更省心。质保期内建议优先选择官方售后，避免因非认证维修导致保修失效。", "strategy": ""}, {"question": "五菱MPV安全配置推荐", "answer": "五菱MPV各车型安全配置推荐如下：\n五菱凯捷（安全配置最全）：采用63%高强钢+31.53%航空级超高强钢车身，高配车型配备6安全气囊、ESP车身稳定系统、360度全景影像、ADAS驾驶辅助系统。推荐1.5T CVT旗舰型。\n五菱佳辰（性价比高）：笼式车身结构，中高配车型配备主副驾+侧气囊、ESP、ABS、360°全景影像。推荐1.5T CVT智享豪华型。\n五菱宏光PLUS（经济实用）：标配ESP、ABS+EBD、胎压监测、倒车雷达，高配车型配置较全。推荐1.5T手动豪华型。\n五菱征程（商用为主）：基础安全配置，营运版可选ESP、后轮盘刹，安全配置相对较低。\n平台选购建议：家用首选凯捷或佳辰，商用选征程，经济实用选宏光PLUS。建议优先选择中高配车型，安全配置更完善。", "strategy": ""}]

def select_best_matched_examples(input: str) -> dict:
    reason_prompt_list  =  reason_prompt_dict  # json.loads(reason_prompt_list)
    retrieve_type_str   =  "无需知识库检索"
    few_shot = []
    try:
        result_structure = json.loads(input)
        retrieve_type_str = result_structure["检索类型"]
        case_list = result_structure["最相似问题"]

        #case_list = json.loads(input)

        for index in case_list:
            # index = case
            question = reason_prompt_list[index]["question"]
            # assert reason_prompt_list[index]["question"] == question
            answer = reason_prompt_list[index]["answer"]
            strategy = reason_prompt_list[index]["strategy"]
            few_shot.append({
                "问题": question,
                "答案": answer,
                "回答策略": strategy
            })
        return {
            "few_shot": json.dumps(few_shot, ensure_ascii=False),
            "retrieve_type": f"{retrieve_type_str}"
        }
    except Exception as e:
        try:

            result_structure = extract_clean_json(input)
            retrieve_type_str = result_structure["检索类型"]
            case_list = result_structure["最相似问题"]
            few_shot = []
            for index in case_list:
                # index = case
                question = reason_prompt_list[index]["question"]
                answer = reason_prompt_list[index]["answer"]
                strategy = reason_prompt_list[index]["strategy"]
                few_shot.append({
                    "问题": question,
                    "答案": answer,
                    "回答策略": strategy
                })
            return {
                "few_shot": json.dumps(few_shot, ensure_ascii=False),
                "retrieve_type": f"{retrieve_type_str}"
            }
        except Exception as e:
            #print(f"Error converting category to dict: {e}")
            return {
                "few_shot": "",
                "retrieve_type": "无需知识库检索"
            }

class Ner(object):

    @staticmethod
    def has_entity(
            query
    ):
        url = "http://ai-nlp-std-ner.guazi-apps.com/nerForIR"
        try:
            data = {"query": query}
            ori_response = requests.post(url=url, json=data)
            response = json.loads(ori_response.text)
            return response
        except Exception as e:
            print(e)
            return {}


# 生产环境(在线接口)
api_endpoint_searchner = "http://search-nlp-ner.guazi-apps.com/search/nlp/car"
# 测试环境（测试接口）
# api_endpoint_searchner = "http://search-nlp-ner.guazi-cloud.com/search/nlp/car"
# 生产环境（在线token）
api_token = "3c5febb881afc062d09f3f15a0d69997"
# 测试环境（测试token）
# api_token = "d6fad81268eea3df77ae7267778f742a"
# 准备请求头
headers_retrieval_ner = {
    "Content-Type": "application/x-www-form-urlencoded",
    "uuid": "C7956700-EA7D-4BAF-B65D-5D94BD98B4F3",
    "source": "app",
    "token": f"{api_token}",
    "dataType": "1",
    "product": "lm-agent",
}


def get_searchengine_nerresult(question: str):
    try:
        # 1.准备请求体
        payload = {
            "keyword": f"{question}"
        }

        # 2.发送POST请求
        response = requests.post(
            api_endpoint_searchner,
            headers=headers_retrieval_ner,
            params=payload
        )
        if response.status_code != 200:
            return None
        return response
    except requests.exceptions.RequestException as e:
        print(f"请求搜索ner接口发生异常: {str(e)}")
        return None


def getBrandAndChexi(query: str):
    brand = ""
    chexi = ""
    if (query is None) or (len(query) == 0):
        return brand, chexi
    else:
        # 调用搜索团队线上接口
        response = get_searchengine_nerresult(query)
        if response is None:
            return brand, chexi
        else:
            json_data = response.json()
            if json_data.get("nerResult") is None:
                return brand, chexi
            else:
                nerResult = json_data.get("nerResult")
                if len(nerResult) > 0:
                    try:
                        if nerResult[0].get("car_minor") is not None:
                            brand = nerResult[0].get("car_minor")[0].get("name", "")
                        if nerResult[0].get("car_tag") is not None:
                            chexi = nerResult[0].get("car_tag")[0].get("name", "")
                    except Exception as e:
                        pass

    return brand, chexi


def getNerResult(query: str):
    # print(f"Query输入:{query}")
    ner = Ner()
    ner_result = {
        "brand": "",
        "chexi": "",
        "year": ""
    }
    if query is None or len(query) == 0:
        return ner_result

    result = ner.has_entity(query)

    try:
        car_year = {
            "value": "",
            "confidence": 0.00
        }

        brand = {
            "value": "",
            "confidence": 0.00,
        }

        chexi = {
            "value": "",
            "confidence": 0.00
        }

        # 解析NER的结果
        for item in result['data']:
            entity_name = item['entity_name']
            entity_value = item['entity_value']
            entity_type = item['type']
            confidence = item['confidence']

            #print(f"实体类型：{entity_name},实体字面值:{entity_value},实体数值类型:{entity_type},置信度:{confidence}")

            if entity_name == "car_year":
                try:
                    if confidence > car_year['confidence']:
                        # 拿到car_year 的值后再判断
                        if entity_type == "number":
                            year = entity_value['min_value']
                            if len(str(year)) == 4:
                                car_year['value'] = str(year)
                                car_year['confidence'] = confidence
                except Exception as e:
                    print(f"车型年款实体识别解析失败:{e}")
            if (entity_name == "brand") and (entity_type == "category"):
                if confidence > brand['confidence']:
                    if len(str(entity_value)) > 0:
                        brand["value"] = str(entity_value).strip()
                        brand["confidence"] = confidence
            if (entity_name == "chexi") and (entity_type == "category"):
                if confidence > chexi['confidence']:
                    if len(str(entity_value)) > 0:
                        chexi["value"] = str(entity_value).strip()
                        chexi["confidence"] = confidence
                        # 拿到检索接口的NER结果
        brand_, chexi_ = getBrandAndChexi(query)
        ner_result["brand"] = brand_
        # print(chexi["value"])
        searh_chexi = chexi_.lower()
        query_lower = str(copy.deepcopy(query)).lower()
        ner_nlp_chexi = str(chexi["value"]).lower()
        if (searh_chexi not in query_lower) and (len(ner_nlp_chexi) > 0) and (ner_nlp_chexi in ner_nlp_chexi):
            ner_result["chexi"] = chexi["value"]
        else:
            ner_result["chexi"] = chexi_
        ner_result["year"] = car_year["value"]
    except Exception as e:
        print(f"Query:{query} Ner解析出现异常！{e}")

    return ner_result


def filterKeyInfo(query: str, candidate_list: str) -> dict:
    if query is None or len(query) == 0:
        return {
            "result": ""
        }
    try:
        result = getNerResult(query)
        brand_query = result.get("brand", "")

        # 特例
        if brand_query == "MG":
            brand_query = "名爵"
            # 车型库跟线上有差异
        model_query = result.get("chexi", "")
        if model_query == "传祺GE3":
            brand_query = "传祺"
        year_query = result.get("year", "")
        json_list = json.loads(candidate_list)
        selected_cartype = ""
        for car_type in json_list:
            if len(year_query) > 0:
                if car_type.get("年款") is not None:
                    if str(car_type.get("年款")) != year_query:
                        continue
            if len(brand_query) > 0:
                if car_type.get("品牌") is not None and len(car_type.get("品牌")) > 0:
                    if str(car_type.get("品牌")).lower() in brand_query.lower() or brand_query.lower() in str(
                            car_type.get("品牌").lower()):
                        pass
                    else:
                        if query in str(car_type):
                            pass
                        else:
                            continue
            if len(model_query) > 0:
                if car_type.get("车系") is not None and len(car_type.get("车系")):
                    if (str(car_type.get("车系")).lower() in model_query.lower()) or (
                            model_query.lower() in str(car_type.get("车系")).lower()):
                        pass
                    else:
                        if query in str(car_type):
                            pass
                        else:
                            continue
            selected_cartype += str(car_type.get("车型id"))
            selected_cartype += "、"
        if len(selected_cartype) > 0:
            selected_cartype = copy.deepcopy(selected_cartype[:len(selected_cartype) - 1])
        return {
            "result": selected_cartype
        }
    except Exception as e:
        print(f"NER error {e}")
        return {
            "result": ""
        }

API_MILVUS_RETRIEVAL_URL = "https://dify-extra-api.guazi-apps.com/retrieval"
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer dify_extra_api',
    'accept':'application/json'
}

def Milvus_Retrieval(collection_name:str,query:str,topk:int = 10,score_threshold:float=0.2 ,metric_type="L2"):

    if query is None or len(query) == 0:
        return [],0.0
    time_begin = time.time()
    try:
      params = {
                "knowledge_id": f"milvus_{collection_name}",
                "query": f"{query}",
                "retrieval_setting": {
                                      "top_k": topk,
                                      "score_threshold": score_threshold,
                                      "nprobe": 50,
                                      "ef": 64,
                                      "consistency_level": "Bounded",
                                      "model_name": "bge-m3-model"
                }
              }
      time_start = time.time()
      response = requests.post(API_MILVUS_RETRIEVAL_URL, headers=HEADERS, data=json.dumps(params))
      time_end = time.time()

      return response.json()["records"],(time_end - time_start) * 1000
    except Exception as e:
      #print(f" 请求发生错误:{str(e)}")
      time_error_end = time.time()
      return [],(time_error_end-time_begin)*1000

def getCandidateInfo(search_result):
    if search_result is None or len(search_result) == 0:
        return "[]"

    key_info_list = []
    try:
        for car_type_config in search_result:
            car_config_str = car_type_config.get('content', "")
            if len(car_config_str) == 0:
                continue
            car_config_json = json.loads(car_config_str)
            key_info = {}

            car_id = car_config_json.get("车型id", "")
            factory = car_config_json.get("厂商", "")
            brand = car_config_json.get("品牌", "")
            chexi = car_config_json.get("车系", "")
            chexingmingcheng = car_config_json.get("车型名称", "")
            niankuan = car_config_json.get("年款", "")
            car_category = car_config_json.get("车辆类型", "")
            car_level = car_config_json.get("级别", "")
            car_country = car_config_json.get("国别", "")

            key_info["车型id"] = car_id
            key_info["厂商"] = factory
            key_info["品牌"] = brand
            key_info["车系"] = chexi
            key_info["车型名称"] = chexingmingcheng
            key_info["年款"] = niankuan
            key_info["车辆类型"] = car_category
            key_info["级别"] = car_level
            key_info["国别"] = car_country
            key_info_list.append(key_info)
        json_str = json.dumps(key_info_list, ensure_ascii=False)
        return {
            "result": str(json_str),
        }
    except Exception as e:
        return {
            "result": ""
        }

def getCarTypeRetrieveFinalResult(result: str, search_result) -> dict:
    if result is None or len(result) == 0:
        return {
            "result": "[]",
            "retrieve_type": "车型知识库检索"
        }

    try:
        car_types_selected = []
        if search_result is None or len(search_result) == 0:
            return {
                "result": "[]",
                "retrieve_type": "车型知识库检索"
            }
        else:
            car_ids = result.split('、')
            car_id_set = set(car_ids)
            for car_type_config in search_result:
                car_config_str = car_type_config.get('content', "")
                if len(car_config_str) == 0:
                    continue
                car_config_json = json.loads(car_config_str)

                car_id = car_config_json.get("车型id", "")
                if car_id in car_id_set:
                    car_types_selected.append(car_config_json)
            return {
                "result": json.dumps(car_types_selected, ensure_ascii=False),
                "retrieve_type": "车型知识库检索"
            }
    except Exception as e:
        car_types_selected_str = json.dumps(car_types_selected, ensure_ascii=False)
        return {
            "result": car_types_selected_str,
            "retrieve_type": "车型知识库检索"
        }

def getRetrievalResultCartypeBase(query: str,topk: int=10,score_threshold:float=0.2,metric_type="L2"):
    result ={
              "车型知识库检索"   :     "[]",
              "检索耗时"        :     0.0
    }
    chexing_result ,time_elapsed_   =   Milvus_Retrieval(collection_name="car_type_knowledgebase_chekuang", query=query, topk=topk)

    # 候选车型关键信息提取
    keyinforesult = getCandidateInfo(chexing_result)["result"]

    #相关性判定
    revelant_result = filterKeyInfo(query,keyinforesult)["result"]
    
    final_result = getCarTypeRetrieveFinalResult(revelant_result,chexing_result)["result"]

    result["车型知识库检索"]         =   copy.deepcopy(final_result)
    result["检索耗时"]              =   time_elapsed_

    return result


def getChexingkoubeFinalResult(search_result) -> dict:
    if search_result is None:
        return{
            "result":"[]",
            "retrieve_type":"车型口碑知识库检索"
        }
    else:
        content = []
        index = 0
        try:
            for item in search_result:
                index += 1
                if int(index) > 4:
                    break
                car_config_str = item.get('content', "")
                car_config_json = json.loads(car_config_str)
                content.append(car_config_json)
            json_str = json.dumps(content,ensure_ascii=False)
            return {
                "result": json_str,
                "retrieve_type":"车型口碑知识库检索"
            }
        except Exception as e:
            return {
                "result" : "[]",
                "retrieve_type": "车型口碑知识库检索"
            }


def getChexikoubeFinalResult(search_result,query) -> dict:
    if search_result is None or query is None or len(query) == 0:
        return{
            "result":"[]",
            "retrieve_type":"车系口碑知识库检索"
        }
    else:
        try:
            #获取用户问题中的车系
            chexi_name_in_query = ""
            brand_,chexi_ = getBrandAndChexi(query)
            chexi_name_in_query = chexi_
            if chexi_name_in_query == "北京BJ40":
                chexi_name_in_query = "北京越野BJ40"
            # 识别的品牌中增加了（进口）
            elif (chexi_name_in_query not in query) and chexi_name_in_query.find("(进口)") != -1:
                chexi_name_in_query = chexi_name_in_query.replace("(进口)","")

            content = []
            index   = 0
            valid_num = 0
            for item in search_result:
                index += 1
                if valid_num > 4:
                    break

                car_config_str   =   item.get('content', "")
                car_config_json = json.loads(car_config_str)

                chexi_koubei_content = item.get('content', "").lower()
                if chexi_koubei_content.find(chexi_name_in_query.lower()) != -1:
                    # data = {
                    #     "车系口碑知识": str(item["content"])
                    # }
                    content.append( car_config_json )
                    valid_num += 1
                    #content += "\n"
                else:
                    pass
            json_str = json.dumps(content,ensure_ascii=False)
            return {
                "result": json_str,
                "retrieve_type":"车系口碑知识库检索"
            }
        except Exception as e:
            #print(f"异常{e}")
            return {
                "result": "[]",
                "retrieve_type":"车系口碑知识库检索"
            }
def getBrandkoubeFinalResult(search_result,query) -> dict:
    if search_result is None:
        return{
            "result":"[]",
            "retrieve_type":"汽车口碑知识库检索"
        }
    else:
        try:
            #获取用户问题中的车系
            chexi_name_in_query = ""
            brand_,chexi_ = getBrandAndChexi(query)
            chexi_name_in_query = chexi_
            if chexi_name_in_query == "北京BJ40":
                chexi_name_in_query = "北京越野BJ40"

            content = []
            index   = 0
            valid_num = 0
            for item in search_result:
                index += 1
                if valid_num > 4:
                    break
                #print(item)

                car_config_str = item.get('content', "")
                car_config_json = json.loads(car_config_str)

                chexi_koubei_content = item.get('content', "").lower()
                #chexi_koubei_content = str(item["content"]).lower()

                if chexi_koubei_content.find(chexi_name_in_query.lower()) != -1:
                    # data = {
                    #     "汽车品牌口碑知识": str(item["content"])
                    # }
                    content.append( car_config_json )
                    valid_num += 1
                    #content += "\n"
                else:
                    pass
            json_str = json.dumps(content,ensure_ascii=False)
            return {
                "result": json_str,
                "retrieve_type":"汽车口碑知识库检索"
            }
        except Exception as e:
            #print(f"异常{e}")
            return {
                "result": "[]",
                "retrieve_type":"汽车口碑知识库检索"
            }

def getRetrieveResultChexingKoubei(query:str,topk:int=10,score_threshold:float=0.2,metric_type="L2"):
    result ={
        "车型口碑知识库检索": "[]",
        "检索耗时" : 0.0
    }
    koubei_chexing_result,time_elapsed_ = Milvus_Retrieval(collection_name="car_type_knowledge_base_koubei_withscore", query=query, topk=topk)

    #获取车型口碑最终结果
    koiubei_chexing_final_result = getChexingkoubeFinalResult(koubei_chexing_result)["result"]

    result["车型口碑知识库检索"] = copy.deepcopy(koiubei_chexing_final_result)
    result["检索耗时"] = time_elapsed_
    return result

def getRetrieveResultChexiKoubei(query:str,topk:int=10,score_threshold:float=0.2,metric_type="L2"):
    result ={
        "车系口碑知识库检索":"[]",
        "检索耗时":0.0
    }
    koubei_chexi_result,time_elapsed_ = Milvus_Retrieval(collection_name="car_type_chexikoubei_knowledgebase_new", query=query, topk=topk)

    koubei_chexi_final_result = getChexikoubeFinalResult(koubei_chexi_result,query)["result"]

    result["车系口碑知识库检索"] = copy.deepcopy(koubei_chexi_final_result)
    result["检索耗时"] = time_elapsed_
    return result

def getRetrieveResultPinpaiKoubei(query:str,topk:int=10,score_threshold:float=0.2,metric_type="L2"):
    result = {
        "品牌口碑知识库检索": "[]",
        "检索耗时": 0.0
    }
    koubei_brand_result, time_elapsed_ =   Milvus_Retrieval( collection_name="brand_koubei_knowledgebase",query=query, topk=topk )

    koubei_brand_final_result = getBrandkoubeFinalResult(koubei_brand_result,query)["result"]
    result["品牌口碑知识库检索"]          =   copy.deepcopy(koubei_brand_final_result)
    result["检索耗时"]                  =  time_elapsed_
    return result

def BochaSearch(query:str,topk:int=10):
    if query is None or len(query) == 0:
        return [],0.0

    web_search_api_key =  "sk-c12f4e3162ad493e83fdb50511d4660f"
    websearch_url      =  "https://api.bochaai.com/v1/web-search"
    headers            = {
                            'Content-Type': 'application/json',
                            'Authorization': f'Bearer {web_search_api_key}',
                          }
    time_begin = time.time()
    try:
        params = {
                "query": f"{query}",
                "summary": True,
                "freshness": "oneYear",
                "count": topk,
                "include":"autohome.com.cn|dongchedi.com|xin.com|renrenche.com",
                "page": 1
            }
        time_start = time.time()
        response = requests.post(websearch_url, headers=headers, data=json.dumps(params))
        time_end = time.time()
        json_data = response.json()
        return json_data,(time_end-time_start)*1000
    except Exception as e:
        time_error_end = time.time()
        return [],(time_error_end-time_begin)*1000


def getBoChaFinalResult(status_code: int, body) -> dict:
    if status_code is None:
        return {
            "result": "[]",
            "retrieve_type": "联网检索"
        }
    if status_code != 200:
        return {
            "result": "[]",
            "retrieve_type": "联网检索"
        }
    else:
        search_result = ""
        try:
            search_result = body
            search_pages = search_result["data"]["webPages"]["value"]

            content = []
            for page in search_pages:
                summary = page["summary"]
                content.append(copy.deepcopy(summary))
                # content += "\n\n"
            json_str = json.dumps(content, ensure_ascii=False)
            return {

                # "result":str(search_result["data"]["webPages"]["value"]),
                "result": json_str,
                "retrieve_type": "联网检索"
            }
        except:
            return {
                "result": "[]",
                "retrieve_type": "联网检索"
            }


def getRetrieveResultWebSearchKoubei(query:str,topk:int=10):
    result = {
        "联网检索" :  "[]",
        "检索耗时" :  0.0
    }

    # websearch_result, time_elapsed_ = BochaSearch(query=query,topk=topk)
    # status_code = websearch_result["code"]
    # websearch_final_result = getBoChaFinalResult(status_code,websearch_result)["result"]

    # result["联网检索"] = copy.deepcopy(websearch_final_result)
    # result["检索耗时"] = time_elapsed_
    return result



def llm_select_car_knowledge_base(query: str) -> str:
    """
    根据用户问题判断依赖的知识库类型，并返回相似问题索引。
    使用 ChatOpenAI 调用大模型，超时 10 秒返回空结果。
    """
    # 加载系统提示词文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    instruction_path = os.path.join(script_dir, "car_knowledge_base_select_instruction")
    try:
        with open(instruction_path, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print(f"知识库模型选择提示词文件未找到: {instruction_path}")
        return ""

    # 用 query 替换提示词中的变量
    system_prompt = system_prompt.replace("{question}", query)
    
    decoded = base64.b64decode("N2IyMzQ1MjItZmY0ZC00ODBhLThmZmEtNzMwYjUxYWFmYTI0").decode("utf-8")

    # 初始化 ChatOpenAI（兼容 OpenAI 的 API）
    llm = ChatOpenAI(
        api_key=f"{decoded}",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        model="ep-20260304210402-gw4fj",#"seed2.0-lite",
        request_timeout=10,
        extra_body={"thinking": {"type": "disabled"}},  # 禁用推理模式，直接输出答案
    )

    start_ms = time.perf_counter() * 1000
    try:
        response = llm.invoke(system_prompt)
        end_ms = time.perf_counter() * 1000
        elapsed_ms = round(end_ms - start_ms, 2)
        #print(f"大模型调用耗时: {elapsed_ms} ms")
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        end_ms = time.perf_counter() * 1000
        elapsed_ms = round(end_ms - start_ms, 2)
        return ""

def get_best_matched_examples(query: str) -> dict:
    """
    根据用户问题从参考问题库中找出问法或句式最相似的问题。
    """
    time_begin = time.time()
    llm_selcet_knowledge_base_result = llm_select_car_knowledge_base(query)
    result = select_best_matched_examples(llm_selcet_knowledge_base_result)
    time_end = time.time()
    time_elapsed = (time_end - time_begin)*1000

    result_return = {
            "模型知识库选择": result.get("retrieve_type",""),
            "模型选库耗时": time_elapsed,
            "few_shot": result.get("few_shot","")
        }
    return result_return


def get_car_knowlege_merge_result(car_type_data:str,koubei_data:str,internet_search_data:str,recommend_search_type:str,few_shot:str,chexi_koubei_data:str,brand_koubei_data:str) -> dict:
    if recommend_search_type.find("无需知识库检索") != -1:
        return {
            "knowledge_base": "[]",
            "retrieve_type":"无需汽车知识库检索",
            "few_shot":few_shot
        }
    elif recommend_search_type.find("车型知识库检索") != -1:
        if car_type_data is None:
            return {
                "knowledge_base": "[]",
                "retrieve_type":"车型知识库检索",
                "few_shot":few_shot
            }
        else:
            return {
                "knowledge_base": copy.deepcopy(car_type_data),
                 "retrieve_type":"车型知识库检索",
                "few_shot":few_shot
            }
    elif recommend_search_type.find("车型口碑知识库检索") != -1:
        if koubei_data is None:
            return {
                   "knowledge_base": "[]",
                   "retrieve_type":"车型口碑知识库检索",
                   "few_shot":few_shot
            }
        else:
            return {
                   "knowledge_base": copy.deepcopy(koubei_data),
                   "retrieve_type":"车型口碑知识库检索",
                   "few_shot":few_shot
            }    
    elif recommend_search_type.find("联网检索") != -1:
        if internet_search_data is None: # 出现了异常
            return {
                   "knowledge_base": "[]",
                   "retrieve_type":"联网检索",
                   "few_shot":few_shot
            }
        else:
            return {
                   "knowledge_base": copy.deepcopy(internet_search_data),
                   "retrieve_type":"联网检索",
                   "few_shot":few_shot
            }
    elif recommend_search_type.find("车系口碑知识库检索") != -1: 
        if internet_search_data is None: # 出现了异常
            return {
                   "knowledge_base": "[]",
                   "retrieve_type":"车系口碑知识库检索",
                   "few_shot":few_shot
            }
        else: 
            return {
                   "knowledge_base": copy.deepcopy(chexi_koubei_data),
                   "retrieve_type":"车系口碑知识库检索",
                   "few_shot":few_shot
            }
    elif recommend_search_type.find("汽车品牌口碑知识库检索") != -1:
        if brand_koubei_data is None: # 出现了异常
            return {
                   "knowledge_base": "[]",
                   "retrieve_type":"汽车品牌口碑知识库检索",
                   "few_shot":few_shot
            }
        else: 
            return {
                   "knowledge_base": copy.deepcopy(brand_koubei_data),
                   "retrieve_type":"汽车品牌口碑知识库检索",
                   "few_shot":few_shot
            }
    else:
        return {
            "knowledge_base": "[]",
            "retrieve_type":"无需汽车知识库检索",
            "few_shot":few_shot
    }
def get_car_knowledge_base_search_result(query: str) -> dict:
    if query is None or len(query) == 0:
        return {
                    "car_type_data"        :  "[]",   # 车型配置检索结果
                    "cartype_config_retrieval_time"      :  0.0,
                    "koubei_data"          :  "[]",   # 车型口碑结果
                    "cartype_koubei_retrieval_time"   :  0.0,
                    "internet_search_data" :  "[]",   # 联网检索结果
                    "websearch_time"           :  0.0,
                    "chexi_koubei_data"    :  "[]",   # 车系口碑检索结果
                    "chexi_koubei_retrieval_time"   :  0.0,
                    "brand_koubei_data"    :  "[]",   # 品牌口碑检索结果
                    "brand_koubei_retrieval_time"   :  0.0,
                    "selected_knowledge_base": "",
                    "selected_knowledge_base_time": 0.0,
                    "few_shot": {}
             }
    # 分别使用车型知识库检索、车型口碑知识库检索、车系口碑知识库检索、品牌口碑知识库检索和联网检索，并返回每一种检索的时间（ms）
    # 启动四个线程分别进行
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    results = []
    # 添加车型知识库检索 done
    future_cartypebase = executor.submit(getRetrievalResultCartypeBase, query, 3)
    results.append(future_cartypebase)

    # done
    future_chexingkoubei  = executor.submit(getRetrieveResultChexingKoubei,query,2)
    results.append(future_chexingkoubei)

    # doing
    future_chexikoubei = executor.submit(getRetrieveResultChexiKoubei,query,2)
    results.append(future_chexikoubei)

    future_pinpaikoubei = executor.submit(getRetrieveResultPinpaiKoubei,query,2)
    results.append(future_pinpaikoubei)

    future_websearch = executor.submit(getRetrieveResultWebSearchKoubei,query,4)
    results.append(future_websearch)

    future_best_matched_examples = executor.submit(get_best_matched_examples,query)
    results.append(future_best_matched_examples)

    result_return = {
                    "car_type_data"        :  "",   # 车型配置检索结果
                    "cartype_config_retrieval_time"      :  0.0,
                    "koubei_data"          :  "",   # 车型口碑结果
                    "cartype_koubei_retrieval_time"   :  0.0,
                    "internet_search_data" :  "",   # 联网检索结果
                    "websearch_time"           :  0.0,
                    "chexi_koubei_data"    :  "",   # 车系口碑检索结果
                    "chexi_koubei_retrieval_time"   :  0.0,
                    "brand_koubei_data"    :  "",   # 品牌口碑检索结果
                    "brand_koubei_retrieval_time"   :  0.0,
                    "selected_knowledge_base": "",
                    "selected_knowledge_base_time": 0.0,
                    "few_shot": ""
             }

    for future in concurrent.futures.as_completed(results):
        result = future.result()
        # get_best_matched_examples 返回结构: {"模型知识库选择", "模型选库耗时", "few_shot"}
        if "模型知识库选择" in result:
            result_return["selected_knowledge_base"] = result["模型知识库选择"]
            result_return["selected_knowledge_base_time"] = round(result["模型选库耗时"], 2)
            result_return["few_shot"] = result.get("few_shot", "")
        # 其他检索返回结构: {检索类型名, "检索耗时"}
        elif "车型知识库检索" in result:
            result_return["cartype_config_retrieval_time"] = round(result["检索耗时"], 3)
            result_return["car_type_data"] = result["车型知识库检索"]
        elif "车型口碑知识库检索" in result:
            result_return["cartype_koubei_retrieval_time"] = round(result["检索耗时"], 2)
            result_return["koubei_data"] = result["车型口碑知识库检索"]
        elif "车系口碑知识库检索" in result:
            result_return["chexi_koubei_retrieval_time"] = round(result["检索耗时"], 2)
            result_return["chexi_koubei_data"] = result["车系口碑知识库检索"]
        elif "品牌口碑知识库检索" in result or "汽车口碑知识库检索" in result:
            retrieve_key = "品牌口碑知识库检索" if "品牌口碑知识库检索" in result else "汽车口碑知识库检索"
            result_return["brand_koubei_retrieval_time"] = round(result["检索耗时"], 2)
            result_return["brand_koubei_data"] = result[retrieve_key]
        elif "联网检索" in result:
            result_return["websearch_time"] = round(result["检索耗时"], 2)
            result_return["internet_search_data"] = result["联网检索"]
    # 关闭线程池
    executor.shutdown()


    output = get_car_knowlege_merge_result(result_return.get("car_type_data",""),result_return.get("koubei_data",""),result_return.get("internet_search_data",""),result_return.get("selected_knowledge_base",""),result_return.get("few_shot",""),result_return.get("chexi_koubei_data",""),result_return.get("brand_koubei_data",""))

    knowledge_base   =   output.get("knowledge_base",'[]')
    retrieve_type    =   output.get("retrieve_type","")
    few_shot         =   output.get("few_shot","")
    
    if retrieve_type.find("车型知识库检索") != -1 and knowledge_base == '[]':
        car_config_websearch_result = websearch_car_config_result(query,10)
        return {
            "data": car_config_websearch_result.get("websearch_knowledge_base",""),
            "retrieve_type": car_config_websearch_result.get("retrieve_type",""),
            "few_shot": few_shot
        }

    elif retrieve_type.find("联网检索") != -1:
        websearch_result = websearch_result(query,10)
        return {
            "data": car_config_websearch_result.get("websearch_knowledge_base",""),
            "retrieve_type": car_config_websearch_result.get("retrieve_type",""),
            "few_shot": few_shot
        }
    else:
       return  {
           "data": knowledge_base,
           "retrieve_type": retrieve_type,
           "few_shot": few_shot
       }


def get_car_knowledge_base_search_result_main(query: str):
    result = get_car_knowledge_base_search_result(query)
    return result

if __name__ == "__main__":
    # query = "丰田汉兰达口碑怎么样？"
    # result = main(query)
    # print(result)
    query = "宝马X3 2029款口碑怎么样？"
    result = get_car_knowledge_base_search_result_main(query)
    print(result)
# 利用 llm (spark)判断query所属类别，实现对链路对选择
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from langchain.chains import LLMChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langsmith import traceable
from NL2SQL import nl2sql
from langchain_community.llms import SparkLLM
from _settings import conf

appid = conf['spark_appid']
api_secret = conf['spark_api_secret']
api_key = conf['spark_api_key']
gpt_url = conf['spark_gpt_url']
domain = conf['spark_domain']




# 使用 ChatSparkLLM 类
llm = SparkLLM(
    sparkai_url=gpt_url,
    # 星火认知大模型调用秘钥信息，请前往讯飞开放平台控制台（https://console.xfyun.cn/services/bm35）查看
    # SPARKAI_APP_ID = '0bcea58d',
    spark_app_id=appid,
    spark_api_secret=api_secret,
    spark_api_key=api_key,
    # 星火认知大模型Spark Max的domain值，其他版本大模型domain值请前往文档（https://www.xfyun.cn/doc/spark/Web.html）查看
    sparkai_domain=domain
)


def intent_recognition(question: str) -> str:
    '''
            该方法的目标是对用户提出的问题进行意图识别，随后进行对应的路由分支
            意图的类型，暂时分为《法律》、《中标信息》、《企业关系》
        :param question:用户提出的问题
        :return:对应的意图
        '''

    template = """
        你是一名政府企业的招标投标领域的专家，对招投标领域有丰富的行业经验。
        并且你擅长对用户提出的问题进行分类，目前提供选择的类型有3种<招标信息获取、招标疑问解答、投标建议提供、智能标书生成>，你只允许从这4种类型中选择，并且只能选择其中1种。
        必须回复分类类型，如果不属于这四种类型，请回复《无》，回复的字数不能超过10个字。


        使用以下格式：
        问题：用户提问的问题。
        结果是：你思考出来的答案

        你可以参考以下例子：
        <用户的问题：请帮助我查找近期发布的招标公告，特别是与[南京市]相关的项目。
        结果是：招标信息获取。>
        <用户的问题：请展示所有与[交通水利]相关的最新招标公告，并按发布时间进行排序。
        结果是：招标信息获取。>
        <能否帮我找到与[特定行业]相关的重大项目招标信息，并按项目规模筛选结果？
        结果是：招标信息获取。>
        <2024年南京一共招了多少标？
        结果是：招标信息获取。>
        <请提供[特定项目]的招标信息包括招标人、联系方式、地址等。
        结果是：招标信息获取。>
        <用户的问题：能提供《合肥市康众路道路维修建设第一期工程》的中标企业是谁吗？
        结果是：招标疑问解答>
        <用户问题：上海市青年宿舍的外墙维修项目已经在政府网站公告了吗？
        结果是：招标疑问解答>
        <用户问题：请基于历史中标数据，分析该项目的中标价格区间，并提供合理的投标报价建议。
        结果是：投标建议提供>
        <用户问题：请提供过去一年中标供应商的报价趋势，并给出该项目的最佳投标报价范围。
        结果是：投标建议提供>
        <用户问题：根据以往的中标结果，分析哪些因素在该项目中最为关键，并提供相关的投标策略。
        结果是：投标建议提供>

        好的，请根据用户提供的问题做出回复。

        用户的问题：{input}
        结果是：
        """
    prompt = PromptTemplate(template=template, input_variables=['input'])
    llm_chain = prompt | llm
    result = llm_chain.invoke({"input": question})
    # print(type(result))
    return result

def route(intention: str, question: str):
    '''
    根据意图路由到对应思维链
    中标信息的链路进行NL2SQL
    :param intention:用户的意图
    :return:
    '''
    if intention:  # 检查 intention 是否为 None 或空
        if '招标信息获取' in intention:
            nl2sql(question)

        elif '招标疑问解答' in intention:
            print('该功能等待实现')
        elif '供应商' in intention:
            print('该功能等待实现')
        else:
            print('用户意图不明，请让客户重新输入')
    else:
        print("intention is None or empty, skipping")




    # 问题




if __name__ == '__main__':
    while True:
        question = input('您好，我是招标投标的AI助手，很高兴能为您服务，请问您要咨询什么问题？如果需要退出服务，请输入“退出”：')

        if question == '退出':
            print('好的，期待您的下次咨询')
            break

        # 意图识别
        intention = intent_recognition(question)
        route(intention, question)
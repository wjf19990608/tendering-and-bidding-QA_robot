from operator import itemgetter

import os

import mysql.connector
from mysql.connector import Error

from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
# from langchain_community.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langsmith import traceable

from _settings import conf

# 数据库信息
db_host = conf['db_host']
db_user = conf['db_user']
db_password = conf['db_password']
db_port = conf['db_port']
db_name = conf['db_name']
# 设置你的 OpenAI API 密钥
openai_api_key = os.getenv("OPENAI_API_KEY","bacai-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtb2JpbGUiOiIxODc5NTc4MDM4MSIsImV4cCI6NDg0NzU4NzU3MDA3NCwiaWF0IjoxNzI1NTIzNTcwfQ.hegBUj1R9E-vzv9h4CjrKw5obWEfp6kKb_bllTDRtnM")
openai_api_base = os.getenv("OPENAI_API_BASE", "https://api.baicaigpt.com/v1")
llm = ChatOpenAI(openai_api_key="bacai-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtb2JpbGUiOiIxODc5NTc4MDM4MSIsImV4cCI6NDg0NzU4NzU3MDA3NCwiaWF0IjoxNzI1NTIzNTcwfQ.hegBUj1R9E-vzv9h4CjrKw5obWEfp6kKb_bllTDRtnM",
                 model='gpt-3.5-turbo',
                 openai_api_base="https://api.baicaigpt.com/v1")
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}")



# openai.api_key = 'bacai-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtb2JpbGUiOiIxODc5NTc4MDM4MSIsImV4cCI6NDg0NzU4NzU3MDA3NCwiaWF0IjoxNzI1NTIzNTcwfQ.hegBUj1R9E-vzv9h4CjrKw5obWEfp6kKb_bllTDRtnM'
# openai.api_base = 'https://api.baicaigpt.com/v1'
# def llm(prompt: str) -> str:
#     openai.api_key = openai_api_key  # 设置 OpenAI 的 API 密钥
#     openai.api_base = openai_api_base # 如果你使用自定义的 API 基础 URL
#
#     # 使用 GPT-3.5-turbo 生成 SQL 查询
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are an AI that helps generate SQL queries based on user requests."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#
#
#
#     # 提取模型生成的 SQL 查询
#     sql_query = response.choices[0].message['content']
#     print(sql_query)
#     return sql_query



@traceable
def nl2sql(question:str)->str:

    """
    该方法是将用户的问题转变为SQL语句，随后DB库执行SQL语句，将结果拼接到Prompt中再度返回给llm，让llm回复
    :param question: 用户提出的问题
    :return: SQL查询的结果
    """
    try:
        connection = mysql.connector.connect(
            host=db_host,  # 数据库主机
            user=db_user,  # 数据库用户名
            password=db_password,  # 数据库密码
            database=db_name  # 数据库名称
        )
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

    if connection.is_connected():
        print("Successfully connected to the MySQL database")

        # ======================tools=======================
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()
        # ====================NL2SQL提示词========================
        SQL_PREFIX = """You are an agent designed to interact with a SQL database.
            Given an input question, create a syntactically correct SQLite query to run, then look at the results of the query and return the answer.
            The answer is sourced from the Content in AIMessage.
            Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
            You can order the results by a relevant column to return the most interesting examples in the database.
            Never query for all the columns from a specific table, only ask for the relevant columns given the question.
            You have access to tools for interacting with the database.
            Only use the below tools. Only use the information returned by the below tools to construct your final answer.
            You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.

            DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

            To start you should ALWAYS look at the tables in the database to see what you can query.
            Do NOT skip this step.
            Then you should query the schema of the most relevant tables."""

        system_message = SystemMessage(content=SQL_PREFIX)
        human_message = HumanMessage(content=question)
        # ===================NL2SQL的Chain调用====================
        agent_executor = create_react_agent(llm, tools, messages_modifier=system_message)
        text = agent_executor.invoke(
        {"messages": [human_message]})

        print(text)
        try:
            query = text['messages'][2].content.split('\n')[1].split(':')[-1]+ ';'
        except Exception as e:
            print(f"Error while NL2SQL: {e}")


        # ====================初始化SQL数据库执行器======================
        execute_query = QuerySQLDataBaseTool(db=db)
        # ===================解决客户问题的提示词======================
        sql_result = text['messages'][-1].content
        answer_prompt = PromptTemplate.from_template(
            """Given the following user question, corresponding SQL query, and SQL result, answer the user question.

            Question: {question}
            SQL Query: {query}
            SQL Result: {result}+{sql_result}
            Answer: """,

        )

        # ======================解决客户问题的Chain=====================
        chain = (
                RunnablePassthrough.assign(
                    result=itemgetter("question") | execute_query
                ) | answer_prompt
                | llm | StrOutputParser()
        )
        # 输出SQl查询的结果
        result = chain.invoke({'question': question,
                               'query': query,
                               'sql_result':sql_result})
        # 输出查询结果看一下
        print(result)

        if connection.is_connected():
            connection.close()
    return result


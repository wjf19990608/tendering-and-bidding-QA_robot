import bs4
import os
os.environ["OPENAI_API_KEY"] = 'ab78b1a21a614ba1ade36ba88b172893'
os.environ["OPENAI_API_BASE"] = "https://api.lingyiwanwu.com/v1"
os.environ["USER_AGENT"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
from langchain_community.document_loaders import WebBaseLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from langchain.prompts.prompt import PromptTemplate

from sentence_transformers import SentenceTransformer

# 文本导入
loader = WebBaseLoader(
    web_path="https://www.mohrss.gov.cn/SYrlzyhshbzb/zcfg/flfg/201601/t20160119_232110.html",
    bs_kwargs=dict(parse_only=bs4.SoupStrainer(
            class_=("TRS_PreAppend")
        ))
)
docs = loader.load()

# 文本切割
text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
)
splits = text_splitter.split_documents(docs)

# 向量化存储
db = Chroma.from_documents(
    documents=splits,
    embedding=OpenAIEmbeddings(),
    persist_directory="./chroma_db")


# prompt
prompt_template_str = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.

Question: {question} 

Context: {context} 

Answer:
"""
prompt_template = PromptTemplate.from_template(prompt_template_str)

# 链接本地向量数据库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=OpenAIEmbeddings()
)

# 构建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

# 查询
docs = retriever.invoke("劳动者解除劳动合同需要提前多久告诉人事？")


print()
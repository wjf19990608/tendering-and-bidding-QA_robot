
from sentence_transformers import SentenceTransformer


model_name = 'all-MiniLM-L6-v2'
transformer_model = SentenceTransformer(model_name)

# 创建 LangChain 嵌入对象


# 用户问题输入
def get_query():
    user_query = input("Please enter your question: ")
    return user_query

# 向量化
def query2embedding(query : str):
    query_embedding = transformer_model.encode(query)
    return query_embedding

# NL2SQl
def query2SQl(query : str):
    pass
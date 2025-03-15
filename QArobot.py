# 基于langchain的招投标智能问答机器人
# from query_input import get_query,query2embedding
from chain_selector import select_chain



# 用户问题输入
# user_query = get_query()

# 链路选择

question = "Can I track my shipment?"
select_chain(question)

# 生成answer


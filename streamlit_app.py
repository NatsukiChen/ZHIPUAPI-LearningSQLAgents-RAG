import streamlit as st
from langchain_openai import ChatOpenAI
import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableBranch, RunnablePassthrough
import sys
sys.path.append("Embedding.ipynb") # 将父目录放入系统路径中
from zhipuai_embedding import ZhipuAIEmbeddings
from langchain_community.vectorstores import Chroma

def get_retriever():
    # 定义 Embeddings
    embedding = ZhipuAIEmbeddings()
    # 向量数据库持久化路径
    persist_directory = 'data_base/vector_db'
    # 加载数据库
    vectordb = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding
    )
    return vectordb.as_retriever()

def combine_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs["context"])

def get_qa_history_chain():
    retriever = get_retriever()
    llm = ChatOpenAI(base_url = "https://open.bigmodel.cn/api/paas/v4",
                 api_key = zp_api_key,
                 model = "glm-5.3",
                 temperature=0)

    condense_question_system_template = (
        "请根据聊天记录总结用户最近的问题，"
        "如果没有多余的聊天记录则返回用户的问题。"
    )
    # 带有信息压缩的检索
    # 由于用户在多轮对话中的提问往往是指代不清的（如：“那它的缺点呢？”），系统需要结合 {chat_history} 把用户的当前问题改写成独立、完整的问题
    condense_question_prompt = ChatPromptTemplate([
            ("system", condense_question_system_template),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ])

    retrieve_docs = RunnableBranch(
        (lambda x: not x.get("chat_history", False), (lambda x: x["input"]) | retriever, ),
        condense_question_prompt | llm | StrOutputParser() | retriever,
    )

    # 向问答链注入上下文与历史记录
    system_prompt = (
        "你是一个问答任务的助手。 "
        "请使用检索到的上下文片段回答这个问题。 "
        "如果你不知道答案就说不知道。 "
        "请使用简洁的话语回答用户。"
        "\n\n"
        "{context}"
    )

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ]
    )
    # 提问-上下文-大模型根据上下文回答 的链条
    # ❗注意，这里没有 提问 -> 检索 的步骤，意味着 qa_chain 并没有连接到 vectorstore
    qa_chain = (
        RunnablePassthrough().assign(context=combine_docs)
        | qa_prompt
        | llm
        | StrOutputParser()
    )

    # qa_chain 在这里才接上了 vectorstore: 代码在 context 处直接用了另一个定义好的检索分支chain: retrieve_docs
    qa_history_chain = RunnablePassthrough().assign(
        context = retrieve_docs,    # context 是经过信息压缩检索而检索到的相关上下文
        ).assign(answer=qa_chain)
    return qa_history_chain

# 利用 LangChain 的 .stream 方法实现了流式输出（打字机效果）。它遍历底层组件吐出的数据块，专门截取属于最终回答 answer 的部分实时返回给前端 UI
def gen_response(chain, input, chat_history):
    response = chain.stream({
        "input": input,
        "chat_history": chat_history
    })
    for res in response:
        if "answer" in res.keys():
            yield res["answer"]

# Streamlit 应用程序界面
def main():
    st.markdown('### 🦜🔗 SQL 学习助手')

    # 1. 在左侧边栏添加 API Key 输入框
    with st.sidebar:
        st.markdown("## ⚙️ 设置")
        user_api_key = st.text_input("请输入你的智谱 API Key", type="password")
        st.markdown("[获取智谱 API Key](https://bigmodel.cn/usercenter/apikeys)")

    # 2. 拦截检查：如果没有输入 Key，则停止运行后续代码并提示用户
    if not user_api_key:
        st.warning("👈 请先在左侧边栏输入智谱 API Key 以启动应用")
        st.stop()  

    # 3. 将用户输入的 Key 动态写入环境变量，供后续的 llm 和 embedding 调用
    os.environ["ZHIPU_API_KEY"] = user_api_key

    # 4. 初始化会话状态（对话历史与问答链）
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # 注意：这里的 get_qa_history_chain() 会在用户输入 Key 之后才执行，
    # 因此能够成功读取到上面 os.environ 刚刚写入的 ZHIPU_API_KEY
    if "qa_history_chain" not in st.session_state:
        st.session_state.qa_history_chain = get_qa_history_chain()
        
    # 5. 创建固定高度的对话气泡容器
    messages = st.container(height=550)
    
    # 6. 渲染历史对话
    for message in st.session_state.messages:
        with messages.chat_message(message[0]):
            st.write(message[1])
            
    # 7. 监听底部输入框并处理新问题
    if prompt := st.chat_input("请提问关于 SQL 的问题..."):
        # 将用户输入渲染并保存
        st.session_state.messages.append(("human", prompt))
        with messages.chat_message("human"):
            st.write(prompt)

        # 传递给问答链生成流式响应
        answer = gen_response(
            chain=st.session_state.qa_history_chain,
            input=prompt,
            chat_history=st.session_state.messages
        )
        
        # 将 AI 回复以打字机效果渲染并保存
        with messages.chat_message("ai"):
            output = st.write_stream(answer)
        st.session_state.messages.append(("ai", output))


if __name__ == "__main__":
    main()

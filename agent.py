from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AnyMessage, AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from tools import calculator
from prompts import system_prompt, qc_prompt


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]



class Agent:
    def __init__(self, model_name : str, tools : list, system : str = '', use_qc : bool = False):
        self.system = system
        self.llm = ChatOllama(model=model_name, temperature=0).bind_tools(tools)

        graph = StateGraph(AgentState)

        graph.set_entry_point('BigBuck5')
        graph.add_node('BigBuck5', self.call_model)
        graph.add_node('tools', ToolNode(tools))
        graph.add_edge("tools", "BigBuck5")


        if use_qc:
            self.qc_llm = ChatOllama(model=model_name, temperature=0)
            graph.add_node('quality_control', self.evaluate_response)
            graph.add_conditional_edges('BigBuck5', tools_condition, {'tools':'tools', '__end__': 'quality_control'})
            graph.add_conditional_edges('quality_control', self.check_quality, {'APROVADO': END, 'REJEITADO': 'BigBuck5'})
        
        else:
            graph.add_conditional_edges('BigBuck5', tools_condition)


        memory = MemorySaver()
        self.app = graph.compile(checkpointer=memory)



    def call_model(self, state : AgentState):
        messages = state["messages"]
        
        if self.system and not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system)] + messages
            
        response = self.llm.invoke(messages)
        return {"messages": [response]}
    

    def evaluate_response(self, state: AgentState):
        messages = state["messages"]
        ultima_resposta = messages[-1].content

        avaliacao = self.qc_llm.invoke([HumanMessage(content=f'{qc_prompt} \n A resposta a avaliar é esta: {ultima_resposta}')])
        return {'messages': [AIMessage(content=avaliacao.content)]}


    def check_quality(self, state: AgentState):
        avaliacao = state['messages'][-1].content
        if 'APROVADO' in avaliacao.upper():
            return 'APROVADO'
        else:
            return 'REJEITADO'
        

if __name__ == '__main__':
    tools_construidas = [calculator] 
    BigBuck5 = Agent(model_name='gemma4:e2b',
                   tools=tools_construidas,
                   system=system_prompt,
                   use_qc=False)
    
    print('💸 BigBuck5 Financial Agent is online!')
    print("-" * 100)
    print('Ask me about your expenses, budget, savings or financial habits.')
    print("Type 'exit' to stop the assistant.")

    config_estado = {"configurable": {"thread_id": "conversa_1"}}

    while True:
        pergunta = input('Escreva aqui:')
        if pergunta.strip().lower() in ["exit", "quit", "sair"]:
            print("BigBuck5: Shutting down... See you next time! :) ")
            break
            
        novo_estado = {"messages": [HumanMessage(content=pergunta)]}

        resposta_final = ''
        
        try:
            for event in BigBuck5.app.stream(novo_estado, config=config_estado):
                for key, value in event.items():
                    if key == "tools":
                        print("BigBuck5 is checking the numbers...")
                    elif key == "BigBuck5":
                        resposta_final = value["messages"][-1].content
                    elif key == "quality_control":
                        print("\n BigBuck5 is reviewing the answer quality...")
        except Exception as e:
            print('BigBuck5: Sorry, something went wrong.')
            print(f'Technical error: {e}')
            
        if resposta_final: 
            print(f"BigBuck5: {resposta_final}")
        else:
            print('BigBuck5: I could not generate an answer. Please try again')
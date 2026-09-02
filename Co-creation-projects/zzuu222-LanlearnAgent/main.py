from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM
from src.agents.conversation import SpeakTeacherAgent

#Загрузить переменные среды
load_dotenv()
llm = HelloAgentsLLM()

#Входящие параметры: язык, сложность, предпочтения.
#Варианты сложности: начальный, начинающий, средний, продвинутый.
# Варианты предпочтений: технологии, повседневная жизнь и т. д.
talkagent = SpeakTeacherAgent(llm,"Английский","Средний","Технологии")
result = talkagent.letstalk()



from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import json, os



class Node():
    def __init__(self, message):
        self.message = message 
        self.children = [] # list of [child_node, criteria_for_this_node]


class Dialogue_Tree():
    def __init__(self, root):

        self.set_up_gpt()

        # self.main_chat = ChatOpenAI()
        self.validater = ChatOpenAI()
        self.chooser = ChatOpenAI()

        self.node = root
        self.current_response = None
        self.current_question = None
        self.chat_history = []


    def set_up_gpt(self):
        ###------Set Up OpenAI Environment------###
        # OpenAI API Key
        # Opening JSON file
        f = open("/Users/aarmanpannu/Desktop/CS/HRI/my_API_key.json")

        # returns JSON object as a dictionary
        key_information = json.load(f)
        api_key = key_information['keys'][0]['api_key']

        os.environ["OPENAI_API_KEY"] = api_key


    def start_dialogue(self):
        """
        Main function for dialogue 

        @ every msg, we will
        1) ask a msg from the DT
        2) see if it makes sense
            if not, rephrase and start 1
        3) store that msg in its chat_history
        4) determine which path makes most sense to go on
        5) continue to next msg
        """

        continue_dialogue = True
        self.current_question = self.node.message

        while continue_dialogue:
            print(self.current_question)
            # print("Current Question: \t", f"{self.current_question=}")
            self.current_response = input(">>> ")
            is_not_valid = self.validate_dialogue()

            if is_not_valid:
                # still @ this node, but now asking rephrased question
                self.current_question = is_not_valid
            else:
                self.chat_history.append([self.current_question, self.current_response])

                # choose next question
                if len(self.node.children) == 1:
                    self.node = self.node.children[0]
                    self.current_question = self.node.message
                elif len(self.node.children) == 0:
                    continue_dialogue = False
                else:
                    self.choose_next_path()
                    self.current_question = self.node.message
        
        return self.chat_history



    def choose_next_path(self):
        template = (
            """
            Your job is to pick the next question in a conversation from a list of possible questions. \
            You will be given criteria for each question and your goal is to match the current response to the \
            criteria. 

            The criteria will be in the following format:
            0: criteria_0
            1: criteria_2
            2: criteria_2

            Your response should ONLY be the index of the selected next question. For example, if you \
            choose the first question, respond ONLY with '0'
            Here are the previous responses in the conversation for context:
            {chat_history}
            """
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = """The last question asked was '{current_question}'. The responde was: '{current_response}' \
        Return ONLY the index. Here are the criteria: {critera}
        """
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        # get a chat completion from the formatted messages
        res = self.chooser(
            chat_prompt.format_prompt(
                chat_history= self.chat_history,
                current_question = self.current_question,
                current_response = self.current_response,
                critera = "\n".join([f"{i}:  {q_c[1]}" for i, q_c in enumerate(self.node.children)])
            ).to_messages()
        )
        
        res = res.content.strip()
        # print('choose next path: \t', f"{res=}")
        try:
            self.node = self.node.children[int(res)][0]
        except:
            self.node = self.node.children[0][0]
            


    def validate_dialogue(self):
        """
        if the current response does not make sense, rephrase question
        ask chat if msg makes sense

        returns False, if question makes sense
        returns rephrased question if it does not
        """

        template = (
            """
            You are assisting a conversation between a person and a robot. Your job is to determine if there is \
            a misunderstanding between the robot's questions and the the person's response, and if so, provide the \
            robot with a rephrased question.
            
            If it does not make sense, provide the robot with the rephrased question to account for any \
            misunderstanding or confusion. This response should be from the perspective of the robot. \
            Please respond in the following format: "Rephrased question: new_question"

            If the response to the question asked makes sense, respond with: "True". 
            Here are the previous responses in the conversation:
            {chat_history}
            """
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        human_template = "The robot just asked '{current_question}'. The human responded with: '{current_response}'"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

        chat_prompt = ChatPromptTemplate.from_messages(
            [system_message_prompt, human_message_prompt]
        )

        # get a chat completion from the formatted messages
        res = self.validater(
            chat_prompt.format_prompt(
                chat_history= self.chat_history,
                current_question = self.current_question,
                current_response = self.current_response 
            ).to_messages()
        )
        res = res.content.strip()

        # print("Validate Dialogue \n", f"{res=}")
        if res != "True":
            return " ".join(res.split()[2:])
        return False



# ### EXAMPLE DIALOGUE
# root = Node("Hi, what are some things you like to do for fun?")
# n11 = Node("What are some of your favorite sports to play?")
# n12 = Node("Do you like to paint at all?")
# n13 = Node("What are some of your favorite books?")
# root.children = [[n11, "physical activities"], [n12, "creative activities"], [n13, "academic activities, intellectual activities"]]

# n11.children.append([Node("Do you watch any sports too?"), "plays a lot of sports"])
# n11.children.append([Node("Do you want to be a professional athlete when you grow up?"), "has played a sport for a long time"])

# n12.children.append([Node("Do you want to go to art school?"), "Likes to paint"])
# n12.children.append([Node("Do you like going to museums?"), "Does not like to paint"])

# n13.children.append([Node("Have you read Harry Potter?"), "Likes fantasy novels"])
# n13.children.append([Node("Have you read Sherlock Holmes?"), "Likes crime novels"])
# n13.children.append([Node("Who is your favorite super hero?"), "Likes comics"])
# n13.children.append([Node("Do you tend to read professors books?"), "Likes nonfiction"])

# T = Dialogue_Tree(root=root)
# chat = T.start_dialogue()
# print("\n\n", f"{chat=}")


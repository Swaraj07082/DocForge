from groq import Groq
import json

class RefactoringAgent:
    
#     def __init__(self , model):

#         self.model = model
#         client = Groq()

#         chat_completion = client.chat.completions.create(
#             messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant."
#         },
#         {
#             "role": "user",
#             "content": "Explain the importance of fast language models",
#         }
#     ],
#     model = self.model
# )


    def refactor_code(self , file_name):
        
        with open("symbol_index.json", "r") as f:
            symbol_index = json.load(f)

        # print(symbol_index)

        functions : list = []

        for symbol in symbol_index:
            if symbol_index[symbol][0] == f"{file_name}":
                functions.append(symbol)



obj = RefactoringAgent()
obj.refactor_code("app.py")



from utilites.pydantic_types import AgentResponse

schema =  AgentResponse.model_json_schema()

print(schema)
context = """You are a coding agent.
            - Be concise. Avoid long reasoning.
            - When the user asks for code, output ONLY a single, runnable code block with minimal comments.
            - No extra explanations unless explicitly requested.
            """

code_parser_template = """Parse the response from a previous LLM into a description and a string of valid code, 
                            also come up with a valid filename this could be saved as that doesnt contain special characters. 
                            Here is the response: {response}. You should parse this in the following JSON Format: """
"""
Simple indentation formatter
"""

def indentation_formatter(text, tab_size=3, max_budget=29):
    """
    AI can't write this.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n') # deal with carriage returns

    stack = 0 # quote-unquote 'Stack'
    curr_budget = max_budget
    state = "TABBING" # TABBING, PARSING
    index = 0
    parsed = []

    while index < len(text):
        if text[index] == '\n':
            stack = 0
            curr_budget = max_budget
            state = "TABBING"
            parsed.append('\n')
            index += 1
            continue
        if state == "TABBING":
            if text[index] == '\t':
                stack += 1
                index += 1
            elif index+3 < len(text) and text[index:index+4] == '    ': # Handle 4-space indentations
                stack += 1
                index += 4
            else:
                state = "PARSING"
        elif state == "PARSING":
            # Ignore tabs between paragraph. There's probably some edge 
            # case here somewhere regarding the number of indentations. 
            if text[index] != '\t': 
                if curr_budget == max_budget:
                    parsed.extend([' ' for i in range(stack * tab_size)])
                    curr_budget -= stack * tab_size
                parsed.append(text[index])
                curr_budget -= 1
                if curr_budget == 0:
                    if (
                        index+1 < len(text) and 
                        text[index] != ' ' and 
                        text[index].isalpha() and 
                        text[index+1] != ' ' and 
                        text[index+1].isalpha()
                    ):
                        parsed.append('-') # Hyphen
                    curr_budget = max_budget
                    parsed.append('\n')
            index += 1

    return ''.join(parsed)

if __name__ == "__main__":
    text = """
Hello world! How are you doing today! I am going to tell you all about my favorite ice cream flavors. For no reason what so ever!
	- My favorite ice cream flavors:
		- Chocolate
		- Mint 										Chocolate Chip (We just added a buncha tabs there)
		- Rocky Road
			- sort of
		- Vanilla
		- Strawberry
		- Okay I guess I like everything then
    
    - Now we're indenting by 4-spaces 
        - Again...
            - And again.........
"""
    print(indentation_formatter(text))
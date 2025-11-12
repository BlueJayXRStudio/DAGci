import pytest
from Tools.parsers.indentation_formatter import indentation_formatter

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
answer = "\nHello world! How are you doin-\ng today! I am going to tell y-\nou all about my favorite ice \ncream flavors. For no reason \nwhat so ever!\n   - My favorite ice cream fl-\n   avors:\n      - Chocolate\n      - Mint Chocolate Chip (\n      We just added a buncha \n      tabs there)\n      - Rocky Road\n         - sort of\n      - Vanilla\n      - Strawberry\n      - Okay I guess I like e-\n      verything then\n\n   - Now we're indenting by 4\n   -spaces \n      - Again...\n         - And again.........\n\n"

@pytest.mark.parser_test
def test_indentation_formatter():
    assert indentation_formatter(text) == answer
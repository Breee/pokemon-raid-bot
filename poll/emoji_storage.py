import discord

# Dictionary that maps the numblock emojis to a number.
EMOJI_TO_NUMBER = {
    "\U00000031\U000020E3": 0,
    "\U00000032\U000020E3": 1,
    "\U00000033\U000020E3": 2,
    "\U00000034\U000020E3": 3,
    "\U00000035\U000020E3": 4,
    "\U00000036\U000020E3": 5,
    "\U00000037\U000020E3": 6,
    "\U00000038\U000020E3": 7,
    "\U00000039\U000020E3": 8,
    "\U0001F51F": 9
}

# Reverse of EMOJI_TO_NUMBER
NUMBER_TO_EMOJI = {
    0: "\U00000031\U000020E3",
    1: "\U00000032\U000020E3",
    2: "\U00000033\U000020E3",
    3: "\U00000034\U000020E3",
    4: "\U00000035\U000020E3",
    5: "\U00000036\U000020E3",
    6: "\U00000037\U000020E3",
    7: "\U00000038\U000020E3",
    8: "\U00000039\U000020E3",
    9: "\U0001F51F",
}
"""
:regional_indicator_a:  \U0001F1E6
:regional_indicator_b:  \U0001F1E7
:regional_indicator_c:  \U0001F1E8
:regional_indicator_d:  \U0001F1E9
:regional_indicator_e: \U0001F1EA
:regional_indicator_f: \U0001F1EB
:regional_indicator_g:  \U0001F1EC
:regional_indicator_h:  \U0001F1ED
:regional_indicator_i:  \U0001F1EE
:regional_indicator_j:  \U0001F1EF
"""
LETTEREMOJI_TO_NUMBER = {
'\U0001F1E6' : 0,
'\U0001F1E7' : 1,
'\U0001F1E8' : 2,
'\U0001F1E9' : 3,
'\U0001F1EA' : 4,
'\U0001F1EB' : 5,
'\U0001F1EC' : 6,
'\U0001F1ED' : 7,
'\U0001F1EE' : 8,
'\U0001F1EF' : 9
}

NUMBER_TO_LETTEREMOJI = {
0: '\U0001F1E6',
1: '\U0001F1E7',
2: '\U0001F1E8',
3: '\U0001F1E9',
4: '\U0001F1EA',
5: '\U0001F1EB',
6: '\U0001F1EC',
7: '\U0001F1ED',
8: '\U0001F1EE',
9: '\U0001F1EF'
}


# Dictionary that maps the people emojis to a number.
# The emojis in this dict are used in the raid-poll to express the amount of extra people someone
#  brings to a raid.

DEFAULT_PEOPLE_EMOJI_TO_NUMBER = {
    "\U0001F57A": 1,
    "\U0001F46D": 2,
    "\U0001F46A": 3,
    "\U0001F468\U0000200D\U0001F469\U0000200D\U0001F467\U0000200D\U0001F466": 4
}


PEOPLE_EMOJI_TO_NUMBER = dict()

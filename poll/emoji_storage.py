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

# Dictionary that maps the people emojis to a number.
# The emojis in this dict are used in the raid-poll to express the amount of extra people someone
#  brings to a raid.
PEOPLE_EMOJI_TO_NUMBER = {
    "\U0001F57A": 1,
    "\U0001F46D": 2,
    "\U0001F46A": 3,
    "\U0001F468\U0000200D\U0001F469\U0000200D\U0001F467\U0000200D\U0001F466": 4
}
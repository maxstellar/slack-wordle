# placeholder code with input

# load in valid guesses
with open('valid-wordle-words.txt', 'r') as file:
    valid_guesses = {line.strip() for line in file}

# we'll have to load in the daily word from API later - update via date etc.

daily_word = "AUDIO".lower()

def check_guess(guess):
    global daily_word

    if guess not in valid_guesses:
        return "Not in word list"
    
    check_string = []
    yellows = []

    # fill greens
    for i, letter in enumerate(guess):
        if letter == daily_word[i]:
            yellows.append(letter)
            check_string.append("🟩")
            continue
        check_string.append("⬜")
    
    #fill yellows
    for i, letter in enumerate(guess):
        if check_string[i] == "🟩":
            continue
        if letter in daily_word:
            # consider if yellows for this letter have already been given
            if daily_word.count(letter) > yellows.count(letter):
                yellows.append(letter)
            else:
                check_string[i] = "⬜"
                continue
            check_string[i] = "🟨"
    
    return "".join(check_string)

while 1:
    user_guess = input()
    if user_guess == "get me out of here":
        break
    print(f"{user_guess.lower()}: {check_guess(user_guess.lower())}")


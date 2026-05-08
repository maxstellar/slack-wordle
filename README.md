# slack-wordle

wordle bot for slack, written in python

## tech stack

- python (slack bolt framework)
- postgresql
- docker (i guess)

## setup

1. create a slack app at https://api.slack.com/apps
2. enable socket mode and interactivity
3. add these slash commands: `/wordle`, `/wordle-share`, and `/wordle-letters`
4. under oauth & permissions, add the `chat:write` and `commands` scopes
5. install the app to your workspace
6. create a `.env` file from the `.env.example` template
7. add your `slack_bot_token` (xoxb) and `slack_app_token` (xapp)
8. run `docker compose up -d --build` to start it up

## usage

- `/wordle <guess>`: submit a 5-letter guess
- `/wordle-letters`: see your current keyboard (green, yellow, gray, and remaining)
- `/wordle-share`: manually share your results to the channel
- 
## commands

- `docker compose down`: stops the bot
- `docker compose down -v`: stops the bot and wipes the database entirely

"""""
This is the main file of the project. It is responsible for handling the commands and calling the appropriate functions.

Please see READ.md for detailed information about the code.
"""""
import Commands
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = Commands.app

@app.event("app_mention")
def mention_handler(body, context, payload, options, say, event, logger):
    try:
        request = payload['blocks'][0]['elements'][0]['elements'][1]['text']
    except IndexError:
        logger.error("Invalid payload format: %s", payload)
        return
    res = request.lstrip().split(' ', 1)
    logger.info(res)
    cmd = res[0].strip().lower()
    if len(res) > 1:
        params = res[1].lstrip()
    else:
        params = ""
    logger.info(cmd)
    logger.info('#' * 60)

    if cmd == "help":
        #help_cmd(request, cmd, params, say, logger)
        Commands.help_cmd(say)

    elif cmd == "info":
        Commands.info_cmd(event, say, logger)
    
    elif cmd == "spectrogram":
        Commands.spectrogram_cmd(event, say, logger, user_id=event["user"])
    
    elif cmd == "waveform":
        Commands.waveform_cmd(event, say, logger)

    elif cmd == "lpf":
        Commands.lpf_cmd(event, say, logger, user_id=event["user"])

    elif cmd == "hpf":
        Commands.hpf_cmd(event, say, logger, user_id=event["user"])
    
    elif cmd == "bsf":
        Commands.bsf_cmd(event, say, logger, user_id=event["user"])

    else:
        say(f"Sorry, I am unable to complete the command `{cmd}`.\n")
        # help_cmd(request, cmd, params, say, logger)
        Commands.help_cmd(say)

if __name__ == "__main__":
    handler = SocketModeHandler(app, Commands.SLACK_APP_TOKEN)
    handler.start()
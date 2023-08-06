"""
This file contains the functions that are called when a user sends a command to the bot.

Please see READ.md for detailed information about the code.
"""
import logging
import os
import requests
import soundfile as sf
from io import BytesIO
from dotenv import load_dotenv
from slack_bolt import App
import Helper_Functions as hf

# Load .env file
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Define variables
SLACK_BOT_TOKEN = os.environ["Bot_OAuth_token"]
SLACK_APP_TOKEN = os.environ["App_token"]

app = App(token=SLACK_BOT_TOKEN)

def download_audio_data(audio_url):
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
    response = requests.get(audio_url, headers=headers, timeout=50)
    if response.status_code != 200:
        return None, None
    audio_data, sample_rate = sf.read(BytesIO(response.content))
    return audio_data, sample_rate

def send_graph_to_slack(buffer, initial_comment, channel):
    response = requests.post(
        "https://slack.com/api/files.upload",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        files={"file": ("graph.png", buffer, "image/png")},
        data={"initial_comment": initial_comment, "channels": channel},
        timeout=40  # Set the timeout value (in seconds) as per your preference
    )
    return response

def fetch_audio_data(event, logger, say):
    file_name = event["files"][0]["name"]
    audio_url = event["files"][0]["url_private_download"]
    audio_data, sample_rate = download_audio_data(audio_url)

    if audio_data is None:
        logger.error("Failed to download the audio file.")
        say(f"Sorry, I could not download the audio file {file_name}.")
        return None, None

    return audio_data, sample_rate

def apply_filter_and_send_to_slack(event, say, logger, user_id, filter_type, filter_params):
    # Fetch the audio data from the Slack API
    audio_data, sample_rate = fetch_audio_data(event, logger, say)
    if audio_data is None:
        return
    
    # Get the file name
    file_name = event["files"][0]["name"]

    # Apply the specified filter to the audio data
    if filter_type == 'lpf':
        filtered_audio = hf.apply_low_pass_filter(audio_data, sample_rate, **filter_params)
        filter_name = 'Low-Pass'
    elif filter_type == 'hpf':
        filtered_audio = hf.apply_high_pass_filter(audio_data, sample_rate, **filter_params)
        filter_name = 'High-Pass'
    elif filter_type == 'bsf':
        filtered_audio = hf.apply_band_stop_filter(audio_data, sample_rate, **filter_params)
        filter_name = 'Band-Stop'
    else:
        logger.error("Invalid filter type.")
        say("Sorry, there was an error processing the audio file.")
        return

    # Send the filtered audio to Slack
    graph_buffer = hf.generate_graph(filtered_audio, sample_rate, 'spectrogram')
    send_graph_to_slack(graph_buffer, f'Spectrogram of {filter_name} Filtered {file_name}', event['channel'])

    # Save the filtered audio to a new file
    filtered_audio_buffer = BytesIO()
    sf.write(filtered_audio_buffer, filtered_audio, sample_rate, format='wav')

    # Send the filtered audio file to Slack
    response_audio = requests.post(
        "https://slack.com/api/files.upload",
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        files={"file": ("filtered_audio.wav", filtered_audio_buffer.getvalue(), "audio/wav")},
        data={"channels": event['channel']}, timeout=45
    )

    if response_audio.status_code == 200 and response_audio.json()["ok"]:
        logger.info("Filtered audio and spectrogram sent successfully.")
    else:
        logger.error("Failed to send the filtered audio and spectrogram.")

def process_audio_file(event, say, logger, graph_type=None):
    audio_data, sample_rate = fetch_audio_data(event, logger, say)
    if audio_data is None:
        return
    
    file_name = event["files"][0]["name"]

    # Generate the waveform graph
    if graph_type == 'waveform':
        graph_buffer = hf.generate_graph(audio_data, sample_rate, 'waveform')
        graph_title = f'Waveform of {file_name}'
    elif graph_type == 'spectrogram':
        graph_buffer = hf.generate_graph(audio_data, sample_rate, 'spectrogram')
        graph_title = f'Spectrogram of {file_name}'
    else:
        # For the 'info' command
        audio_info = hf.get_audio_info(audio_data, sample_rate)
        say(f"Information for the audio file {file_name}:\n"
            f"- Channels: {audio_info['channels']}\n"
            f"- Sample rate: {audio_info['sample_rate']}Hz\n"
            f"- Bit depth: {audio_info['bit_depth']}\n"
        )
        return

    send_graph_to_slack(graph_buffer, graph_title, event['channel'])

def help_cmd(say):
    say(
    "I can help you with the following commands:\n"
    "- `help` - Displays the help message.\n"
    "- `info` - Get information about an audio file.\n"
    "- `waveform` - Get the waveform of an audio file.\n"
    "- `spectrogram` - Get the spectrogram of an audio file.\n"
    "- `lpf` - Apply a low-pass filter to an audio file. (Cutoff Freq = 2kHz)\n"
    "- `hpf` - Apply a high-pass filter to an audio file. (Cutoff Freq = 6kHz)\n"
    "- `bsf` - Apply a band-stop filter to an audio file. (Low Cut = 2kHz, High Cut = 6kHz)\n"
    )

def info_cmd(event, say, logger):
    process_audio_file(event, say, logger)

def waveform_cmd(event, say, logger):
    process_audio_file(event, say, logger, graph_type='waveform')

def spectrogram_cmd(event, say, logger, user_id):
    process_audio_file(event, say, logger, graph_type='spectrogram')

def lpf_cmd(event, say, logger, user_id):
    # Set the cutoff frequency to a static value (e.g., 1000 Hz)
    cutoff_frequency = 2000  # Hz
    filter_params = {'cutoff_frequency': cutoff_frequency}
    apply_filter_and_send_to_slack(event, say, logger, user_id, 'lpf', filter_params)

def hpf_cmd(event, say, logger, user_id):
    # Set the cutoff frequency for the high-pass filter (e.g., 1000 Hz)
    cutoff_frequency = 6000  # Hz
    filter_params = {'cutoff_frequency': cutoff_frequency}
    apply_filter_and_send_to_slack(event, say, logger, user_id, 'hpf', filter_params)

def bsf_cmd(event, say, logger, user_id):
    # Set the low and high cut frequencies for the band-stop filter in Hz
    low_cut = 2000  # Hz
    high_cut = 6000  # Hz
    filter_params = {'low_cut': low_cut, 'high_cut': high_cut}
    apply_filter_and_send_to_slack(event, say, logger, user_id, 'bsf', filter_params)
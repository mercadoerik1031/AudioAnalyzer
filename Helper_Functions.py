"""
This file contains the helper functions for the main.py file. 

Please see READ.md for detailed information about the code.
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
from scipy import signal

matplotlib.use('Agg')

def convert_to_mono(audio_data):
    if len(audio_data.shape) > 1 and audio_data.shape[1] ==2:
        return audio_data.mean(axis=1)
    
    return audio_data

def get_audio_info(audio_data, sample_rate):
    channels = audio_data.shape[1] if len(audio_data.shape) > 1 else 1
    bit_depth = audio_data.dtype.itemsize * 8
    return{
        'channels': channels,
        'sample_rate': sample_rate,
        'bit_depth': bit_depth
    }

def generate_graph(audio_data, sample_rate, graph_type):
    audio_data = convert_to_mono(audio_data)

    plt.style.use('dark_background')

    # Create the graph
    if graph_type == "waveform":
        time = np.arange(0, len(audio_data)) / sample_rate
        plt.plot(time, audio_data)
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.title('Waveform')
    elif graph_type == "spectrogram":
        n_fft = 4096
        overlap = int(n_fft / 4 * 3)
        window = np.hamming(n_fft)
        spectrogram, _, _, _ = plt.specgram(audio_data, NFFT=n_fft, noverlap=overlap, Fs=sample_rate, window=window)

        # Adding a small value to the spectrogram to avoid divide by zero
        eps = 1e-10
        spectrogram = np.maximum(spectrogram, eps)

        # Determine the frequency range to be displayed (from 0 to 20 kHz)
        f_max_idx = int(spectrogram.shape[0] * 20000 / sample_rate)
        plt.colorbar(label='Power Spectral Density (dB)')
        plt.imshow(10 * np.log10(spectrogram[:f_max_idx]), aspect='auto', cmap='viridis', origin='lower',
                   extent=[0, len(audio_data) / sample_rate, 0, 20000 / 1000]) 
        plt.xlabel('Time (s)')
        plt.ylabel('Frequency (kHz)')
        plt.title('Spectrogram')

    plt.tight_layout()

    # Save the graph to a BytesIO buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer

def apply_low_pass_filter(audio_data, sample_rate, cutoff_frequency):
    nyquist_frequency = 0.5 * sample_rate
    normal_cutoff = cutoff_frequency / nyquist_frequency
    b, a = signal.butter(8, normal_cutoff, btype='low', analog=False)

    audio_data = convert_to_mono(audio_data)

    # Apply the filter to the audio data (mono)
    filtered_audio = signal.lfilter(b, a, audio_data)

    return filtered_audio

def apply_high_pass_filter(audio_data, sample_rate, cutoff_frequency):
    nyquist_frequency = 0.5 * sample_rate
    normal_cutoff = cutoff_frequency / nyquist_frequency
    b, a = signal.butter(8, normal_cutoff, btype='high', analog=False)

    # Convert to mono if the audio is stereo
    audio_data = convert_to_mono(audio_data)

    # Apply the filter to the audio data (mono)
    filtered_audio = signal.lfilter(b, a, audio_data)

    return filtered_audio

def apply_band_stop_filter(audio_data, sample_rate, low_cut, high_cut, order=8):
    nyquist_frequency = 0.5 * sample_rate
    low_cut_normal = low_cut / nyquist_frequency
    high_cut_normal = high_cut / nyquist_frequency
    b, a = signal.butter(order, [low_cut_normal, high_cut_normal], btype='bandstop', analog=False)

    # Convert to mono if the audio is stereo
    audio_data = convert_to_mono(audio_data)

    # Apply the filter to the audio data (mono)
    filtered_audio = signal.lfilter(b, a, audio_data)

    return filtered_audio
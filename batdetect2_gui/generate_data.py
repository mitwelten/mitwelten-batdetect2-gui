import base64
import os
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import audio_utils as au
import wavfile

def compute_audio_data(annotation, audio_dir, playback_time_expansion):
    """returns the metadata, raw audio samples and base64 encoded wav file

    :param annotation (dict): dictionary containing annotations for a file
    :return (tuple):
      - (int) sample rate of audio
      - (array) audio samples
      - (string) base64 wav file
      - (float) file duration
    """
    # load wav
    if not os.path.exists(audio_dir):
        wav_file_path = annotation["file_name"].replace(".json", "")
    else:
        wav_file_path = os.path.join(
            audio_dir, annotation["file_name"].replace(".json", "")
        )
    sampling_rate, audio_raw = au.load_audio_file(
        wav_file_path, annotation["time_exp"]
    )
    duration = audio_raw.shape[0] / float(sampling_rate)

    # apply time expansion if the file is high frequency
    time_exp_listen = annotation["time_exp"]
    if annotation["time_exp"] == 1:
        time_exp_listen = playback_time_expansion
    elif annotation["time_exp"] == playback_time_expansion:
        print("Correct time expansion already used.")
    else:
        raise Exception("Unsuported time expansion factor.")

    aud_file = BytesIO()
    wavfile.write(aud_file, int(sampling_rate / time_exp_listen), audio_raw)
    aud_data = base64.b64encode(aud_file.getvalue()).decode("utf-8")
    aud_file.close()

    return sampling_rate, audio_raw, aud_data, duration

def compute_image_data(audio_raw, sampling_rate, spec_params, reference):
    """computes and saves spectrogram images to files

    :param audio_raw (array): audio samples
    :param sampling_rate (int):
    :return (tuple):
      - (list) paths to the saved spectrogram image files
      - (tuple) height, width in pixels
    """
    n_segments = 16
    if os.path.exists(f'data/{os.path.basename(reference)}_dims'):
        print("Spectrogram already generated.")
        with open(f'data/{os.path.basename(reference)}_dims', 'r') as f:
            dims = tuple(map(int, f.read().split()))
        return [f'data/{os.path.basename(reference)}_{i}.jpg' for i in range(n_segments)], dims

    # generate spectrogram
    spec_raw = au.generate_spectrogram(audio_raw, sampling_rate, spec_params)
    spec_raw -= spec_raw.min()
    spec_raw /= spec_raw.max()
    cmap = plt.get_cmap("inferno")
    spec = (cmap(spec_raw)[:, :, :3] * 255).astype(np.uint8)
    del spec_raw

    dims = (spec.shape[0], spec.shape[1])
    with open(f'data/{os.path.basename(reference)}_dims', 'w') as f:
        f.write(f'{dims[0]} {dims[1]}')

    # split spec into multiple parts along the x axis
    os.makedirs("data", exist_ok=True)
    segment_width = spec.shape[1] // n_segments
    im_paths = []
    for i in range(n_segments):
        start = i * segment_width
        # For the last segment, take all remaining columns
        # to handle non-divisible cases
        end = None if i == n_segments - 1 else start + segment_width
        segment = spec[:, start:end, :]
        im = Image.fromarray(segment)

        # Save the image to a temporary file
        filename = f'data/{os.path.basename(reference)}_{i}.jpg'
        im.save(filename, "JPEG", quality=90)

        # Append the URL of the saved image file
        im_paths.append(filename)

    del spec
    return im_paths, dims

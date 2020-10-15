import os
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import wavfile

clean_trainset_28spk_directory = "datasets/DS_10283_2791/clean_trainset_28spk_wav"
noisy_trainset_28spk_directory = "datasets/DS_10283_2791/noisy_trainset_28spk_wav"
clean_trainset_56spk_directory = "datasets/DS_10283_2791/clean_trainset_56spk_wav"
noisy_trainset_56spk_directory = "datasets/DS_10283_2791/noisy_trainset_56spk_wav"

clean_testset = "res/clean_testset_wav"
noisy_testset = "res/noisy_testset_wav"



def get_speech_duration(path):
    # We already know that all files are 48 KHz 16 bit mono wav.
    # Skip librosa and calculate the duration directly.
    riff_header_bytes = 44
    bytes_per_sample = 2
    samples_pes_second = 48000
    file_bytes = os.path.getsize(path)
    return ((file_bytes - riff_header_bytes) // bytes_per_sample) / samples_pes_second


def load_data(path, max_file_count=None, max_sample_count=None):
    files = os.listdir(path)
    if max_file_count is None:
        max_file_count = len(files)
    if max_sample_count is None:
        data = np.empty((max_file_count,), dtype=np.ndarray)
    else:
        data = np.zeros((max_file_count, max_sample_count))
        print(data)
    for i, file in enumerate(files):
        if i >= max_file_count:
            break
        sample_rate, samples = wavfile.read(os.path.join(path, file))
        if max_sample_count is None:
            data[i] = samples
        else:
            data[i, 0:len(samples)] = samples
    return data


def visualize(noisy, clean, n=None):
    if len(noisy) != len(clean):
        return
    if n is None:
        n = len(noisy)
    if n > len(noisy):
        n = len(noisy)
    for i in range(n):
        plt.plot(noisy[i])
        plt.figtext(0.5, 0.01, "noisy {}".format(i))
        plt.show()
        plt.plot(clean[i])
        plt.figtext(0.5, 0.01, "clean {}".format(i))
        plt.show()


def zero_pad(noisy, clean):
    ret_noisy = np.copy(noisy)
    ret_clean = np.copy(clean)
    if len(noisy) != len(clean):
        return
    max_n = 0
    for i in noisy:
        if len(i) > max_n:
            max_n = len(i)
    for i in range(len(noisy)):
        pad = max_n - len(ret_noisy[i])
        if pad > 0:
            ret_noisy[i] = np.pad(ret_noisy[i], (0, pad), 'constant')
            ret_clean[i] = np.pad(ret_clean[i], (0, pad), 'constant')

    return ret_noisy, ret_clean


def plot_durations_histogram():
    durations = []
    for directory in [clean_trainset_28spk_directory, clean_trainset_56spk_directory]:
        for filename in os.listdir(directory):
            durations.append(get_speech_duration(os.path.join(directory, filename)))
    durations.sort()

    # Histogram from the minimum to the 98-th percentile, to hide the outliers.
    percentiles = np.percentile(durations, [0, 50, 98, 100])
    print(percentiles)  # The median and the maximum are also of interest.
    _, ax = plt.subplots()
    ax.hist(durations, bins=np.linspace(percentiles[0], percentiles[2], num=100))
    plt.show()


def find_closest_speech_lengths(target_count, max_file_count=None, visualize=False):
    noisy_files = []
    if max_file_count is None:
        files = os.listdir(noisy_trainset_28spk_directory)
        max_file_count = len(files)
    for i, filename in enumerate(os.listdir(noisy_trainset_28spk_directory)):
        if max_file_count is None or i < max_file_count:
            duration = get_speech_duration(os.path.join(noisy_trainset_28spk_directory, filename))
            noisy_files.append((filename, duration))
        else:
            break
    noisy_files.sort(key=lambda x: x[1])
    print(noisy_files)

    # Find he subset of target count with minimum duration difference.
    min_i = np.argmin([noisy_files[i + target_count][1] - noisy_files[i][1]
                       for i in range(len(noisy_files) - target_count)])
    target_noisy_files = noisy_files[min_i: min_i + target_count]
    noisy_samples = np.empty((target_count,), dtype=np.ndarray)
    clean_samples = np.empty((target_count,), dtype=np.ndarray)
    i = 0
    for filename, duration in target_noisy_files:
        _, noisy_samples[i] = wavfile.read(os.path.join(noisy_trainset_28spk_directory, filename))
        _, clean_samples[i] = wavfile.read(os.path.join(clean_trainset_28spk_directory, filename))
        i += 1
    return noisy_samples, clean_samples, target_noisy_files[0][1], target_noisy_files[len(target_noisy_files)-1][1]


def read_test_files(min_duration, max_duration):
    noisy_test=[]
    clean_test=[]
    for filename in os.listdir(noisy_testset):
        dur = get_speech_duration(os.path.join(noisy_testset, filename))
        if min_duration <= dur <= max_duration:
            noisy_test.append(wavfile.read(os.path.join(noisy_testset, filename)))
    for filename in os.listdir(clean_testset):
        dur = get_speech_duration(os.path.join(clean_testset, filename))
        if min_duration <= dur <= max_duration:
            clean_test.append(wavfile.read(os.path.join(clean_testset, filename)))

    return  noisy_test, clean_test


def train_val_split(noisy, clean):
    lenconst=noisy.shape[0]
    randperm = np.random.permutation(lenconst)
    noisy, clean = noisy[randperm, :], clean[randperm, :]
    noisy_train, clean_train, noisy_val, clean_val = noisy[:int(np.round(0.8*lenconst)), :], clean[:int(np.round(0.8*lenconst)), :], noisy[int(np.round(0.8*lenconst)):, :], clean[int(np.round(0.8*lenconst)):, :]
    return noisy_train, clean_train, noisy_val, clean_val


def make_np_array(array):
    array = np.asarray(array)
    array = np.vstack([i for i in array])
    return array

# noisy, clean = find_closest_speech_lengths(10000)
# noisy, clean = find_closest_speech_lengths(7, 20)
# noisy_padded, clean_padded = zero_pad(noisy, clean)
# visualize(noisy, clean, 10)
# visualize(noisy_padded, clean_padded, 10)
#plot_durations_histogram()

'''noisy, clean , mindur, maxdur= find_closest_speech_lengths(50)
noisy_test, clean_test = read_test_files(mindur, maxdur)

noisy_padded, clean_padded = zero_pad(noisy, clean)
noisy_test_padded, clean_test_padded = zero_pad(noisy_test, clean_test)

noisy_padded=make_np_array(noisy_padded)
noisy_test_padded=make_np_array(noisy_test_padded)
clean_padded=make_np_array(clean_padded)
clean_test_padded=make_np_array(clean_test_padded)

noisy_train, clean_train, noisy_val, clean_val = train_val_split(noisy_padded, clean_padded)
print(noisy_train.shape, noisy_val.shape)'''

#noisy_padded = np.reshape(noisy_padded, (len(noisy_padded), len(noisy_padded[0])))
#clean_padded = np.reshape(clean_padded, (len(noisy_padded), len(noisy_padded[0])))

#noisy_padded = np.reshape(noisy_padded, (len(noisy_padded), len(noisy_padded[0])))


#visualize(noisy_padded, clean_padded, 10)
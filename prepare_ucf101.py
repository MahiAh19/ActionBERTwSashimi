"""
Given path to UCF dataset's video directory, performs train-val split (saved as json),
and computes video frames to disk, for the given frame-rate.
Creates the following json files in the `--out_dir`:
- train_ucf101.json
- val_ucf101.json
JSON format:
`video_name, label_idx`
The json files are generated as an intermediate step to obtain dataset in standard format;
we run `prepare_data.py` to generate the final dataset file (json).
Also stores the video frames in `--out_dir`.
"""

import os
import glob
import argparse
import numpy as np
import pandas as pd
from utils import save_video_frames

"""
python3 prepare_ucf101.py \
-v /home/axe/Datasets/UCF_101/raw/videos \
-o /home/axe/Datasets/UCF_101 \
-s 0.8 -fps 1
"""


def _filename(path):
    """
    Extracts filename from file path.
    >>> _filename('UCF_101/videos/Biking/v_Biking_g01_c01.avi')
    'Biking/v_Biking_g01_c01.avi'
    :param str path: path to video file
    :return: file name (containing class)
    """
    filename = path.split('/')[-2:]

    filename = '/'.join(filename)

    return filename


def train_val_test_split(label, video_dir, label_idx, split_ratio=0.8):
    """
    For the given video class sub-directory, performs train-val split
    and computes filenames along with class label idx.
    :param str label: class label name
    :param str video_dir: video directory
    :param int label_idx: class label index
    :param split_ratio: train-val set split ratio
    :returns: train & validation lists containing
                tuples of filenames & class idx
    """
    split_ratio2 = 0.1  # modified
    # Get all files in the given class directory
    paths = sorted(glob.glob(os.path.join(video_dir, label, '*.avi')))

    # Set seed (reproducibility) & shuffle
    np.random.seed(0)
    np.random.shuffle(paths)

    split_idx = int(len(paths) * split_ratio)
    split_idx2 = int(len(paths) * split_ratio2)

    split_idx2 = split_idx + split_idx2

    train_paths = paths[:split_idx]  # 1:16 -- 0:15 16vids
    val_paths = paths[split_idx: split_idx2]  # 16:18 -- 16,17 2vids
    test_paths = paths[split_idx2:]  # modified 18:20 -- 18,19 2vids

    # Extract filenames from paths & also insert the class label index
    train_fname_label_idxs = [(_filename(path), label_idx)
                              for path in train_paths]
    val_fname_label_idxs = [(_filename(path), label_idx) for path in val_paths]
    test_fname_label_idxs = [(_filename(path), label_idx)
                             for path in test_paths]  # mod

    # E.g.  [['Biking/v_Biking_g01_c01.avi', 12], ...]
    return train_fname_label_idxs, val_fname_label_idxs, test_fname_label_idxs


# ** Deprecated **
def _write_to_csv(fname_cls_idxs, out_file):
    """
    Given the filename-class_idx list,
    saves the tuple to csv file.
    :param fname_cls_idxs: (filename, class_idx) tuples
    :type fname_cls_idxs: list[tuple[str, int]]
    :param str out_file: path to output csv file
    """
    with open(out_file, 'w') as f:
        # Create columns
        f.write('video_name' + ',' + 'label_idx' + '\n')

        # Append delete
        for fname_cls in fname_cls_idxs:
            class_idx = fname_cls[1]
            filename = fname_cls[0]     # e.g. Bike/v_Bike_c5.avi

            # Clip out the video extension & parent folder (e.g --> v_Bike_c5)
            video_name = filename.split('.')[0].split('/')[-1]

            f.write(video_name + ',' + str(class_idx) + '\n')


def _write_to_json(fname_label_list, out_file):
    """
    Given the filename-class_idx list,
    saves the tuple to csv file.
    :param fname_label_list: (filename, label_idx) tuples <br>
                    e.g. (Bike/v_Bike_c5.avi, 24)
    :type fname_label_list: list[tuple[str, int]]
    :param str out_file: path to output json file
    """
    df = pd.DataFrame(fname_label_list, columns=['video_name', 'label_idx'])

    # Clip out the video extension & parent folder (e.g --> v_Bike_c5)
    df['video_name'] = df['video_name'].apply(
        lambda fname: fname.split('.')[0].split('/')[-1])

    # Save as json
    df.to_json(out_file, orient='records')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Prepares UCF-101 dataset: video to frames & train-val split')

    # Dataset params
    parser.add_argument('-v',   '--video_dir',      type=str,
                        help='input videos directory', required=True)
    parser.add_argument('-o',   '--out_dir',        type=str,
                        help='contains frame sub-dirs & split set files', required=True)
    parser.add_argument('-s',   '--split_ratio',    type=float,
                        help='train-val split ratio', default=0.8)
    parser.add_argument('-fps', '--frame_rate',     type=int,
                        help='frame-rate (FPS) for sampling videos', default=1)

    args = parser.parse_args()

    # Read all action class names
    classes = sorted(glob.glob(os.path.join(args.video_dir, '*')))
    classes = [cls.split('/')[-1] for cls in classes]

    assert len(
        classes) == 152, 'The UCF-101 dataset expects total 152 classes, but {} found!'.format(len(classes))

    # For each class in the videos dir, perform train-val split
    class2idx = {cls: i for i, cls in enumerate(classes)}

    # Store the video filename along with class label index
    train_data = []
    val_data = []
    test_data = []

    for cls_idx, cls_name in enumerate(classes):
        # Get the train-val-test split filename-class_idx tuples
        train_fname_cls_idx, val_fname_cls_idx, test_fname_cls_idx = train_val_test_split(
            cls_name, args.video_dir, cls_idx, args.split_ratio)

        train_data += train_fname_cls_idx
        val_data += val_fname_cls_idx
        test_data += test_fname_cls_idx

    # Save train & val splits as json files
    train_file = os.path.join(args.out_dir, 'train_ucf101.json')
    val_file = os.path.join(args.out_dir, 'val_ucf101.json')
    test_file = os.path.join(args.out_dir, 'test_ucf101.json')

    _write_to_json(train_data, train_file)
    _write_to_json(val_data, val_file)
    _write_to_json(test_data, test_file)

    print('Train, Validation and Test sets saved in:\n{}\n{}\n{}\n'.format(
        train_file, val_file, test_file))

    # list of tuples - (video_filenames, class_idx)
    dataset = sorted(train_data + val_data + test_data)

    # Parse videos & save frames to disk
    save_frames_dir = os.path.join(
        args.out_dir, 'frames_fps_{}'.format(args.frame_rate))

    if not os.path.exists(save_frames_dir):
        os.makedirs(save_frames_dir)

    total = len(dataset)
    for i, sample in enumerate(dataset):
        filename = sample[0]

        video_path = os.path.join(args.video_dir, filename)

        # save frames
        save_video_frames(video_path, args.frame_rate, save_frames_dir)

        if i % 1000 == 0:
            print('{} / {}'.format(i, total))

    print('Done! Video Frames saved in {}'.format(save_frames_dir))

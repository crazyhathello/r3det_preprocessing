import cv2
import argparse
import numpy as np
import os
import shutil
from ast import literal_eval
from skimage.metrics import structural_similarity
# from skimage.measure import compare_ssim

dir_n = 0                   # 影片在資料夾內的層數 (路徑為影片:0, 資料夾/影片:1, 資料夾/資料夾/影片:2 ...)
rpi = 'rpi1_'               # 存檔命名用
# video_path = '/source/input_video.avi'              # 原始影片位置
video_path = os.environ['VIDEO']
ROI_path = os.environ['ROI']
print("Video path: ", video_path)
print("ROI path: ", ROI_path)
img_save_path = '/cropped_frames/'    # 校正後影像位置
new_video_save_path = '/cropped_videos/'
filename_n = 4              # 檔名字數(6:前面補0至6位數 000001)
sep = True                  # 1分鐘影片切成30秒
vdo = False
image_height = 1024
image_width = 1024


ROIs = [(213, 64), (236, 538), (743, 522), (672, 43)]
if ROI_path is not None:
    with open(ROI_path) as f:
        data = f.read()
    ROIs = data.split(": ", 1)[1]
    ROIs = literal_eval(ROIs)
    print(ROIs)
similarity = 1
index = 0


def main():
    args.video_path = os.environ['VIDEO']
    if args.video_path.endswith('.avi'):
        cut_video(args.video_path, img_save_path, new_video_save_path)
    elif dir_n == 1:
        import glob
        video_list = glob.glob('{}/*.avi'.format(args.video_path))
        for video in video_list:
            cut_video(video, img_save_path, new_video_save_path)
    elif dir_n == 2:
        import glob
        dir_list = glob.glob('{}/*'.format(args.video_path))
        for dir1 in dir_list:
            video_list = glob.glob('{}/*.avi'.format(dir1))
            for video in video_list:
                cut_video(video, img_save_path, new_video_save_path)
    elif dir_n == 3:
        import glob
        date_list = glob.glob('{}/*'.format(args.video_path))
        for datei in date_list:
            dir_list = glob.glob('{}/*'.format(datei))
            for diri in dir_list:
                video_list = glob.glob('{}/*.avi'.format(diri))
                for video in video_list:
                    cut_video(video, img_save_path, new_video_save_path)
    elif dir_n == 4:
        import glob
        date_list = glob.glob('{}/*'.format(args.video_path))
        for datei in date_list:
            dir_list = glob.glob('{}/*'.format(datei))
            for diri in dir_list:
                dir_list2 = glob.glob('{}/*'.format(diri))
                for dir_list3 in dir_list2:
                    video_list = glob.glob('{}/*.avi'.format(dir_list3))
                    for video in video_list:
                        cut_video(video, img_save_path, new_video_save_path)


def cut_video(video, img_save_path, new_video_save_path):
    try:
        os.makedirs(img_save_path)
    except FileExistsError:
        print(img_save_path + "  exists")

    global index
    crop_frames = 0
    start = args.start
    # start = 0f
    cap = cv2.VideoCapture(video)
    # src = np.float32(ROIs[args.device])
    src = np.float32(ROIs)
    h, w = args.image_height, args.image_width
    dst = np.float32([(0, 0), (0, h), (w, h), (w, 0)])
    M = cv2.getPerspectiveTransform(src, dst)

    video_name = video.split('/')[-1]
    pa = video_name.split('\\')[-1]
    pa = pa.split('.')[-2]
    # pa = rpi + pa
    p = img_save_path + '/' + pa

    try:
        os.makedirs(p)
    except FileExistsError:
        print(p + "  exist")
    oldpath = p + "/r3det"

    try:
        os.makedirs(oldpath)
    except FileExistsError:
        print(oldpath + "  exist")

    target_image = None
    while True:
        ret, frame = cap.read()
        if ret == False:
            break
        clone = frame.copy()
        processed = cv2.warpPerspective(clone, M, (w, h))

        if target_image is None:
            n = filename_n - len(str(start + crop_frames + index))
            filename = str(0) * n + str(start + crop_frames)
            save = oldpath + '/{}.jpg'.format(filename)
            cv2.imwrite(save, processed)
            target_image = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            crop_frames += 1
            continue

        s = 1
        if s <= similarity:
            n = filename_n - len(str(start + crop_frames))
            filename = str(0) * n + str(start + crop_frames + index)
            save = oldpath + '/{}.jpg'.format(filename)
            cv2.imwrite(save, processed)
            crop_frames += 1
            target_image = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)

    # sepImg -------------------------------------------------------------------
    if sep is True:
        images = [img for img in os.listdir(oldpath)]
        images.sort()

        newpath_1 = p + "/CRNN/" + pa + '-1'
        newpath_2 = p + "/CRNN/" + pa + '-2'
        try:
            os.makedirs(newpath_1)
            print("Created newpath_1")
        except FileExistsError:
            print(newpath_1 + "  exists")
        try:
            os.makedirs(newpath_2)
            print("Created newpath_2")
        except FileExistsError:
            print(newpath_2 + "  exists")

        i = 0
        for image in images[:150]:
            shutil.copy(os.path.join(oldpath, image),
                        os.path.join(newpath_1, image))
        for image in images[150:300]:
            n = 4 - len(str(i))
            new_name = '{}.jpg'.format(i)
            new_name = str(0) * n + new_name
            shutil.copy(os.path.join(oldpath, image),
                        os.path.join(newpath_2, new_name))
            i = i+1

    cap.release()

    # img2video -------------------------------------------------------------------
    if vdo is True:
        try:
            os.makedirs(new_video_save_path)
        except FileExistsError:
            print(new_video_save_path + "  exist")
        if sep is True:
            video_names = [newpath_1, newpath_2]
            print(video_names)
            for image_folder in video_names:
                video_name = pa + image_folder[-2:]
                print(video_name)
                images = [img for img in os.listdir(
                    image_folder) if img.endswith(".jpg")]
                video_save = new_video_save_path + video_name + '.avi'
                frame = cv2.imread(os.path.join(image_folder, images[0]))
                height, width, layers = frame.shape
                fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
                video_1 = cv2.VideoWriter(
                    video_save, fourcc, 30, (width, height))
                for image in images:
                    video_1.write(cv2.imread(
                        os.path.join(image_folder, image)))
                print('save ' + video_save)
        else:
            video_names = [p]
            print(video_names)
            for image_folder in video_names:
                video_name = pa
                print(video_name)
                images = [img for img in os.listdir(
                    image_folder) if img.endswith(".jpg")]
                video_save = new_video_save_path + video_name + '.avi'
                frame = cv2.imread(os.path.join(image_folder, images[0]))
                height, width, layers = frame.shape
                fourcc = cv2.VideoWriter_fourcc('X', 'V', 'I', 'D')
                video_1 = cv2.VideoWriter(
                    video_save, fourcc, 30, (width, height))
                for image in images:
                    video_1.write(cv2.imread(
                        os.path.join(image_folder, image)))
                print('save ' + video_save)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crop video to images')
    parser.add_argument('--video_path', default=video_path,
                        type=str, help='video path')
    parser.add_argument('--device', default='rpi', type=str, help='which rpi')
    parser.add_argument('--start', default=0, type=int,
                        help='which index to start')
    parser.add_argument('--image_height', default=image_height,
                        type=int, help='image height')
    parser.add_argument('--image_width', default=image_width,
                        type=int, help='image width')
    args = parser.parse_args()
    main()

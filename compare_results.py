# -*- coding: utf-8 -*-
"""
Created on Fri May 3 2019
@author: robota
"""
import argparse
import cv2
import glob
import json
import numpy as np
import matplotlib.pyplot as plt
import os


# settings
font = cv2.FONT_HERSHEY_SIMPLEX


def draw_results(frame, tracking_results, frame_idx):
    type_num = len(tracking_results.keys())

    cmap = plt.get_cmap('rainbow')
    _colors = np.array([cmap(float(i/(type_num-1))) for i in range(type_num)])
    colors = 255 * _colors[:,:3]

    for i, data in enumerate(tracking_results.items()):
        name, bboxes = data
        bbox = bboxes[frame_idx]
        c = tuple((int(colors[i,2]), 
                   int(colors[i,1]), 
                   int(colors[i,0])))

        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        cv2.rectangle(frame, p1, p2, c, 2, 1)
        cv2.putText(frame, name, (10, (i+1) * 20), font, 0.5, c)

    return frame


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='compare_results.py',
        add_help=True,
    )
    parser.add_argument('-v', '--video', type=str, required=True)
    
    # parse args
    args = parser.parse_args()
    video_path = args.video
    if not os.path.exists(video_path):
        raise Exception(video_path + ' does not exist.')
    video_bname = os.path.basename(video_path)

    # initialize
    in_video = cv2.VideoCapture(video_path)
    im_w = int(in_video.get(cv2.CAP_PROP_FRAME_WIDTH))
    im_h = int(in_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = in_video.get(cv2.CAP_PROP_FPS)
    frame_num = in_video.get(cv2.CAP_PROP_FRAME_COUNT)

    out_fpath = './{}_compare.mp4'.format(video_bname[:-4])
    out_video = cv2.VideoWriter(out_fpath, 
        cv2.VideoWriter_fourcc('m','p','4','v'), int(fps), (im_w, im_h))

    # load results
    tracking_results = {}
    result_files = glob.glob('./{}*.json'.format(video_bname[:-4]))
    for result_file in result_files:
        fin = open(result_file, 'r')
        ret_dict = json.load(fin)
        name = ret_dict['tracking method']
        bboxes = ret_dict['result bboxes']
        tracking_results[name] = bboxes

    # show the results
    frame_cnt = 0
    while(in_video.isOpened()):
        ret, frame = in_video.read()
        if not ret:  # end of the frame
            break
  
        # update window  
        frame_disp = np.copy(frame)
        frame_disp = draw_results(frame_disp, tracking_results, frame_cnt)
        cv2.imshow('frame', frame_disp)
        out_video.write(frame_disp)

        # key input
        k = cv2.waitKey(33)
        if k == 27 or k == ord('q'):
            break
        
        frame_cnt += 1

    in_video.release()
    out_video.release()
    cv2.destroyAllWindows()


import cv2
import numpy as np
import argparse
# grab references to the global variables 
pts = [] 

def click_and_crop(event, x, y, flags, param):
    
    global pts
	# if the left mouse button was clicked, record the starting
	# (x, y) coordinates and indicate that cropping is being
	# performed
    if event == cv2.EVENT_LBUTTONDOWN:
        pts.append((x, y))
        cv2.circle(image, (x,y), 5, (0, 255, 0), -1)
        cv2.imshow("image", image)


def crop():
    if args.rpi is not None:
        rpi_name = args.rpi
    else:
        rpi_name = "1"
    ROIs = {"rpi_{}".format(rpi_name):[]}

    # Click on points counter-clockwise starting from top left

    # load the image, clone it, and setup the mouse callback function
    global image, pts, clone
    if args.input_path is not None:
        image = cv2.imread(args.input_path)
    else:
        image = cv2.imread('calibration.jpg')
    clone = image.copy()
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)
        
    # keep looping until the 'q' key is pressed
    while True:
        # display the image and wait for a keypress
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        
        # if the 'r' key is pressed, reset the cropping region
        if key == ord("r"):
            image = clone.copy()
            pts = []
        
        # if the 'c' key is pressed, break from the loop
        elif key == ord("c"):
            if len(pts) != 4:
                print('Only 4 points are acceptable')
            else:
                print(pts)
                ROIs["rpi_{}".format(rpi_name)] = pts

                src = np.array(pts, dtype = np.float32)
                dst = np.float32([(0, 0), (0, 512), (512, 512), (512, 0)])
                M = cv2.getPerspectiveTransform(src, dst)
                processed = cv2.warpPerspective(clone, M, (512, 512))
                
                pts = np.array(pts)
                rect = cv2.boundingRect(pts)
                x,y,w,h = rect
                crop_rect = clone[y:y+h, x:x+w].copy()
                
                # (2) make mask
                pts = pts - pts.min(axis=0)
                
                mask = np.zeros(crop_rect.shape[:2], np.uint8)
                cv2.drawContours(mask, [pts], -1, (255, 255, 255), -1, cv2.LINE_AA)
                
                ## (3) do bit-op
                crop = cv2.bitwise_and(crop_rect, crop_rect, mask = mask)

                cv2.imshow("crop", crop)
                cv2.imshow("processed", processed)
        
        elif key == ord("q"):
            break              

    # Save to txt and close all open windows
    path = ""
    if args.output_path is not None:
        path = args.output_path
    else:
        path = "ROIs.txt"
    with open(path,"w+") as f:    
        for key, value in ROIs.items():
            f.write('%s: %s\n' % (key, value))

    cv2.destroyAllWindows()

               
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculate calibration parameters for preprocessing module')
    parser.add_argument('-i','--input_path', help='input path of image for calibration')
    parser.add_argument('-o','--output_path', help='output path for saving calibration results')
    parser.add_argument('-rpi', help='rpi name prefix')
    args,_ = parser.parse_known_args()

    crop()

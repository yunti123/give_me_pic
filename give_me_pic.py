from webdriver_manager.firefox import GeckoDriverManager
from multiprocessing import JoinableQueue
from selenium import webdriver
from threading import Thread
from pytube import YouTube
from time import sleep
from PIL import Image
import urllib
import shutil
import yaml
import cv2
import os


with open('./config.yml') as conf:
    config = yaml.load(conf, Loader=yaml.FullLoader)

MAX_VIDEO = config['MAX_VIDEO_PER_KEYWORD']
FRAME_RATE = config['FRAME_RATE']
img_path = config['IMG_OUT_PATH']
kws = config["KEY_WORDS"]

video_path = config['VIDEO_DOWNLOAD_PATH']
tmp_path = config['TMP_PATH']
  

options = webdriver.FirefoxOptions()
options.set_headless()
browser = webdriver.Firefox(executable_path=GeckoDriverManager().install(),options=options)

urls = JoinableQueue()
paths = JoinableQueue()
names = JoinableQueue()
keys = JoinableQueue()


def download():
    
    while True:
        try:
            print("\nvideo capturing")
            
            # get url from queue        
            url = urls.get()
            # get video from url
            yt = YouTube(url)
            sleep(1)
            title = yt.title
            # get stream parameters for 480p
            stream = yt.streams.get_by_itag(135)

            print("\n" + title + " downloading ...\n")

            # start dowmload
            stream.download(video_path)

            print("\n" + title+" dowloaded\n")

            # move to tmp    
            lis = os.listdir(video_path)
            if not len(lis) <= 1:
                if not lis[0] == "tmp":
                    temp = lis[0]
                else:
                    temp = lis[1]
                
                src = video_path + os.sep + temp
                des = tmp_path + os.sep + temp
                shutil.move(src,des)        
                names.put(temp)        
                paths.put(des)
        except:
            print("An error occur on try to download: {}".format(url))
            pass        

        urls.task_done()

def give_me_image():

    while True:

        video_p = paths.get()
        name = names.get()
        name = name.split(".")[0]
        index = 0
        sample = 0

        print("\nimage converting started\n")
        # read video
        video = cv2.VideoCapture(video_p)
        
        # take image from video
        succ,image = video.read()

        while succ:

            img_des_dir = img_path + os.sep + name
            
            if not os.path.exists(img_des_dir):
                os.makedirs(img_des_dir)
            
            # take image from video
            # save image every FRAME_RATE. frame
            succ,image = video.read()

            if index > 100 and index%FRAME_RATE == 0:
                            
                img_des = img_des_dir + os.sep +"{}.jpg".format(sample)
                cv2.imwrite(img_des,image)
                sleep(0.001)
                try:
                    img = Image.open(img_des)
                    img.save(img_des,quality=85, optimize = True)
                except IOError:
                    print("IO Error on 105")
                    os.remove(img_des)
  
                sample += 1

            index += 1
                
        print("\nimage converting finished")
        
        # end of the save images delete the source video
        video.release()
        sleep(1)
        os.remove(video_p)
        print("\nVideo deleted\n")

        paths.task_done()
        names.task_done()

    

def find_link():

    while True:    


        query_header = "https://www.youtube.com/results?search_query="
        
        search = keys.get()
         
        query = urllib.parse.quote(search)
        url = query_header + query

        browser.get(url)
        sleep(1)

        count = 0
        for ret in browser.find_elements_by_id("thumbnail"):
            try:
                if ret.get_attribute('class') == "yt-simple-endpoint inline-block style-scope ytd-thumbnail":
                    temp = ret.get_attribute('href')
                    if temp != None:
                        urls.put(temp)
                        count += 1
                        if count >= MAX_VIDEO:
                            break
            except:
                pass

        
        keys.task_done()
        


if __name__ == "__main__":

    if not os.path.exists(video_path):
        os.makedirs(video_path)

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    if not os.path.exists(img_path):
        os.makedirs(img_path)


    print("\nkeywords are fetching\n")

    
    for kw in kws:
        keys.put(kw)


    k = Thread(target = find_link)
    k.daemon = True

    d = Thread(target = download) 
    d.daemon = True

    i = Thread(target = give_me_image)
    i.daemon = True

    k.start()
    d.start()
    i.start()

    keys.join()
    urls.join()
    paths.join()
    names.join()

    try:
        shutil.rmtree(video_path)
    except OSError as e:
        print("Error: {} : {}".format(video_path, e.strerror))

    print("\nDone\n")

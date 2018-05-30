import os
import shutil
import cv2
import urllib
import urllib2
import glob

from pytube import YouTube
from threading import Thread
from Queue import Queue
from time import sleep
from bs4 import BeautifulSoup
from PIL import Image

MAX_LINK = 1
FRAME-RATE = 10
ADD_W = False

video_path = "./download"
tmp_path = "./download/tmp"
img_path = "./image"
plz = "./key.plz"
  

urls = Queue()
paths = Queue()
names = Queue()
keys = Queue()

"""

        Starting functions

"""

def download():
    
    while True:

        print("\nvideo capturing")
        
        # get url from queue        
        url = urls.get()
        # get video from url
        yt = YouTube(url)
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
            
            src = video_path + "/" + temp
            des = tmp_path + "/" + temp
            shutil.move(src,des)        
            names.put(temp)        
            paths.put(des)
                

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

            img_des_dir = img_path + "/" + name
            
            if not os.path.exists(img_des_dir):
                os.makedirs(img_des_dir)
            
            # take image from video
            succ,image = video.read()

            # save image every FRAME_RATE. frame
            if index > 2000 and index%FRAME_RATE == 0:
                            
                img_des = img_des_dir + "/" +"{}.jpg".format(sample)
                cv2.imwrite(img_des,image)
                img = Image.open(img_des)
                img.save(img_des,quality=85, optimize = True)
                
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
        
        add = ""
        query_header = "https://www.youtube.com/results?search_query="
        url_header = "https://www.youtube.com"
        search = keys.get() + add
         
        query = urllib.quote(search)
        url = query_header + query
        response = urllib2.urlopen(url)
        res = response.read()

        soup = BeautifulSoup(res,"lxml")
        count = 0
        for ret in soup.findAll(attrs = {'class':'yt-uix-tile-link'}):
            temp = url_header + ret['href']
            urls.put(temp)
            count += 1
            if count >= MAX_LINK:
                break
        
        
        keys.task_done()
        
"""

        Main Program

"""

if not os.path.exists(video_path):
    os.makedirs(video_path)

if not os.path.exists(tmp_path):
    os.makedirs(tmp_path)

if not os.path.exists(img_path):
    os.makedirs(img_path)


print("\nkeywords are fetching\n")

with open(plz) as f:
    for line in f:
        keys.put(line)


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


print("\nDone\n")

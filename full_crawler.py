import os
import re
import time
import argparse
import requests
import io
import hashlib
import itertools
import base64
from PIL import Image
from multiprocessing import Pool
from selenium import webdriver
import urllib.request

argument_parser = argparse.ArgumentParser(description='Download images using google image search')
argument_parser.add_argument('query', metavar='query', type=str, help='The query to download images from')
argument_parser.add_argument('--count', metavar='count', default=100, type=int, help='How many images to fetch')
argument_parser.add_argument('--label', metavar='label', type=str, help="The directory in which to store the images (images/<label>)", required=True)

def ensure_directory(path):
    if not os.path.exists(path):
        os.mkdir(path)

def largest_file(dir_path):
    def parse_num(filename):
        match = re.search('\d+', filename)
        if match:
            return int(match.group(0))

    files = os.listdir(dir_path)
    if len(files) != 0:
        return max(filter(lambda x: x, map(parse_num, files)))
    else:
        return 0



def fetch_image_urls(query, images_to_download):
    image_urls = list()

    # search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"
    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img&hs=cKf&sa=X&ved=0CAIQpwVqFwoTCPCHoOKnzfQCFQAAAAAdAAAAABAE&biw=1836&bih=965"
    browser = webdriver.Firefox()
    browser.get(search_url.format(q=query))
    def scroll_to_bottom():
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    image_count = len(image_urls)
    delta = 0
    while image_count < images_to_download:
        print("Found:", len(image_urls), "images")
        scroll_to_bottom()

        images = browser.find_elements_by_css_selector("img.rg_i")
        for img in images[:images_to_download]:
            img.click()
            time.sleep(1)
            fullImage = browser.find_elements_by_class_name("n3VNCb")
            for i in fullImage:
            	image_urls.append(i.get_attribute('src'))
            
        delta = len(image_urls) - image_count
        image_count = len(image_urls)
        image_urls = list(filter(lambda x: x.startswith("http"), image_urls))
        print(image_urls)

        if delta == 0:
            print("Can't find more images")
            break

        try:
            fetch_more_button = browser.find_element_by_css_selector(".ksb")
            if fetch_more_button:
                browser.execute_script("document.querySelector('.ksb').click();")
                scroll_to_bottom()
        except Exception as e:
            print("No end button")

    browser.quit()
    return image_urls

def persist_image(dir_image_src):
    label_directory = dir_image_src[0]
    image_src = dir_image_src[1]
    image_name = dir_image_src[2]

    print(image_src)
    size = (256, 512)

    try:
    	image = urllib.request.urlretrieve(image_src, label_directory + image_name + ".jpg")
    except Exception as ex:
    	print(ex)	

    #image_file = io.BytesIO(image_content)
    #image = Image.open(image_content).convert('RGB')
    #resized = image.resize(size)
    #file_name = label_directory + hashlib.sha1(image_content).hexdigest() + ".jpg"
    #with open(file_name, 'wb')  as f:
    #    image.save(label_directory + image_name + ".jpg", "JPEG", quality=100)
    #os.remove(file_name)
    return True



if __name__ == '__main__':

    POOL_SIZE = 12
    args = argument_parser.parse_args()

    ensure_directory('./images/')

    query_directory = './images/' + args.label + "/"
    ensure_directory(query_directory)

    image_urls = fetch_image_urls(args.query, args.count)

    values = [item + ("{}_{}".format(args.label, idx),) for idx, item in enumerate(zip(itertools.cycle([query_directory]), image_urls))]
    values = values[:args.count]
    print("Arg count: {}".format(args.count))
    print("image count", len(image_urls))

    pool = Pool(POOL_SIZE)
    results = pool.map(persist_image, values)
    print("Images downloaded: ", len([r for r in results if r]))

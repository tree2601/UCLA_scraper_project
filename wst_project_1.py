#!/usr/bin/env python
# coding: utf-8

# In[87]:


#!pip install bs4
#!pip install Flask
from flask import Flask,request
import urllib.request
from bs4 import BeautifulSoup
import time
import re
import heapq
import json
import os
app = Flask(__name__)
http = 'https://www.ucla.edu/'
path_url_info = 'C://UCLA//2021 Winter//wst//project//local//url_info'
path_inverted_index = 'C://UCLA//2021 Winter//wst//project//local//inverted_index'


# In[3]:


def crawl(url):
  try:
    response = urllib.request.urlopen(url,timeout=1.5)
    h = response.read()
    h = h.decode('utf-8')
    return h
  except: 
    print('Invalid url or time out')
    return None

def parse(html,url=None):
  soup = BeautifulSoup(html,"html.parser")
  out_urls = soup.find_all('a', href=True)
  out_urls_list = []
  for single_url in out_urls:
    href = single_url['href']
    if (bool(re.match('^https',href))):
      out_urls_list.append(href)
  
  title = None
  head = soup.head
  if soup.head is not None:
    title = soup.head.title
    if title is not None:
     title = title.text

  description = None
  if soup.head is not None:
    description = soup.head.find('meta',{"name" : "description"})
  try:
    if description is not None:
      #  if 'content' in description.keys():
           description = description['content']
  except:
    description = None
  
  text = soup.find('body')
  if text is not None:
    text = text.text
  x = {
     'url' :  url ,
    'title' :  title, 
     'description' : description,
     'text' : text, 
    'out_urls' : out_urls_list,

        }
  return x


# In[96]:


def BFS(url,max_depth=2):
  url_dict = {url:0}
  url_info = {}
  url_list = [url]
  index = 0
  while len(url_list) != 0:
    target_url = url_list.pop(0)
    
    time.sleep(0.1)
    if url_dict[target_url] < max_depth+1:
      
      target_html = crawl(target_url)
      if target_html is not None:
        
        target_info = parse(target_html,target_url)
        url_info[index] =target_info
        index = index +1

        for url in target_info['out_urls']:
          if url not in url_dict.keys():
            url_dict[url] = url_dict[target_url]+1
            url_list.append(url)
    

  return url_dict,url_info


# In[48]:


def url_word_score(url_info):
  word_score_set = {}
  for single_info in url_info:
    word_score_dic = {}
    info = url_info[single_info]
    
    title_content = None
    if (info['title'] is not None):
      title_content = info['title'].lower()
      title_content = re.sub(r'[^a-zA-Z0-9]', ' ',title_content ).split()
      for title_word in title_content:
        if title_word not in word_score_dic.keys():
          word_score_dic[title_word] = 200
        else:
          word_score_dic[title_word] = word_score_dic[title_word]+ 200

    description_content = None
    if (info['description'] is not None):
      description_content = info['description'].lower()
      description_content = re.sub(r'[^a-zA-Z0-9]', ' ',description_content ).split()
      for description_word in description_content:
        if description_word not in word_score_dic.keys():
          word_score_dic[description_word] = 10
        else:
          word_score_dic[description_word] = word_score_dic[description_word]+ 10

    text_content = None
    if (info['text'] is not None):
      text_content = info['text'].lower()
      text_content = re.sub(r'[^a-zA-Z0-9]', ' ',text_content).split()
      for text_word in text_content:
        if text_word not in word_score_dic.keys():
          word_score_dic[text_word] = 0.1
        else:
          word_score_dic[text_word] = word_score_dic[text_word]+ 0.1
    
    word_score_set[single_info] = word_score_dic


  return word_score_set


# In[6]:


def inverted_index(word_score_set):
  word_set = {}
  for url_int in word_score_set:
    single_set = word_score_set[url_int]
    for word in single_set:
      if word not in word_set.keys():
        word_set[word] = {}
        word_set[word][url_int] = single_set[word]
      else:
        word_set[word][url_int] = single_set[word]
  
  for single_word in word_set:
    m = min(10, len(word_set[single_word]))
    inverted_tuple = [(value, key) for key,value in word_set[single_word].items()]
    top_ten_tuple = heapq.nlargest(m,inverted_tuple)
    top_ten_tuple_inverted_back = [(key, value) for value,key in top_ten_tuple]
    #top_ten_dict = dict(top_ten_tuple_inverted_back)
    top_ten_dict= {}

    for single_tuple in top_ten_tuple_inverted_back:
      top_ten_dict[single_tuple[0]] = single_tuple[1]

    
    word_set[single_word] = top_ten_dict

  return word_set


# In[12]:


def naive_search(word,word_score_set,url_info):
  result_list = []
  url_score_dict = word_score_set[word]
  for url in url_score_dict:
    result_list.append(url_info[url])

  return result_list


# In[8]:


def search(word,inverted_index_path,url_info_path):
  word_score_set = read_from_json_inverted_index(inverted_index_path)
  url_info = read_from_json_url_info(url_info_path)
  
  result_list = []
  url_score_dict = word_score_set[word]
  for url in url_score_dict:
    result_list.append(url_info[url])

  return result_list


# In[9]:


def save_to_json(path,url_info):
    with open(path, 'w') as json_file:
        json.dump(url_info, json_file)
    print('json complete!')
    return None


# In[10]:


def read_from_json_url_info(path):
    with open(path) as json_file:
        result = json.load(json_file)
    new_result = {}
    for r in result.keys():
        new_result[int(r)] = result[r]
        
    print('Finished reading url info!')
    return new_result


# In[11]:


def read_from_json_inverted_index(path):
    with open(path) as json_file:
        result = json.load(json_file)
    new_result = {}
    for r in result.keys():
        score_list =result[r]
        new_list = {}
        for rr in score_list.keys():
            new_list[int(rr)] = score_list[rr]
        new_result[r] = new_list
        
    print('Finished reading inverted_index!')
    return new_result


# In[ ]:


#test
#a,b = BFS(http,max_depth = 3)
#c = url_word_score(b)
#e = inverted_index(c)
#save_to_json(path_url_info,b)
#save_to_json(path_inverted_index,e)

#f = read_from_json_url_info(path_url_info)
#g = read_from_json_inverted_index(path_inverted_index)


#x = naive_search('ucla',e,b)
#y = search('as',path_inverted_index,path_url_info)
#xx = search('ucla',path_inverted_index,path_url_info)


# In[93]:

@app.route('/search')
def search():
    keyword = request,args.get("keyword")
    temp_result = naive_search(keyword,test_inverted_index,test_url_info)
    
    url_title_description_list = []
    for single_info in temp_result:
        single_info_three=[]
        single_info_three.append(single_info['url'])
        single_info_three.append(single_info['title'])
        single_info_three.append(single_info['description'])
        url_title_description_list.append(single_info_three)
    return url_title_description_list


# In[92]:


if __name__ == "__main__":
    print('nmsl')
    test_url_info = read_from_json_url_info(path_url_info)
    test_inverted_index = read_from_json_inverted_index(path_inverted_index)
    app.run()


# In[ ]:





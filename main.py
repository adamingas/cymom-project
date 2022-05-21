# coding: utf-8

# Input required for script: 1. Facebook Group Admin's "Email address" 2. Facebook Group Admin's "Password" 3. User
# Access Token (Steps: https://docs.google.com/presentation/d/1J_TkY-Cd4AOJmbO-6KWB-A1mISJhk6YBh0gpAMiAFcc/edit#slide
# =id.g4ae885f2b5_0_13 ) 4. Group id - An integer which shows up in the homepage URL of group e.g.
# "https://www.facebook.com/groups/1662317732110904" has group id as "1662317732110904".
#

# Computer Requirements -
# 1. Python 2.7 needs to be installed on computer to run this script.
# Ref - https://www.python.org/download/releases/2.7/
# 2. Mozilla Firefox browser needs to be present on computer.
# Ref- https://www.mozilla.org/en-CA/firefox/new/
#

# <b>Facebook Group Sitemap Structure Analysis:</b>
#
# <img src="Facebook IWK.jpg">
# Image URL: https://docs.google.com/drawings/d/1pkL7UwRBGT4m2p73oD5k--eYB5GyoZ9Smw5YzqbBb7A/edit?usp=sharing

# Algorithm/Code Highlights:
#
# 1. Functions extract_posts(), extract_comments() and extract_replies() have been written to extract all data using
# Facebook API. These functions call each other to extract -
#     a. Combined content of posts/comments/replies.
#     b. A unique id for each post/comment/reply.
#     c. Their corresponding timestamps.
# An HTTPS GET request is sent to the Facebook for this data extraction.
#
# 2. Function user_values() is the core function that extract all other data which is not feasible with Facebook API.
# It uses Selenium to extract - a. All user ids of each post, comment and reply. b. Seen count of each post and exact
# user ids of users who have seen that post (seen count + user ids of users who have seen the post). c. All reactions
# (Like, Love, Haha, Wow, Sad, Angry, any special reactions that come around sometimes like Pride reaction etc.)
# along with the user ids of users who reacted is being extracted for each post, comment and reply. (reactions+ user
# ids pairs for each post/comment/reply).
#
# 3. Facebook has a complete Sitemap hierarchy for group, post, comment/reply, post seen list, reactions for post,
# reactions for comments/replies URLs -
#
#     a. group_url="https://www.facebook.com/groups/"+group_id+"/"
#
#     b. post_url="https://www.facebook.com/groups/"+group_id+"/"+post_id+"/"
#
#     c. comment_or_reply_url="https://www.facebook.com/groups/"+group_id+"/"+post_id+"/?comment_id="+ids
#
#     d. seen_url='https://www.facebook.com/ufi/group/seenby/profile/browser/?id='+post_id+'&av='+unique_id
#
# e. reactions_url='https://www.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier='+post_id+'&av='+unique_id
#
#     f. reactions_url='https://www.facebook.com/ufi/reaction/profile/browser/?ft_ent_identifier='+ids+'&av='+unique_id
#
#     g. "https://www.facebook.com/profile.php?id=" + "any user id" gives us profile of the particular person/user.
#
#
# 4. These variables names have been used as:
#     a. group_id: A unique group id.
#     b. post_id: A unique id for a particular post.
#     c. comment_id: A unique id for a particular comment or reply.
#     d. unique_id: A unique id for each Admin which creates the group (which is the user id/profile id of the Admin.)
#     e. ids: A unique id for a particular comment or reply.
#
# 5. Each URL is opened with Selenium making it possible to extract data one at a time from each page. This helps in
# overcoming the hidden "comment/reply/seen user ids/reaction user ids" issue.
#
# 6. This code also handles edge cases like no reactions, 0 seen counts etc and it also does exception handling if in
# case browser freezes, it will restart itself and resume from the same place.
#
#

# Import Tkinter for UI (User Interface)
# Help Doc for installing Tkinter before importing - https://tkdocs.com/tutorial/install.html

# In[1]:


# from Tkinter import *
# import Tkinter
# import tkMessageBox

# Import simple libraries for sending http/https requests and fetching data
# re library for regular expressions and json for handling json formats

# In[2]:


# import http.client as httplib
import json
# import re
import re
import time
# import httplib, urllib
# import urllib

import requests
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, ElementNotInteractableException
from bs4 import BeautifulSoup
from bs4.element import Tag, ResultSet
from collections import defaultdict
import pandas as pd

# Import selenium for browser automation.
# Help Docs for installing Selenium - https://pypi.org/project/selenium/
# Download GeckoDriver for Mozilla - https://github.com/mozilla/geckodriver/releases
# In[3]:
# import time for handling time components

# call_limit variable to restrict 200 calls per hour and to resume from the same place after an hour


call_limit = 0

# x variable to which we keep appending the extracted data from API to make the final data

# In[6]:


x = '{"data":\n  {'


# Restarts the browser each time Browser freezes. This function helps resume the data extraction from the same place.

# In[7]:


def restart_browser(driver, email_id, password):
	time.sleep(5)
	driver.close()
	time.sleep(5)
	driver = webdriver.Firefox()

	# setting a time limit of 15 seconds for data extraction from a webpage
	driver.set_page_load_timeout(15)
	driver.implicitly_wait(5)

	# opens Facebook homepage and logs in automatically
	finished = 0
	while finished == 0:
		try:
			driver.get('https://www.facebook.com/')
			print("Opened facebook...")
			time.sleep(5)
			accept_cookies = driver.find_element_by_id("u_0_h")
			accept_cookies.click()
			a = driver.find_element_by_id('email')
			a.send_keys(email_id)
			print("Email Id entered...")
			b = driver.find_element_by_id('pass')
			b.send_keys(password)
			print("Password entered...")
			c = driver.find_element_by_id('loginbutton')
			c.click()

			finished = 1

		except Exception as e:
			time.sleep(5)
			driver.close()
			time.sleep(5)
			driver = webdriver.Firefox()

	post_html_code = (driver.page_source).encode('utf-8')

	return driver


# Takes values from the UI, processes it and outputs the final data as json format in a text file.

# In[12]:

def facebook_login(driver, email_id, password):
	# opens Facebook homepage and logs in automatically
	driver.get('https://www.facebook.com/')
	print("Opened facebook...")
	time.sleep(5)
	accept_cookies = driver.find_element_by_id("u_0_h")
	accept_cookies.click()
	a = driver.find_element_by_id('email')
	a.send_keys(email_id)
	print("Email Id entered...")
	b = driver.find_element_by_id('pass')
	b.send_keys(password)
	print("Password entered...")
	c = driver.find_element_by_id('u_0_b')
	c.click()
	return driver


def parse_posts_from_api(list_of_posts, driver,df_dict):
	"""
	Uses a list of posts retrieved using the Facebook API to call get_post_info which navigates to the post's url
	using selenium to retrieve the data.
	TODO: Set up database here and store results of parsing
	TODO: If updated-date of post in list_of_posts is the same as that of the dictionary then don't parse that post
	TODO: Find best waiting time for selenium to wait before visiting website, to prevent it being caught by facebook

	:param list_of_posts: list of dict retrieved using Facebook API
	:param driver: webdriver
	:return:
	"""
	is_posts_df_empty =  df_dict["posts"].empty

	group_dict = defaultdict(list)  # keys: [post_dict, parsed_comments, parsed_replies,parsed_tags]
	for post in list_of_posts:
		print(post["id"])
		print(post.get("message"))
		if is_posts_df_empty or not ((df_dict["posts"]["post_id"] == post["post_id"]) &
								 (df_dict["posts"]["updated_time"] == post["updated_time"]) ).any():

			page_dict = get_post_info(driver, post)
			for key, value in page_dict.items():
				group_dict[key].extend(value)
		else:
			continue
	return group_dict


def user_values(config):
	token = config["access_token"]
	group_id = config["groupid"]
	email_id = config["email"]
	password = config["password"]
	# extract_posts is the function which returns all Facebook Group data from API.
	list_of_posts = extract_posts(token, group_id)
	assert isinstance(list_of_posts, list)

	driver = webdriver.Firefox()

	# setting a time limit of 15 seconds for data extraction from a webpage
	driver.set_page_load_timeout(15)
	driver.implicitly_wait(5)

	driver = facebook_login(driver, email_id, password)
	driver.get("https://m.facebook.com")
	time.sleep(5)

	# Setting up the dataframe to store results in
	# posts_df, comments_df, replies_df, tags_df, reactions_df =
	df_dict = open_dataframes()

	parse_posts_from_api(list_of_posts, driver,df_dict)

	return driver


# extract_posts function extracts all posts' content and further calls extract_comments and extract_replies function to
# extract comments and replies content as well. It returns -
# 1. Combined content of posts/comments/replies.
# 2. A unique id for each post/comment/reply.
# 3. Their corresponding timestamps.
#
# An HTTPS GET request is sent to the Facebook for this data extraction. This complete task is done by using
# Facebook API.
#
# Note: content here means the post/comment/reply itself.

# In[13]:
def open_dataframes():
	"""
	Opens dataframes for posts, comments, replies, tags and reactions
	:return:
	"""
	dataframes = []
	keys = ["posts", "comments", "replies", "tags", "reactions"]
	for i in keys:
		try:
			dataframes.append(pd.read_csv(i+".csv"))
		except (pd.errors.EmptyDataError, FileNotFoundError):
			dataframes.append(pd.DataFrame())
	return dict(zip(keys,dataframes))

def extract_posts(token, group_id):
	"""
	Uses Facebook's Graph API to download information about posts posted in the group.
	:param token: str, The access token of the admin of the group
	:param group_id:str/int, the id of the group
	:return:list of posts, where each post is a dictionary with the following keys:
			[id,created_time,message,full_picture,updated_time]
	"""
	global x
	global call_limit

	# Establish https connection with Facebook API.
	# Checking call limit of 195 calls. Facebook allows 200 calls/hour. But we considered 195 calls to be on safe side.
	# Once the call limit is reached, it resumes API calls again after 3660 seconds or 61 minutes.

	call_limit = call_limit + 1
	if call_limit == 195:
		time.sleep(3660)
	# We pass the request Parameters as arguments to the get function of the requests library
	req = requests.get('https://graph.facebook.com/{}/feed/'.format(group_id), params={
		"fields": "created_time,message,full_picture,updated_time",
		# Limit is the number of posts to fetch using the api. Not specifiying it will return 25 popsts. 500 gives out an
		# error, so we use 400
		"limit": 400,
		'access_token': token
	})
	response = req.json()
	try:
		data = response["data"]
	except KeyError:
		print("Most probably you need to update your Authentication token")
		print(response)
		raise KeyError
	req.close()
	# TODO: Clean up this mess after done with posts
	# num_of_posts = len(data)
	# if num_of_posts > 0:
	# 	for n in range(m):
	#
	# 			post = data["feed"]["data"][n]
	# 			k = post.get("message",b"")
	#
	# 			if k:
	# 				# try:
	# 				# 	k = k.decode('utf-8')
	# 				# except Exception as e:
	# 				# 	print(k)
	# 				# 	print("Exception " + str(e))
	# 				time_stamp = str(post["updated_time"])
	# 				post_id = str(post["id"])
	# 				x = x + '\n\n   {"post":"' + k + '",' + '"post_id":' + post_id + ',' + '"time_stamp":' + time_stamp + '},'
	# 				print("~"*20)
	#
	# 				extract_comments(token, post_id)
	#
	# 				x = x + "\nZZENDZZAA1214"
	#
	# 	x = x + '\n  }'
	# print(x)
	return data


def expand_all_comments(driver):
	# Expands all comments.

	replies_list = driver.find_elements_by_css_selector("a[data-sigil='ajaxify']")

	# Clicking on all show more links
	for show_more in replies_list:
		try:
			show_more.click()
		except StaleElementReferenceException:
			print("Nothing to click")
			continue
	return driver


def get_post_info(driver: webdriver, post_dict: dict):
	"""
	Uses selenium to retrieve reactions from all levels of posting and BeautifulSoup to parse the html page of the post,
	creating a dictionary for each post, comment, reply, and tag
	:param driver: Seleium web driver
	:param post_dict: Dictionary with information about the post
	:return:
	"""
	# TODO: Work on this next time
	# Go through each post url and:
	# 	click on all reply links
	# 	get the name of the poster
	#  	get all comments and who posted them
	# Keys in the post_dict are "id", "created_time", "message", "full_picture"
	url = "https://m.facebook.com/%s" % post_dict["id"]
	driver.get(url)
	driver = expand_all_comments(driver)
	page_source = driver.page_source
	page_dict = parse_post(page_source)

	# Merging parsed post dict with the one obtained through Facebook API
	page_dict["post_dict"][0] = {**page_dict["post_dict"][0], **post_dict}
	# TODO: Get reactions with selenium
	return page_dict


def parse_post(page_source):
	"""
	Parses post using BeautifulSoup, with the aim of retrieving post info, comments, replies, and tags
	:param page_source:
	:return: dict with keys:[post_dict, parsed_comments, parsed_replies,parsed_tags]
	"""
	parsed_comments = []
	parsed_replies = []
	parsed_tags = []
	soup = BeautifulSoup(page_source, features="html.parser")
	post_body = soup.find(class_="story_body_container")
	poster_url = post_body.select("[href]")[0].attrs["href"]
	poster_name = post_body.strong.a.text
	try:
		post_figure_container = post_body.select("i[aria-label^=Image]")
		if len(post_figure_container) > 1:
			post_figure_url, post_figure_label, post_figure_contains = [], [], []
			for i, figure in enumerate(post_figure_container):
				post_figure_url.append(figure.find_parent("a").attrs["href"])
				post_figure_label.append(figure.attrs["aria-label"])
				post_figure_contains.append(re.split(",| and ", re.sub(".*: ", "", post_figure_label[i])))
		else:
			post_figure_container = post_figure_container[0]
			post_figure_url = post_figure_container.find_parent("a").attrs["href"]
			post_figure_label = post_figure_container.attrs["aria-label"]
			post_figure_contains = re.split(",| and ", re.sub(".*: ", "", post_figure_label))
	except IndexError:
		post_figure_url = None
		post_figure_contains = None

	post_url = soup.find_all(attrs={"data-sigil": re.compile("m-feed-voice-subtitle")})[0]. \
		find(attrs={"href": re.compile("")}).attrs["href"]
	post_id = int(post_url.split("/")[6])
	post_body_container = soup.find(class_="story_body_container").p
	if post_body_container == None:
		post_text = ""
		post_tags=  []
	else:
		post_text = post_body_container.text
		post_tags = post_body_container.select("[href*=groupid]")
	comments_list = soup.find_all(attrs={"data-sigil": "comment"})
	# Getting number of reactions which are in text form.
	# This might include your own reaction and/or a friend's reaction, thus we first split the string on "," and "and"
	# i.e. "You, Adamos and 56 others" => ["You"," Adamos "," 56 others"]
	# We then get the last element and remove non numeric characters and convert it into an integer
	reaction_string = soup.find(class_="_1g06").text
	reaction_list = re.split(",|and", reaction_string)
	others = reaction_list[-1]
	others_int = int(re.sub("[^0-9]", "", others))
	post_number_of_reactions = len(reaction_list) - 1 + others_int
	post_dict = {"post_id": post_id,
				 "poster_name": poster_name,
				 "poster_url": poster_url,
				 "post_text": post_text,
				 "number_of_coments": len(comments_list),
				 "number_of_replies": 0,
				 "number_of_reactions": post_number_of_reactions,
				 "number_of_tags": len(post_tags),
				 "post_figure_url": post_figure_url,
				 "post_figure_contains": post_figure_contains
				 }

	for tag in post_tags:
		parsed_tags.append({
			"id": post_id,
			"tag_poster_name": poster_name,
			"tag_poster_url": poster_url,
			"tagged_user_name": tag.text,
			"tagged_user_url": tag.attrs["href"]
		})
	for comment in comments_list:
		# All of this is done just to get the post id, which can also be found in the current url of the driver
		# post_id		 = json.loads(comment.attrs["data-store"].replace("'", "\""))["token"].split("_")[0]
		comment_id = int(comment.attrs["id"])
		comment_container = comment.find(class_="_2b04")

		# Number of reactions are in a container next to the parent of the comment body, inside a class named _14va
		# Another function will be used to
		try:
			number_of_reactions = int(comment.find(class_="_14va").text)
		except ValueError:
			number_of_reactions = 0

		comment_poster_info = comment.find(class_="_2b05")
		comment_poster_url = comment_poster_info.a.attrs["href"]
		comment_poster_name = comment_poster_info.text

		# If the container next to the one that has the users info does not have the attribute data-sigil
		# then that means there is no text in the comment. This can happen if users respond with gifs
		if comment_poster_info.next_sibling.attrs.get("data-sigil"):
			comment_body = comment.find(attrs={"data-commentid": comment_id})
			comment_text = comment_body.text
			comment_tags = comment_body.select("[href*=groupid]")
			unique_comment_tags = get_unique_tags(comment_tags, parent_poster=(poster_name, poster_url))
		else:
			comment_text = ""
			comment_tags, unique_comment_tags = [], []

		# TODO: Actually Check this works retrieving images in comments. It has only been tested for replies and posts
		try:
			comment_figure_container = comment.find(class_="_14v5").select("i[aria-label^=Image]")
			if len(comment_figure_container) > 1:
				comment_figure_url, comment_figure_label, comment_figure_contains = [], [], []
				for i, figure in enumerate(comment_figure_container):
					comment_figure_url.append(figure.find_parent("a").attrs["href"])
					comment_figure_label.append(figure.attrs["aria-label"])
					comment_figure_contains.append(re.split(",| and ", re.sub(".*: ", "", comment_figure_label[i])))
			else:
				comment_figure_container = comment_figure_container[0]
				comment_figure_url = comment_figure_container.find_parent("a").attrs["href"]
				comment_figure_label = comment_figure_container.attrs["aria-label"]
				comment_figure_contains = re.split(",| and ", re.sub(".*: ", "", comment_figure_label))
		except IndexError:
			comment_figure_url = None
			comment_figure_contains = None

		replies_list = comment.find_all(attrs={"data-sigil": "comment inline-reply"})
		comment_dict = {"comment_id": comment_id,
						"post_id": post_id,
						"poster_name": poster_name,
						"poster_url": poster_url,
						"comment_poster_name": comment_poster_name,
						"comment_poster_url": comment_poster_url,
						"comment_text": comment_text,
						"number_of_replies": len(replies_list),
						"number_of_reactions": number_of_reactions,
						"number_of_tags": len(comment_tags),
						"number_of_unique_tags": len(unique_comment_tags),
						"comment_figure_url": comment_figure_url,
						"comment_figure_contains": comment_figure_contains
						}
		post_dict["number_of_replies"] += len(replies_list)
		parsed_comments.append(comment_dict)
		for tag in unique_comment_tags:
			parsed_tags.append({
				"id": comment_id,
				"tag_poster_name": comment_poster_name,
				"tag_poster_url": comment_poster_url,
				"tagged_user_name": tag.text,
				"tagged_user_url": tag.attrs["href"]
			})
		for reply in replies_list:
			reply_id = int(reply.attrs["id"])

			reply_body = reply.find(attrs={"data-sigil": "comment-body"})
			reply_text = reply_body.text
			reply_poster_info = reply_body.previous_sibling
			reply_poster_url = reply_poster_info.select("[href]")[0].attrs["href"]
			reply_poster_name = reply_poster_info.text
			try:
				numb_of_reply_reacts = int(reply.find(class_="_14va").text)
			except ValueError:
				numb_of_reply_reacts = 0

			try:
				reply_figure_container = reply.select("i[aria-label^=Image]")
				if len(reply_figure_container) > 1:
					reply_figure_url = []
					reply_figure_label = []
					reply_figure_contains = []
					for i, figure in enumerate(reply_figure_container):
						reply_figure_url.append((figure.parent.attrs["href"]))
						reply_figure_label.append(reply_figure_container.attrs["aria-label"])
						reply_figure_contains.append(re.split(",| and ", re.sub(".*: ", "", reply_figure_label[i])))
				else:
					reply_figure_container = reply_figure_container[0]
					reply_figure_url = reply_figure_container.parent.attrs["href"]
					reply_figure_label = reply_figure_container.attrs["aria-label"]
					reply_figure_contains = re.split(",| and ", re.sub(".*: ", "", reply_figure_label))
			except IndexError:
				reply_figure_url = None
				reply_figure_contains = None

			# A list of people tagged in the comment
			reply_tags = reply_body.select("[href*=groupid]")
			unique_reply_tags = get_unique_tags(reply_tags, parent_poster=(comment_poster_name, comment_poster_url),
												grandparent_poster=(poster_name, poster_url))
			reply_dict = {
				"reply_id": reply_id,
				"post_id": post_id,
				"poster_name": poster_name,
				"poster_url": poster_url,
				"comment_id": comment_id,
				"comment_poster_name": comment_poster_name,
				"comment_poster_url": comment_poster_url,
				"reply_poster_name": reply_poster_name,
				"reply_poster_url": reply_poster_url,
				"reply_text": reply_text,
				"number_of_reactions": numb_of_reply_reacts,
				"number_of_tags": len(reply_tags),
				"number_of_unique_tags": len(unique_reply_tags),
				"reply_figure_url": reply_figure_url,
				"reply_figure_contains": reply_figure_contains
			}
			parsed_replies.append(reply_dict)

			for tag in unique_reply_tags:
				parsed_tags.append({
					"id": reply_id,
					"tag_poster_name": reply_poster_name,
					"tag_poster_url": reply_poster_url,
					"tagged_user_name": tag.text,
					"tagged_user_url": tag.attrs["href"]
				})
	return dict(post_dict=[post_dict], parsed_comments=parsed_comments, parsed_replies=parsed_replies,
				parsed_tags=parsed_tags)


def get_unique_tags(tags, parent_poster=(None, None), grandparent_poster=(None, None)):
	"""
	Gets tag string which contains link to tagged person as well as name. If the tagged person is the same as the parent
	of the comment then the tag is not a "true" tag of a third person but a reply.
	i.e. if user Orestis replies to a comment made by user Avramis in a post by the user Giorgos, and tags Avramis and
	Adamos then: The parent of the comment is Avramis
				 The grandparent of the comment is Giorgos
				 The tag on user Avramis is considered a reply
				 The tag on user Adamos is considered a "true" tag
	:param tags: ResultSet (accessed like a list) with href and name of tagged user
	:param parent_poster: tuple of (name,url) of poster at one level above the current setting
					   (reply -> commenter, comment->poster)
	:param grandparent_poster: tuple of (name,url) of poster two levels above the current (reply -> poster)
	:return: dict of true tag
	"""
	assert isinstance(tags, ResultSet)
	unique_tags = ResultSet([])
	for t in tags:
		if t.attrs["href"] != parent_poster[1] and t.attrs["href"] != grandparent_poster[1]:
			unique_tags.append(t)

	return unique_tags


# Tkinter library provides support for user intreface.
# It takes -
# 1. Facebook Group Admin's "Email address"
# 2. Facebook Group Admin's "Password"
# 3. User Access Token
# 4. Group id
# from user in a textbox and passes it over to user_values() function to use further.

# In[16]:
if __name__ == "__main__":
	config = json.load(open("config.json", "r"))
	user_values(config)
	driver = webdriver.Firefox()
	driver = facebook_login(driver, config["email"], config["password"])

	# TODO: Work on getting reactions
	reaction_links = driver.find_elements_by_css_selector("a[href^='/ufi/reaction']")
	try:
		reaction_links[3].click()
	except ElementNotInteractableException:
		pass
	driver.back()
# top = Tkinter.Tk()
# L1 = Label(top, text="Facebook Data Extractor", ).grid(row=0, column=1)
#
# L2 = Label(top, text="Access Token", ).grid(row=1, column=0)
# E1 = Entry(top, bd=5)
# E1.grid(row=1, column=1)
#
# L3 = Label(top, text="FB Group Id", ).grid(row=2, column=0)
# E2 = Entry(top, bd=5)
# E2.grid(row=2, column=1)
#
# L4 = Label(top, text="Email ID", ).grid(row=3, column=0)
# E3 = Entry(top, bd=5)
# E3.grid(row=3, column=1)
#
# L5 = Label(top, text="Password", ).grid(row=4, column=0)
# E4 = Entry(top, bd=5)
# E4.grid(row=4, column=1)
#
# B = Button(top, text="Collect Data", command=user_values).grid(row=5, column=1, )
#
# Button(top, text="Quit", command=top.destroy).grid(row=6, column=1, )
# top.mainloop()
#

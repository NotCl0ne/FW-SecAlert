#!/usr/bin/python3
from telegram.ext import Updater
from bs4 import BeautifulSoup
import requests
import re
import yaml
from constants import BOT_TOKEN,CHAT_ID

#import os
#os.chdir('/home/antqt/Security-Alert/')
def send(messages):
	updater = Updater(token=BOT_TOKEN, use_context=True)
	for message in messages:
		updater.bot.send_message(chat_id=CHAT_ID, text=message)

def load_urls(links_path):
	with open(links_path) as f:
		data = yaml.load(f,Loader=yaml.FullLoader)
	return data

def load_config(yaml_path):
	with open(yaml_path) as f:
		config = yaml.load(f,Loader=yaml.FullLoader)
		host=config['host']
		tuple_recognize=config['tuple_recognize']

		data_location=config['data_location']
		number_rows=config['number_rows']

		report_location=config['report_location']
		api_link=config['api_link']
		message_format=config['message_format']

	return host,tuple_recognize,data_location,number_rows,report_location,api_link,message_format


def get_current_record(tuple_recognize,data_location,number_rows,url,api_link):
	tuples=[]
	records={}

	session = requests.session()

	if(api_link==""):
		response = BeautifulSoup(session.get(url).text, "html.parser")
		raw_data=response.find_all(tuple_recognize[0])

		for data in raw_data:
			while '\n' in data.contents: data.contents.remove('\n')
			tuples.append(''.join(str(_) for _ in data.contents))
		
		for _tuple in tuples:
			if (any(feature not in _tuple for feature in tuple_recognize[1:])):
				tuples.remove(_tuple)

		for _tuple in tuples:
			data=[]
			data_on_1_line={}
			for _data_location in data_location:
				data.append(re.findall(data_location[_data_location],_tuple)[0])
			data_on_1_line[data[0]]=data[1:]
			records.update(data_on_1_line)		
	
	else:
		all_res = session.get(api_link).json()
		all_tuples=all_res[tuple_location]

		for _tuple in all_tuples:
			data_list=[]
			data_on_1_line={}
			for _data_location in data_location:
				data_element ="" if data_location[_data_location] == "" else _tuple[data_location[_data_location]]
				data= "Pending" if data_element == None else data_element
				data_list.append(data)
			data_on_1_line[data_list[0]]=data_list[1:]
			records.update(data_on_1_line)

	return dict(list(records.items())[:number_rows])

def get_old_record(location):
	try:
		with open(location) as f:
			records = yaml.load(f,Loader=yaml.FullLoader)
	except:
		print("Can't find old records!")
		records={}

	return records

def write_yaml(destination,content):
	with open(destination, 'w') as file:
		yaml.dump(content, file)

def format_message(host,dictionary,message_format):
	message_list=[]
	for element in dictionary:
		link = dictionary[element][0] if 'https://' in dictionary[element][0] else host+dictionary[element][0]
		message=message_format.format(link,element)
		for _element in dictionary[element][1:]:
			message+='\n\n[+]: {}'.format(_element)
		message_list.append(message)
	return message_list


if __name__ == '__main__':
	urls = load_urls('resources/links.yaml')
	for url in urls:
		host,tuple_recognize,data_location,number_rows,report_location,api_link,message_format=load_config(urls[url])	
		old_record=get_old_record(report_location)
		current_record=get_current_record(tuple_recognize,data_location,number_rows,url,api_link)
		diff = { index : current_record[index] for index in set(current_record) - set(old_record) }

		if(len(diff)!=0):
			message_list=format_message(host,diff,message_format)
			send(message_list)
			write_yaml(report_location,current_record)
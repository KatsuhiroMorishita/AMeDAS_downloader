#!usr/bin/python3
# -*- coding: utf-8 -*-
#----------------------------------------
# name: get_today_list
# purpose: 気象庁のアメダス観測データの1時間毎に発表される準リアルタイムデータのダウンロードに必要なパラメータを取得する
# author: Katsuhiro MORISHITA, 森下功啓
# created: 2015-08-19
# lisence: MIT
#----------------------------------------
import urllib.request
import re
import time


today_list = []
url = "http://www.jma.go.jp/jp/amedas_h/map"
for i in range(10, 66):
	_url = url + str(i) + ".html"
	print(_url)

	html = None
	try:
		response = urllib.request.urlopen(_url)
		html = response.read()
		#print(html)
	except:
		pass

	if html != None:
		html = html.decode("utf-8")
		#print(html)
		p = re.compile("<area shape='rect' alt='(?P<name>.+)' coords='.+' href='today-(?P<_id>\d+).html\?areaCode=(?P<area_code>\d+)&groupCode=(?P<group_code>\d+)'/>")
		match = p.findall(html)
		for mem in match:
			if mem not in today_list:
				today_list.append(mem)
	time.sleep(0.2)



with open("today_list.csv", "w", encoding="utf-8-sig") as fw:
	for mem in today_list:
		name, _id, area_code, group_code = mem
		s = "\t".join(mem)
		fw.write(s)
		fw.write("\n")

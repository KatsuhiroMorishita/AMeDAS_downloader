#!usr/bin/python3
# -*- coding: utf-8 -*-
#----------------------------------------
# name: get_today_list
# purpose: 気象庁のアメダス観測データの1時間毎に発表される準リアルタイムデータのダウンロードに必要なパラメータを取得する
# author: Katsuhiro MORISHITA, 森下功啓
# created: 2015-08-19
# lisence: MIT
#----------------------------------------
import requests
import re
import time


def read_group_members():
	""" 観測ブロック名とそこに属する観測所名の一覧を読み込む
	"""
	groups_info = {}
	with open("amedas_group.csv", "r", encoding="utf-8-sig") as fr:
		lines = fr.readlines()
		for line in lines:
			print(line)
			line = line.rstrip()
			field = line.split("\t")
			print(field)
			group_name = field[0]
			members = field[1:]
			internal_dict = {}
			names = set()
			for mem in members:
				print(mem)
				block_no, name = mem.split("_")
				internal_dict[name] = block_no
				names.add(name)
			groups_info[group_name] = [internal_dict, names]
	return groups_info


def get_block_no(groups_info, target_names, target_name):
	"""
	同名の観測所は複数あるが、近傍の観測所の名前までは同じではなかろうという希望的観測を基に、観測所のブロック番号（観測所毎にユニークな番号）を返す
	エラーが出ないことを祈るw
	Argv:
		groups_info <dict>
		target_names <set>
		target_name <str>
	"""
	#print(target_names, target_name)
	group_score = {}
	scores = []
	for group_name in groups_info:
		internal_dict, names = groups_info[group_name]
		if target_name in names:
			#if target_name == "竜王山":
			#	print("names: ", names)
			_score = len(names.intersection(target_names))
			#print(_score)
			scores.append(_score)
			group_score[_score] = group_name
	if len(scores) > 0:                        # 検査対象の観測所名しか合致しない場合は1だが、1は何かおかしい（例えば、過去の観測データには無いが最新の観測データはあるなど。考えづらいが。）
		score_max = max(scores)
		group_name = group_score[score_max]
		#print(group_name)
		internal_dict, names = groups_info[group_name]
		return internal_dict[target_name]
	else:
		print("--error no match--", print(target_names, target_name))
		exit()



# 観測所のリストを取得する
groups_info = read_group_members()
today_list = set()
block_no_set = set()
url = "http://www.jma.go.jp/jp/amedas_h/map"
for i in range(10, 66): # 10 to 66, memo to test.
	_url = url + str(i) + ".html"
	print(_url)

	html = None
	try:
		response = requests.get(_url) # ダウンロード
		response.encoding = "utf-8"  # 気象庁のHPは自動認識に失敗する
		html = response.text
		#print(html)
	except Exception as e:
		print(str(e))

	if html != None:
		#print(html)
		p = re.compile("<area shape='rect' alt='(?P<name>.+)' coords='.+' href='today-(?P<_id>\d+).html\?areaCode=(?P<area_code>\d+)&groupCode=(?P<group_code>\d+)'/>")
		match = p.findall(html)
		names = set()
		_local_list = {}
		for mem in match:
			print(mem)
			name = mem[0]
			names.add(name)
			_local_list[name] = mem

		for name in names:
			block_no = get_block_no(groups_info, names, name)
			#if block_no == "1302":
			#	print(block_no, names, name)
			#	time.sleep(5)
			today_list.add(_local_list[name] + (block_no,))
			if block_no not in block_no_set: # 処理のミスによる2重登録をチェック
				block_no_set.add(block_no)
			else:
				if "富士山" != name and "竜王山" != name:          # 富士山は公式に2重登録されているorz。竜王山は最新のデータ画面では香川と徳島に見えるが、過去のデータ画面には徳島にないパターン。
					print("--error double block_no--", block_no, names, name)
					exit()
	time.sleep(0.2)


# 保存する
with open("today_list.csv", "w", encoding="utf-8-sig") as fw:
	for mem in today_list:
		#name, _id, area_code, group_code, block_no = mem
		s = "\t".join(mem)
		fw.write(s)
		fw.write("\n")

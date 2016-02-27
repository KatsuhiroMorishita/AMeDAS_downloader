#!usr/bin/python3
# -*- coding: utf-8 -*-
#----------------------------------------
# name: download
# purpose: 気象庁のアメダスから過去の気象データをダウンロードする
# memo: 同じ観測所名に対応できていないことに気が付いた@2016-01-29。例：1462	高松, 47891	高松
# author: Katsuhiro MORISHITA, 森下功啓
# created: 2015-08-17
# lisence: MIT
#----------------------------------------
import os
import sys
import time
import urllib.request
from datetime import datetime as dt
from datetime import timedelta as td


start_date = dt(2015,8,1) # 書き込んでいる日付けはテキトー
end_date = dt(2015,8,24)


def create_dir(path_list):
    """ 指定されたパスのディレクトリを作成する
    Argv:
        path_list   <list<str>> 作成するディレクトリ
                        階層を要素とする。
    """
    #print(path_list)
    dir = ""
    for men in path_list:
        dir = os.path.join(dir, men)
        #print(dir)
        if not os.path.isdir(dir):
            os.mkdir(dir)
    return dir


class amedas_node:
	""" 個々のアメダス観測所に合わせた処理を実装したオブジェクト
	"""
	def __init__(self, prec_num, block_num, name, _id, area_code, group_code):
		self._block_num = block_num
		self._prec_num = prec_num
		self._name = name
		self._url_patr = None
		self._id = _id
		self._area_code = area_code
		self._group_code = group_code

		if int(self._block_num) < 10000:
			self._url_part = "a"
		else:
			self._url_part = "s"

	def get_data(self, _type="10min", date=None):
		""" 指定されたデータタイプの観測データをダウンロードする
		"""
		url = ""
		if _type == "10min" or _type == "hourly":
			url = "http://www.data.jma.go.jp/obd/stats/etrn/view/" + \
				_type + "_" + self._url_part + "1.php?" + \
				"prec_no=" + self._prec_num + \
				"&block_no=" + self._block_num + \
				"&year=" + str(date.year) + "&month=" + date.strftime("%m") + "&day=" + date.strftime("%d") + "&view="
		elif _type == "real-time":
			url = "http://www.jma.go.jp/jp/amedas_h/today-" + self._id + ".html"
		else:
			print("arg is unknown type.")
			return

		print("--target url--")
		print(url)
		html = None
		try:
			response = urllib.request.urlopen(url)
			html = response.read()
		except Exception as e:
			print("--download error--", str(e))
		return html

	def save(self, _type="10min", date=None):
		""" 指定されたデータタイプの観測データをダウンロードして、規定のディテクトリ構造で保存する
		"""
		html = self.get_data(_type, date)
		if html != None:
			_dir_path = ["Raw HTML", self._block_num + "_" + self.name, date.strftime("%Y")]
			_dir = create_dir(_dir_path)
			fname = self._block_num + "_" + self.name + date.strftime("_%Y_%m_%d") + ".html"
			path = os.path.join(_dir, fname)
			with open(path, "wb") as fw:
				fw.write(html)

	@property
	def name(self):
	    return self._name
	



def get_amedas_nodes():
	""" アメダス観測所の観測データへアクセスする辞書オブジェクトを返す
	"""
	# 過去の観測データの入手に必要なアメダスのノード情報をファイルから読み取る
	names1 = set() # 観測所名の一致チェック用
	amedas_info1 = {}
	fname = os.path.join(os.path.dirname(__file__), "AMEDAS list.csv") # 他のスクリプトから呼び出されても、これなら動作する
	with open(fname, "r", encoding="utf-8-sig") as fr:
		lines = fr.readlines()
		for line in lines:
			line = line.rstrip()
			field = line.split("\t")
			print(field)
			prec_num, block_num, name = field
			if "（" in name:
				name = name.split("（")[0]
			names1.add(name)
			amedas_info1[name] = [prec_num, block_num, name]

	# 最新の観測データの入手に必要なアメダスのノード情報をファイルから読み取る
	amedas_info2 = {}
	names2 = set()
	fname = os.path.join(os.path.dirname(__file__), "today_list.csv")
	with open(fname, "r", encoding="utf-8-sig") as fr:
		lines = fr.readlines()
		for line in lines:
			line = line.rstrip()
			field = line.split("\t")
			print(field)
			name, _id, area_code, group_code = field
			names2.add(name)
			amedas_info2[name] = [_id, area_code, group_code]
	#print(names1 - names2) # 引く方向は注意。片方にしか含まれていない領域なら、メソッドを使う。
	names = names1 | names2

	# アメダスノードオブジェクトを作成する
	print("--setting amedas node object--")
	amedas_nodes = {}
	for a_name in names:
		prec_num, block_num, name = None, None, None
		if a_name in amedas_info1:
			prec_num, block_num, name = amedas_info1[a_name]
		_id, area_code, group_code = None, None, None
		if a_name in amedas_info2:
			_id, area_code, group_code = amedas_info2[a_name]
		#print(a_name)
		amedas_nodes[a_name] = amedas_node(prec_num, block_num, name, _id, area_code, group_code)

	return amedas_nodes




def main():
	# 引数の処理
	argvs = sys.argv
	_type = ""
	if len(argvs) >= 2:
		_type = argvs[1]
	else:
		print("please set argv. e.g. hourly, 10min, real-time.")
		exit()

	amedas_nodes = get_amedas_nodes()

	# ダウンロードの対象となっている期間とアメダスの一覧をファイルから読み込む
	target = []
	with open("AMEDAS.ini", "r", encoding="utf-8-sig") as fr:
		lines = fr.readlines()
		start_date = dt.strptime(lines[0], "start=%Y,%m,%d\n")
		end_date = dt.strptime(lines[1], "stop=%Y,%m,%d\n")
		for i in range(3, len(lines)):
			line = lines[i]
			line = line.rstrip()
			line = line.lstrip()
			if len(line) == 0:
				continue
			if "#" in line:
				continue
			field = line.split("\t")
			print(field)
			block_num, name = field
			target.append(name)
			
	# もし、最新データが必要であれば設定ファイルの内容を無視して、現時点の時刻データに置き換える
	if _type == "real-time":
		start_date = dt.now()
		end_date = start_date

	# 観測データをダウンロードして保存する
	t = start_date
	while t <= end_date:
		for name in target:
			node = amedas_nodes[name]
			node.save(_type, t)
			time.sleep(0.5)
		t += td(days=1)


	"""
	hoge = amedas_node("86", "1240", "阿蘇乙姫")
	html = hoge.get_data("10min", dt(2015,8,16))
	print(html)
	"""


if __name__ == '__main__':
	main()
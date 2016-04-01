#!usr/bin/python3
# -*- coding: utf-8 -*-
#----------------------------------------
# name: get_block_members
# purpose: AMeDASの過去の観測データページから、観測所の情報、および観測ブロック名とそこに属する観測所名の一覧を取得する。
# author: Katsuhiro MORISHITA, 森下功啓
# created: 2016-03-02
# lisence: MIT
#----------------------------------------
import urllib.request
import re
import time

# AMeDASの過去の観測データページから、観測所の情報、および観測ブロック名とそこに属する観測所名の一覧を取得する
group_members = {}
member_data = {}
with open("prec_no.txt") as fr:
	lines = fr.readlines()
	for line in lines:
		prec_no = line.rstrip()
		_url = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no=" + prec_no
		print(_url)
		html = None
		try:
			response = urllib.request.urlopen(_url) # ダウンロード
			html = response.read()
			#print(html)
		except Exception as e:
			print(str(e))

		
		if html != None:
			html = html.decode("utf-8")             # 文字コードを指定して、文字列に変換
			# グループ名を取得
			p = re.compile('alt="(?P<group_name>.+)全地点')
			match = p.search(html)
			group_name = None
			if match != None:
				group_name = match.group("group_name")
				print(group_name)
			
			# 個々の観測所の情報を抽出
			names = set()
			p = re.compile("'.','\d+','.+','.+','[-]?\d\d','\d\d.\d','\d\d\d','\d\d.\d','[-]?\d+(?:[.]\d+)?'") # 秋田の大潟は標高が0以下なので、Ruby版だとヒットしていないんじゃないか？
			match = p.findall(html)
			if match != None:
				for mem in match:
					mem = mem.replace("'", "")
					kind, block_no, name_kanji, name_kana, lat_deg, lat_min, lon_deg, lon_min, height = mem.split(",")
					name_kanji = re.sub("[（].+[）]", "", name_kanji)
					degree_lon = str(float(lon_deg) + float(lon_min) / 60)
					degree_lat = str(float(lat_deg) + float(lat_min) / 60)
					names.add(block_no + "_" + name_kanji)
					member_data[int(block_no)] = (prec_no, kind, block_no, name_kanji, name_kana, str(group_name), degree_lat, degree_lon, height) # group_nameはNoneであることがある（南極とか南極とか南極とか）
					#print(mem)
				group_members[group_name] = tuple(names)
print(group_members)



# 保存する
with open("amedas_node_list.csv", "w", encoding="utf-8-sig") as fw:
	block_nos = sorted(member_data.keys())
	for block_no in block_nos:
		mem = member_data[block_no]
		#print(mem)
		mem = list(mem)
		#print(mem)
		s = "\t".join(mem)
		fw.write(s)
		fw.write("\n")

with open("amedas_group.csv", "w", encoding="utf-8-sig") as fw:
	for group_name in group_members:
		fw.write(str(group_name))
		fw.write("\t")
		print(group_name, group_members[group_name])
		mem = group_members[group_name]
		s = "\t".join(mem)
		fw.write(s)
		fw.write("\n")

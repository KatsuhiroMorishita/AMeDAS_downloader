#!usr/bin/python3
# -*- coding: utf-8 -*-
#----------------------------------------
# name: create_amedas_list
# purpose: AMeDASのダウンロードに必要なノード情報を作成する。
# author: Katsuhiro MORISHITA, 森下功啓
# created: 2016-03-03
# lisence: MIT
#----------------------------------------
import urllib.request
import re
import time


# 最新（準リアルタイム）のデータを公開している観測所の情報を取得する
today_node = {}
with open("today_list.csv", "r", encoding="utf-8-sig") as fr:
	lines = fr.readlines()
	for line in lines:
		line = line.rstrip()
		field = line.split("\t")
		name, _id, area_code, group_code, block_no = field #清水	50261	000	35	1243
		today_node[block_no] = (_id, area_code, group_code)


# 過去の観測データを公開している観測所の情報を取得する
past_node = {}
with open("amedas_node_list.csv", "r", encoding="utf-8-sig") as fr:
	lines = fr.readlines()
	for line in lines:
		line = line.rstrip()
		field = line.split("\t")
		prec_no, kind, block_no, name_kanji, name_kana, degree_lat, degree_lon, height = field #85	a	1616	北山	ホクザン	33.413333333333334	130.22	339
		past_node[block_no] = (prec_no, block_no, name_kanji)



# 保存する
with open("AMeDAS_list.csv", "w", encoding="utf-8-sig") as fw:
	block_nos = sorted(past_node.keys())
	for block_no in block_nos:
		out = past_node[block_no]
		if block_no in today_node:
			out += today_node[block_no]
		else:
			out += ("None", "None", "None")
		s = "\t".join(out)
		fw.write(s)
		fw.write("\n")


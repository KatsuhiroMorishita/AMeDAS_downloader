#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        pyConvertor
# Purpose:  AMeDASのhtmlファイルを処理して、CSVファイルに変換・保存する
#
# Author:      morishita
#
# Created:     10/12/2013
# Copyright:   (c) morishita 2013
# Licence:     MIT
# History:     2014-01-19   観測値が確定していない場合に「)」が付くが、これに対応した。
#              2014-03-20   10分データのhtmlファイルフォーマットに対応していないバグを修正した。 
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import os
import sys
import re
import datetime

def get_Date(txt):
    """ 日付の文字列から時刻オブジェクトを作成する
    """
    #print(txt)
    p = re.compile(r'(?P<date>(?P<year>\d{4})(?:,|/|-)(?P<month>\d{1,2})(?:,|/|-)(?P<day>\d{1,2}))')    # 日付にマッチするパターン
    matchTest = p.search(txt)
    if matchTest != None:
        #print(matchTest.groups())
        year   = int(matchTest.group('year'))
        month  = int(matchTest.group('month'))
        day    = int(matchTest.group('day'))
        return datetime.datetime(year, month, day, 0, 0, 0, 0)
    else:
        return None
    return

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


def get_column_names(html_path):
    """ 観測項目名の一覧をリストで返す
    memo:
        現時点（2013/12/12）では、日ごとのデータの解析に対応していない。
        項目名を得るには、まず3行分取って、2行目に注目しつつ3行目を処理して、2行目を置換。
        それが終わったら、1行目に注目しつつ2行目を処理して、1行目を置換・・・でOK
    """
    column_names = []
    row = None
    with open(html_path, "r", encoding="utf-8-sig", errors="ignore") as fr:
        lines = fr.readlines()
        # まずは項目名の候補捜し
        n = None
        for i in range(60, 130):                     # 行番号は幅を持たせて走査する
            line = lines[i]
            if "時" in line and "rowspan" in line:   # 項目名には必ず含まれるはず
                n = i
                break
        # 次に項目名であるかどうかを確認し、取得する
        if n != None:
            #print("dummy")
            line = lines[n]
            p = re.compile(
                    '[<]th' \
                    '(?: (?P<kind>rowspan|colspan)="(?P<span>\d)")?' \
                    '(?: scope="\w+")?' \
                    '[>]' \
                    '(?P<name>(?:\w|[(]|[)]|[/]|℃|[<]br[>]|・|㎡|％)+)[<]/th[>]'
                    )                               # 項目名にヒットするパターン
            matchTest1 = p.findall(line)
            if matchTest1 != None:
                #print("match 01")
                # 項目名パターンにマッチしていた場合、次の行の検査も行う
                line = lines[n + 1]
                matchTest2 = p.findall(line)       # 次の行のマッチ結果を得る
                #print(matchTest2)
                if matchTest2 != None:              # ヒットしていればタプル
                    #print("match 02")
                    # 項目名をまとめる
                    names = []
                    i = 0
                    for kind, span, name in matchTest1: # マッチした結果（タプルのリスト）を分解しつつ確認
                        if "<br>" in name:
                            name = name.replace("<br>", "")     # 余計な文字列の削除
                        if kind == "colspan":                   #　2行目にさらに細分項目があるとifの中を実行
                            for m in range(0, int(span)):       # 細分項目の数だけループ
                                _name = name + matchTest2[i][2] # 項目名を作る
                                names.append(_name)
                                i += 1                          # 利用した項目名を2度と使わないようにインクリメント
                        else:
                            names.append(name)
                    column_names = names
                    row = n + 1
    #print((column_names, row))
    return (column_names, row)

def get_data(html_path):
    """ 指定されたHTMLファイルから観測データを抽出してリストとして返す
    """
    ans = []
    names, row = get_column_names(html_path)    # 項目名と、項目名が含まれる最後の行番号を取得
    #print(names)
    if row != None:                             # 項目が取得できているかを確認
        ans.append(names)
        with open(html_path, "r", encoding="utf-8-sig", errors="ignore") as fr:
            lines = fr.readlines()
            # 観測値にヒットするパターン
            p = re.compile("\"[>]" +
                "(?P<value>(?:" +
                    "(?:\d+[:]?(?:\d{2})?)" + "|" +
                    "(?:[-]?\d+[.]?\d+(?:[ ][)])?)" + "|" +
                    "(?:\w+(?:[ ][)])?)" + "|" +
                    "(?:[-]+)" + "|" +
                    "(?:[)])" + "|" +
                    "(?:×)" + "|" +
                    "(?:[/])" + "|" +
                    "(?:\d+[<]span style=\"vertical[-]align:super; font-size:80%\"[>][-][<][/]span[>])" + "|" +
                    '(?:[<]img src=".{10,30}[/]F8(?:\w|\d){2}[.]gif"[>])' + "|" +
                    "(?:[+])" + "|" +
                    "(?:\d+&nbsp;(?:[-]|[+])?)" + "|" +
                    "(?:#)" + "|" +
                    "(?:[*])" + "|" +
                    "(?:.{20,60}FB\w\w\.gif)" + "|" +
                    "(?:[]])"
                ")?)" +
                "[<][/]td")
            for i in range(row + 1, len(lines)):    #　項目名直後から観測値であることを前提として、走査
                line = lines[i]
                if "tr class=" not in line:
                    break
                matchTest = p.findall(line)         # 観測値を一気に取得
                #print(matchTest)
                # 値の検査（余計な文字を削除）
                _temp = []
                p2 = re.compile('(?P<kind>F8(?:\w|\d){2})[.]gif')   # 天気記号にヒットするパターン
                for men in matchTest:
                    if "&nbsp;" in men:
                        men = men.replace("&nbsp;", "") # 空白を表現するタグを削除
                    matchTest2 = p2.findall(men)    # 一気にリストになるのでfindallを使っている
                    #print(matchTest2)
                    if len(matchTest2) == 1:        # ヒットしなければ0
                        men = matchTest2[0]
                        #print(men)
                    _temp.append(men)               # 要素を格納
                #print(_temp)
                ans.append(_temp)                   # 答えのオブジェクト（リストのリストになっている）に格納
    return ans

def main():
    if os.path.exists("./AMEDAS.ini"):
        lines = []
        with open("AMEDAS.ini", "r", encoding="utf-8-sig", errors="ignore") as fr:
            lines = fr.readlines()
        if len(lines) < 4:
            print("amount of parameters is too low.")
            sys.exit(1)
        start = lines[0]
        stop  = lines[1]
        re_start = "start=(?P<date>\d{4}(,|-|/)\d{1,2}(,|-|/)\d{1,2})"  # 開始日のフォーマット
        re_stop = "stop=(?P<date>\d{4}(,|-|/)\d{1,2}(,|-|/)\d{1,2})"    # 終了日のフォーマット
        if not (re.match(re_start, start) and re.match(re_stop, stop)): # フォーマットチェック
            print("parameter is anomaly.")
            sys.exit(1)
        start = get_Date(start)                                         # 時刻オブジェクトに変換
        stop = get_Date(stop)
        if start > stop:                                                # 日付の設定ミスを確認
            print("date setting is anomaly.")
            sys.exit(1)
        re_station = re.compile("(?P<block_no>\d{4,5})(?:,|\t)(?P<station_name>\w+)")   # 設定にヒットするパターン
        for i in range(3, len(lines)):
            line = lines[i]
            # まずはコメントを除外
            field = line.split("#")
            if len(field) >= 2:                                         # #マーク以降はコメントとみなす
                line = field[0]
            # 観測局マッチ検査
            matchTest = re_station.search(line)                         # パターンマッチ
            if matchTest != None:
                block_no     = matchTest.group('block_no')
                station_name = matchTest.group('station_name')
                _date = start
                while _date <= stop:                                    # 設定日時でループ
                    fname = block_no + "_" + station_name + "_" + _date.strftime('%Y_%m_%d')    # 読み出すべきファイル名を生成
                    #print(fname)
                    f_html = fname + ".html"
                    target_path = os.path.join("Raw HTML", block_no + "_" + station_name, _date.strftime('%Y'), f_html)
                    print("target file path: " + target_path)
                    if os.path.exists(target_path):
                        f_csv = fname + ".csv"
                        f_path = ["Processed HTML", block_no + "_" + station_name, _date.strftime('%Y')]    # 生成するファイルを格納するフォルダのパスをリストに生成
                        dir = create_dir(f_path)                        #　フォルダが無ければ作る
                        c_path = os.path.join(dir, f_csv)               # パスをつないで、ファイルの相対パスを生成
                        #print(c_path)
                        # 変換と保存
                        with open(c_path, "w", encoding="utf-8-sig") as fw:
                            data = get_data(target_path)                # ************
                            #print(data)
                            for men in data:
                                fw.write(",".join(men) + "\n")
                    else:
                        print("target file is not exist.")
                    _date += datetime.timedelta(days=1)

    else:
        print("AMEDAS.ini isn't exist.")
        sys.exit(1)


if __name__ == '__main__':
    main()

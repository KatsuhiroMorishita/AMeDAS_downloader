#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name: html_parser
# purpose:  AMeDASのhtmlファイルを処理して、CSVファイルに変換・保存する
# author: morishita
# created: 10/12/2013
# copyright: (c) morishita 2013
# licence: MIT
# history: 2014-01-19   観測値が確定していない場合に「)」が付くが、これに対応した。
#          2014-03-20   10分データのhtmlファイルフォーマットに対応していないバグを修正した。 
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os
import sys
import re
from datetime import datetime as dt
from datetime import timedelta as td



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



def get_column_names(lines):
    """ 1日毎に更新されるアメダスの過去データが入っているhtmlファイルから観測項目名の一覧をリストで返す
    memo:
    現時点（2013/12/12）では、日ごとのデータの解析に対応していない。
        項目名を得るには、まず3行分取って、2行目に注目しつつ3行目を処理して、2行目を置換。
        それが終わったら、1行目に注目しつつ2行目を処理して、1行目を置換・・・でOK
    """
    column_names = []
    row = None
    # まずは項目名の候補捜し
    n = None
    #print(lines)
    if len(lines) < 130:                       # 存在しない過去情報の場合、130行もない
        return None
    for i in range(60, 130):                   # 行番号は幅を持たせて走査する
        line = lines[i]
        if "時" in line and "rowspan" in line: # 項目名には必ず含まれるはず
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
                '(?P<name>(?:\w|[(]|[)]|[/]|℃|(?:[<]br[>]|[<]br /[>])|・|㎡|％)+)[<]/th[>]'
                )                               # 項目名にヒットするパターン
        matchTest1 = p.findall(line)
        #print(matchTest1)
        if matchTest1 != None:
            #print("match 01")
            # 項目名パターンにマッチしていた場合、次の行の検査も行う
            line = lines[n + 1]
            matchTest2 = p.findall(line)         # 次の行のマッチ結果を得る
            #print(matchTest2)
            if matchTest2 != None:               # ヒットしていればタプル
                #print("match 02")
                # 項目名をまとめる
                names = []
                i = 0
                for kind, span, name in matchTest1: # マッチした結果（タプルのリスト）を分解しつつ確認
                    if "<br>" in name:
                        name = name.replace("<br>", "")   # 余計な文字列の削除
                    if "<br />" in name:
                        name = name.replace("<br />", "") # 余計な文字列の削除
                    if kind == "colspan":                 # 2行目にさらに細分項目があるとifの中を実行
                        for m in range(0, int(span)):     # 細分項目の数だけループ
                            _name = name + matchTest2[i][2] # 項目名を作る
                            names.append(_name)
                            i += 1                        # 利用した項目名を2度と使わないようにインクリメント
                    else:
                        names.append(name)
                column_names = names
                row = n + 1
    #print((column_names, row))
    #exit()
    return (column_names, row)


def get_data_from_past_format(lines):
    """ 1日毎に更新されるアメダスの過去データが入っているhtmlファイルから観測データを抽出してリストとして返す
    """
    ans = []
    indexes = get_column_names(lines)      # 項目名と、項目名が含まれる最後の行番号を取得
    if indexes == None:
        return []
    names, row = indexes
    #print(names)
    if row != None:                        # 項目が取得できているかを確認
        ans.append(names)
        # 観測値にヒットするパターン
        p = re.compile("\"[>]" +
            "(?P<value>(?:" +
                "(?:\d+[:]?(?:\d{2})?)" + "|" +
                "(?:[-]?\d+[.]?\d+(?:[ ][)])?)" + "|" +
                "(?:\w+(?:[ ][)])?)" + "|" +
                "(?:[-]+)" + "|" +
                "(?:[)])" + "|" +
                "(?:×)" + "|" +
                "(?:[/]+)" + "|" +
                "(?:\d+[<]span style=\"vertical[-]align:super; font-size:80%\"[>][-][<][/]span[>])" + "|" +
                '(?:[<]img src=".{10,30}[/]F8(?:\w|\d){2}[.]gif"[>])' + "|" +
                "(?:[+])" + "|" +
                "(?:\d+&nbsp;(?:[-]|[+])?)" + "|" +
                "(?:\d+(?:[-]|[+])?)" + "|" +
                "(?:#)" + "|" +
                "(?:[*])" + "|" +
                "(?:.{20,60}FB\w\w\.gif)" + "|" +
                "(?:[]])"
            ")?)" +
            "[<][/]td")
        for i in range(row + 1, len(lines)):     # 項目名直後から観測値であることを前提として、走査
            line = lines[i]
            if "tr class=" not in line:
                break
            matchTest = p.findall(line)          # 観測値を一気に取得
            #print(matchTest)
            # 値の検査（余計な文字を削除）
            _temp = []
            p2 = re.compile('(?P<kind>F8(?:\w|\d){2})[.]gif')   # 天気記号にヒットするパターン
            for men in matchTest:
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


def get_data_from_lasted_format(lines):
    """ 1時間毎に公開情報が更新されるアメダスの観測データが入ったhtmlファイルから、観測情報を読み出す
    """
    table_found = False
    data = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if '<table id="tbl_list" cellpadding="0" cellspacing="0" border="0">' in line: # 表の始まりの箇所を探す
            table_found = True
        if table_found == True:
            if "<tr>" in line:           # <tr>毎に新しいレコードが入っている
                row = ""
                while i < len(lines):    # </tr>が発見されるまで文字列を結合する
                    line = lines[i]
                    line = line.rstrip()
                    line = line.replace(" ", "")
                    line = line.replace("\t", "")
                    row += line
                    if "</tr>" in line:  # 文字列のパターンを探して、項目名と観測値を探す
                        p = re.compile(">(?P<label>(?:[\w℃/\d.\-%]+)|&nbsp;)</td>")
                        match = p.findall(row)
                        match = [x.replace("&nbsp;", "") for x in match] # 空白コードを置換
                        data.append(match)
                        break
                    i += 1
        if table_found == True and "</table>" in line: # 観測データ以降はもう見なくてもOK
            break
        i += 1
    return data



def get_clock(txt):
    """ 時刻を時と分に分けて返す
    """
    #print(txt)
    p = re.compile("(?P<hour>\d{1,2})(?:[:](?P<min>\d\d))?")   # 分は10分毎の観測データ以外では省略されている
    matchTest = p.match(txt)
    #print(matchTest)
    hour = None
    minute = None
    if matchTest != None:
        #print(matchTest.groups())
        hour = matchTest.group('hour')
        if hour != None:
            hour = int(hour)
        minute = matchTest.group('min')
        if minute != None:
            minute = int(minute)
        #print(hour, minute)
    return (hour, minute)


def get_data(lines, date=None):
    """ 観測データの種類に合わせて処理した結果を返す
    """
    txt = "\n".join(lines)
    data = None
    if "１時間ごとの値" in txt or "１０分ごとの値" in txt: # 観測データの種類を判別して呼び出す関数を変えている
        data = get_data_from_past_format(lines)
    elif "今日の観測データ" in txt:
        data = get_data_from_lasted_format(lines)

    # 時刻の処理
    if date != None:
        temp_data = []
        for x in data:
            t = x[0]
            if "時" in t:
                x.insert(0, "日時")
                continue
            hour, minute = get_clock(t)
            if minute == None:
                minute = 0
            _date = dt(year=date.year, month=date.month, day=date.day) + td(hours=hour, minutes=minute)
            x.insert(0, str(_date))
            temp_data.append(x)
        date = temp_data
    elif data != None:
        for i in range(len(data)):
            data[i].insert(0, "")
    return data



def main():
    # 処理の対象となっている期間とアメダスの一覧をファイルから読み込む
    start_date = None
    end_date = None
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
            block_no, name = field
            while True:                   # Excelで編集した際に文字列先頭の0を無くしちゃうことがあるが、面倒なのでコードで対応
                if len(block_no) >= 4:
                    break
                block_no = "0" + block_no
            target.append((block_no, name))


    for block_no, name in target:
        _date = start_date
        while _date <= end_date:                                # 設定日時でループ
            fname = block_no + "_" + name + "_" + _date.strftime('%Y_%m_%d')    # 読み出すべきファイル名を生成
            #print(fname)
            f_html = fname + ".html"
            target_path = os.path.join("Raw HTML", block_no + "_" + name, _date.strftime('%Y'), f_html)
            print("target file path: " + target_path)
            if os.path.exists(target_path):
                f_csv = fname + ".csv"
                f_path = ["Processed HTML", block_no + "_" + name, _date.strftime('%Y')]   # 生成するファイルを格納するフォルダのパスをリストに生成
                dir = create_dir(f_path)                        #　フォルダが無ければ作る
                c_path = os.path.join(dir, f_csv)               # パスをつないで、ファイルの相対パスを生成
                #print(c_path)
                lines = []
                with open(target_path, "r", encoding="utf-8-sig", errors="ignore") as fr: # 観測データの入ったhtmlファイルを読み込む
                    lines = fr.readlines()
                data = get_data(lines, _date)
                if data != None:
                    with open(c_path, "w", encoding="utf-8-sig") as fw:
                        for men in data:
                            fw.write(",".join(men) + "\n")
            else:
                print("target file is not exist.")
            _date += td(days=1)


if __name__ == '__main__':
    main()

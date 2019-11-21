#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name: html_parser
# purpose:  AMeDASのhtmlファイルを処理して、CSVファイルに変換・保存する
# author: morishita
# created: 10/12/2013
# history: 2014-01-19   観測値が確定していない場合に「)」が付くが、これに対応した。
#          2014-03-20   10分データのhtmlファイルフォーマットに対応していないバグを修正した。 
# copyright: (c) morishita 2013
# Licence: MIT. If you use this program for your study, you should write Acknowledgement in your paper.
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os
import sys
import re
from datetime import datetime as dt
from datetime import timedelta as td
import pandas as pd


table_index = {"daily":0, "hourly":0, "10min":0,  "real-time":4} # pandasで解析したときにどの表が観測データかを識別するための番号
time_index = {"daily":"日", "hourly":"時", "10min":"時分",  "real-time":"時"}  # データ毎の時間表現


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



def get_shape(match_list):
    """ 引数から判断できる表の形状を取得します。
    """
    col_size = 0
    row_size = 0
    for mem in match_list:
        col_span = 1
        row_span = 1
        if "colspan" in mem:
            index = mem.index("colspan")
            col_span = int(mem[index + 1])
        col_size += col_span
        _row_span = 1
        if "rowspan" in mem:
            index = mem.index("rowspan")
            _row_span = int(mem[index + 1])
        if row_size < _row_span:
            row_size = _row_span
    return row_size, col_size


def mearge_table(match_list, table, row):
    """ tableに項目名を格納して返す
    """
    i = 0
    for mem in match_list:
        col_span = 1
        if "colspan" in mem:
            index = mem.index("colspan")
            col_span = int(mem[index + 1])
        row_span = 1
        if "rowspan" in mem:
            index = mem.index("rowspan")
            row_span = int(mem[index + 1])
        while True:
            if table[row][i] is not None:
                i += 1
            else:
                break
        for _ in range(col_span):
            for j in range(row_span):
                if j == 0:
                    name = mem[4] 
                else:
                    name = ""
                table[row+j][i] = name# set name
                #print(row_span, col_span, mem[4])
            i += 1
    return table


def get_column_names(lines):
    """ 1日毎に更新されるアメダスの過去データが入っているhtmlファイルから観測項目名の一覧をリストで返す
    memo:
    現時点（2017/02/11）では、リアルタイムのデータには対応していない。
    """
    column_names = []
    row = None
    
    # まずは項目名の候補捜し
    n = None
    #print(lines)
    if len(lines) < 120:                       # 存在しない過去情報の場合、行数が少ない（2019年9月現在、阿蘇乙姫で74行）
        print("len(lines) is less. It may be blank data.")
        return None
    for i in range(60, 130):                   # 項目名の行番号を探す。行番号は幅を持たせて走査する
        line = lines[i]
        if ("時" in line and "rowspan" in line) or ("日" in line and "rowspan" in line) : # 項目名には必ず含まれるはず
            n = i
            break
            
    # 次に項目名を取得する
    if n is not None:
        #print("dummy")
        line = lines[n]
        p = re.compile(
                '[<]th' \
                '(?: (?P<kind1>rowspan|colspan)="(?P<span1>\d)")?' \
                '(?: (?P<kind2>rowspan|colspan)="(?P<span2>\d)")?' \
                '(?: scope="\w+")?' \
                '[>]' \
                '(?P<name>(?:\w|[(]|[)]|[/]|℃|\-|[:]|(?:[<]br[>]|[<]br /[>])|・|㎡|％)+)[<]/th[>]'
                )                               # 項目名にヒットするパターン'
        match = p.findall(line)
        #print("--match--", match)
        row_size, col_size = get_shape(match)
        #print(row_size, col_size)
        table = [[None] * col_size for _ in range(row_size)] # 項目名を格納する2次元配列を用意
        table = mearge_table(match, table, 0)
        #print("table", table)
        
        table_row = 1
        while len(match) != 0:
            n += 1
            line = lines[n]
            match = p.findall(line)         # 次の行のマッチ結果を得る
            #print("--match--", match)
            if len(match) != 0:
                table = mearge_table(match, table, table_row)
                #print("table", table)
            table_row += 1

        # 項目名を作る
        index_list = [""] * len(table[0]) # まずは列の数だけ空の文字列を作る
        for i in range(len(table[0])):
            name = ""
            for j in range(len(table)): # tableを縦に走査して、文字列を結合
                name += table[j][i]
            name = name.replace("<br>", "") 
            name = name.replace("<br />", "") # 余計な文字列の削除
            index_list[i] = name
        #print("--column names--", index_list)
        column_names = index_list
        row = n                                      # nは項目名の下の行を指しているはず
    return (column_names, row)



def get_data_from_past_format(lines):
    """ 1日毎に更新されるアメダスの過去データが入っているhtmlファイルから観測データを抽出してリストとして返す
    記号に関しては、「www.data.jma.go.jp/obd/stats/data/mdrr/man/remark.html」を参照のこと。
    """
    print("--get_data_from_past_format--")
    ans = []
    indexes = get_column_names(lines)      # 項目名と、項目名が含まれる最後の行番号を取得
    if indexes is None:
        return []
    names, row = indexes
    #print(names)
    if row is not None:                        # 項目が取得できているかを確認
        ans.append(names)
        # 観測値にヒットするパターン
        p = re.compile("\"[>]" +
            "(?P<value>(?:" +
                "(?:\d+[:]?(?:\d{2})?)" + "|" +
                "(?:[\-]?\d+[.]?\d+\s?[ )\]]?)" + "|" +
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
                "(?:[\]])" +
            ")?)" +
            "[<][/]td")
        for i in range(row, len(lines)):        # 項目名直後から観測値であることを前提として、走査
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
                        p = re.compile(">(?P<label>(?:[\w℃/\d.\-%\]×)]+)|&nbsp;)</td>")
                        match = p.findall(row)
                        match = [x.replace("&nbsp;", "") for x in match] # 空白コードを置換
                        data.append(match)
                        break
                    i += 1
        if table_found == True and "</table>" in line: # 観測データ以降はもう見なくてもOK
            break
        i += 1
    return data




def get_data_with_pandas(lines):
    """ 月毎にまとめられた、日毎のデータを返す
    日毎のデータはデータ構造がまた異なるので新設した。
    表の数値などは1時間毎でも得られるので、整理した方がいいだろう。
    """
    print("--get_data_with_pandas--")
    indexes = get_column_names(lines)      # 項目名と、項目名が含まれる最後の行番号を取得
    #print(indexes)
    if indexes is None:
        return []
    names, row = indexes
    txt = "\n".join(lines)
    fetched_dataframes = pd.io.html.read_html(txt)
    df = fetched_dataframes[table_index["daily"]]
    #print(df)
    while True:   # pandsが取得した表に入っている項目名を削除する
        if isinstance(df.loc[0][0], str) and not (df.loc[0][0]).isdigit():
            #print(df.loc[0])
            df = df.drop(0)
            df.reset_index(drop=True, inplace=True)
        else:
            break
        #print("--while loop--")
        #print(df)
        #print(len(df))

    # 項目名をセット
    df.loc[-1] = names        # とりあえずは最後に追加
    df.index = df.index + 1   # shifting index
    df = df.sort_index()       # sorting by index
    return df.values.tolist() # pandasによるindexは含まれない




def get_clock(txt):
    """ 時刻を時と分に分けて返す
    """
    #print(txt)
    p = re.compile("(?P<hour>\d{1,2})(?:[:](?P<min>\d\d))?")   # 分は10分毎の観測データ以外では省略されている
    matchTest = p.match(txt)
    #print(matchTest)
    hour = None
    minute = None
    if matchTest is not None:
        #print(matchTest.groups())
        hour = matchTest.group('hour')
        if hour is not None:
            hour = int(hour)
        minute = matchTest.group('min')
        if minute is not None:
            minute = int(minute)
        #print(hour, minute)
    return (hour, minute)




def get_data(lines, date=None):
    """ 観測データの種類に合わせて処理した結果を返す
    """
    #print("--get_data--")
    txt = "\n".join(lines)
    data = None
    if "１時間ごとの値" in txt or "１０分ごとの値" in txt: # 観測データの種類を判別して呼び出す関数を変えている
        data = get_data_from_past_format(lines)
    elif "今日の観測データ" in txt:
        data = get_data_from_lasted_format(lines)
    elif "日ごとの値" in txt and not "１０分ごとの値" in txt: # 毎月の日毎のデータの場合
        data = get_data_with_pandas(lines)
        #print("--get_data--", data)

    # 時刻の処理
    if not date is None:
        temp_data = []
        for x in data:
            #print("--x--", x)
            t = str(x[0])    # Python3.7.4の？pandasでは整数化されるので、文字列に変換する
            if "時" in t: # 日時を1列目に加えるために、項目名を増やす
                x.insert(0, "日時")
                continue
            elif "日" in t:
                x.insert(0, "日付")
                continue

            if "日ごとの値" in txt and not "１０分ごとの値" in txt: # 毎月の日毎のデータの場合
                _date = dt(year=date.year, month=date.month, day=int(t))
            else:
                hour, minute = get_clock(t)
                #print("--time--", hour, minute)
                if minute is None:
                    minute = 0
                _date = dt(year=date.year, month=date.month, day=date.day) + td(hours=hour, minutes=minute)
            x.insert(0, str(_date))
            temp_data.append(x)
        date = temp_data
    elif not data is None:
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
            field = re.split("\t|,|\s+", line)
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
                #print("--data--", data)
                if data is not None:
                    with open(c_path, "w", encoding="utf-8-sig") as fw:
                        for mem in data:
                            mem = [str(x) for x in mem]
                            fw.write(",".join(mem) + "\n")
            else:
                print("target file is not exist.")
            _date += td(days=1)


if __name__ == '__main__':
    main()

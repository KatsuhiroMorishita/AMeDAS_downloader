#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        file_fusion
# Purpose:      このスクリプトファイルと同じ階層にあるフォルダを走査し、観測データを結合する
#               処理済みファイル数年分のデータ結合に利用可能です。
#               昨年組んだRubyスクリプトよりも利便性が上がったはず。
# Author:      K. Morishita
#
# Created:     22/08/2012
# History:      2013/12/14 現在のCSV保存フォーマットに対応した。
#                           スクリプトの実行フォルダを"Processed HTML"の上にした。
#               2014/1/19   保存ファイルに日付を入れるように変更
#                           1時間毎の観測データに対応
#               2015-08-22 時刻の処理を削除（html_parserに移行）
# Copyright:   (c) morishita 2012
# Licence:     MIT. If you use this program for your study, you should write Acknowledgement in your paper.
#-------------------------------------------------------------------------------
import os
import re
import glob


def process(dirPath):
    """ 指定されたフォルダの直下にあるフォルダ内を走査し、全てのcsvを結合したテキストデータを保存する
    """
    saveFileName = "fusion.csv"
    savePath = dirPath + "/" + saveFileName
    fw = open(savePath, 'w', encoding='utf-8-sig')
    index_write_flag = False
    plist =  os.listdir(dirPath)                # 指定されたフォルダ内を走査する
    plist = sorted(plist)
    #print (plist)
    for men in plist:
        fpath = os.path.join(dirPath, men)
        if os.path.isdir(fpath):                # 直下のフォルダを対象として処理
            fileList =  glob.glob(dirPath + "/" + men + '/*.csv')   # CSVファイルのリストを作成
            fileList = sorted(fileList)
            for fname in fileList:
                bname = os.path.basename(fname)
                if(bname != saveFileName):
                    with open(fname, 'r', encoding='utf-8-sig') as fr:
                        lines = fr.readlines()
                        for line in lines:
                            if "時" in line:    # 項目は1回だけ書き込んで、後は読み飛ばす
                                if index_write_flag == True:
                                    continue
                                else:
                                    index_write_flag = True
                            if line != "":
                                fw.write(line)
    fw.close()
    return

def main():
    """
    "Processed HTML"内のフォルダを走査し、そのフォルダ内にある全てのcsvファイルを各々結合する
    """
    target_dir = "Processed HTML"
    if os.path.isdir(target_dir):                   # target_dirの存在を確認
        print("'{0}' is founded.".format(target_dir))
        target_dir_path = os.path.join(os.getcwd(), target_dir)
        plist =  os.listdir(target_dir_path)        # target_dir内のファイルとフォルダを走査
        print("target list: ")
        print(plist)
        print("\n")
        for men in plist:
            _each_target_path = os.path.join(target_dir_path, men)
            if os.path.isdir(_each_target_path):    # フォルダ判定
                print("now target: " + men)
                process(_each_target_path)
                print(men + " is fin.")
    else:
        print("there isn't '{0}' dir.".format(target_dir))

if __name__ == '__main__':
    main()

#-------------------------------------------------------------------------------
# Name:        fusion.py
# Purpose:      このスクリプトファイルと同じ階層にあるフォルダを走査し、観測データを結合する
#               処理済みファイル数年分のデータ結合に利用可能です。
#               昨年組んだRubyスクリプトよりも利便性が上がったはず。
# Author:      K. Morishita
#
# Created:     22/08/2012
# histroy:     21/11/2012 更新した。ファイルの比較処理にあったバグを修正.
# Copyright:   (c) morishita 2012
# Licence:     new BSD
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os
import glob

def main():
    saveFileName = "fusion.csv"
    fw = open(saveFileName, 'w')                              #
    plist =  os.listdir(os.getcwd())
    #print (plist)
    for men in plist:
        if os.path.isdir(men):
            fileList =  glob.glob(os.getcwd() + '/' + men + '/*.csv')
            for fname in fileList:
                bname = os.path.basename(fname)
                if(bname != saveFileName):
                    fr = open(fname,'r')                                        #
                    _txt = fr.readlines()                                       #
                    for line in _txt:
                        fw.write(line)
    fw.close()

if __name__ == '__main__':
    main()

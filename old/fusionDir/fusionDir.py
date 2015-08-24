#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        fusionDir.py
# Purpose:      指定したフォルダの中身をコピーします。
#               同じファイルがあれば、上書きします。
#               再帰的に処理するのでネスト構造になった全てのファイルがコピー可能です。
# Author:      K. Morishita
#
# Created:     21/11/2012
# Copyright:   (c) morishita 2012
# Licence:     new BSD
#-------------------------------------------------------------------------------
#!/usr/bin/env python
import os
import shutil


def copy(copySourceDir, copyToDir):
    """ 指定されたフォルダの下層にあるフォルダとファイルをコピーする。フォルダがなければ作る。
    """
    dirlist1 =  os.listdir(copyToDir)           # ファイルとフォルダの一覧を取得
    dirlist2 =  os.listdir(copySourceDir)
    # 下層フォルダの一覧を辞書で作る
    dirPathDict1 = {}
    for men in dirlist1:
        path = copyToDir + "/" + men
        if os.path.isdir(path):
            dirPathDict1[men] = path
    dirPathDict2 = {}
    filePathDict2 = {}
    for men in dirlist2:
        path = copySourceDir + "/" + men
        if os.path.isdir(path):
            dirPathDict2[men] = path            # フォルダならこちら
        else:
            filePathDict2[men] = path           # ファイルならこちら
    # 移し元のフォルダを基に、コピーを実行
    copyDirListKeys = dirPathDict2.keys()
    for men in copyDirListKeys:
        dirName = copyToDir + "/" + men
        if os.path.isdir(dirName) == False:     # フォルダが既にあるかどうかをチェック
            shutil.copytree(dirPathDict2[men], dirName)     # フォルダがなければ、丸ごとコピー（再帰的に処理してくれる）
        else:
            copy(dirPathDict2[men], dirName)    # 再帰を使って、中身のフォルダ・ファイルのコピーを試みる
    # 移し元のファイルをコピー
    copyFileListKeys = filePathDict2.keys()
    for men in copyFileListKeys:
        pathSource = copySourceDir + "/" + men
        pathTo = copyToDir + "/" + men
        shutil.copy2(pathSource, pathTo)
    return

def main():
    """
    同じ階層にあるフォルダを走査し、そのフォルダ内にある全てのcsvファイルを結合する
    """
    if os.path.isdir("dir 1") or os.path.isdir("dir 2"):    # フォルダの存在を確認
        quit
    cdir = os.getcwd()
    uDir1 = cdir + "/copy To"                               # 移し先
    uDir2 = cdir + "/copy source"                           # 移し元
    copy(uDir2, uDir1)

if __name__ == '__main__':
    main()

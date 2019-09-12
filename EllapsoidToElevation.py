# -*- coding: utf-8 -*-　　
# EllapsoidToElevation
# 
# Read CSV that contains latitude, longitude, ellapsoid-height,
# then output to another CSV replacing ellapsoid-height with elevation.
# 
# This program uses data and argorythm which is distrubuted from Geospation Information Authority of Japan and ported to Python
# https://www.gsi.go.jp/buturisokuchi/grageo_geoidseika.html
#  
# Copyright (c) 2019 Naoki Ueda
#
#This software is released under the MIT License.
#http://opensource.org/licenses/mit-license.php
#
# 

import sys
import csv
import os
import math
import importlib

GSI_GEOID_FILE_NAME = 'gsigeo2011_ver2_1.asc'

#ジオイドデータはglobalで使う
global geoid
global geoidparam
global glamn
global glomn
global dgla
global dglo
global nla
global nlo

#ジオイドデータを読込みます。事前作成したデータファイルモジュール（geoidData.py）が存在しない時は
#国土地理院のジオイドデータファイルから作成します。（次回以降の処理が若干早くなる）
def getGeoidData():
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    if (os.path.exists(os.path.join(os.getcwd(),'geoidData.py')) == False):
        print('国土地理院のジオイドファイルからデータファイルを作成します(初回のみ)')
        if (os.path.exists(os.path.join(os.getcwd(),GSI_GEOID_FILE_NAME)) == False):
            print('エラー:データファイルがありません')
            print('同じフォルダに国土地理院のジオイドファイル「' + GSI_GEOID_FILE_NAME + '」を置いてください')
            return False
        createGeoidData()
    else:
        print('データファイルを読込中')
        module = importlib.import_module('geoidData')
        geoid = module.setGeoid()
        misc = module.setMiscData()
        glamn = misc["glamn"]
        glomn = misc["glomn"]
        dgla = misc["dgla"]
        dglo = misc["dglo"]
        nla = misc["nla"]
        nlo = misc["nlo"]
    #ヘッダのdglaの有効桁数違いで地理院プログラムと微小な差異があったので、より計算値に近づける
    dgla = math.floor(dgla * (nla - 1)) / (nla - 1)
    dglo = math.floor(dglo * (nlo - 1)) / (nlo - 1)

#国土地理院のジオイドデータからPythonのデータを書きだして、次回から使えるようにします。
def createGeoidData():
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    f = open(os.path.join(os.getcwd(),GSI_GEOID_FILE_NAME), 'r')
    #f = open('gsigeo2011_ver2_1.asc', 'r')
    line = f.readline()
    #  20.00000 120.00000 0.016667 0.025000 1801 1201 1 ver2.1         
    linestr = '' + line
    linestr = linestr.strip() 
    header = linestr.split(" ")
    glamn = float(header[0])
    glomn = float(header[1])
    dgla = float(header[2])
    dglo = float(header[3])
    nla = int(header[4])
    nlo = int(header[5])

    geoid = {}
    la = 0
    lo = 0
    while line:
        line = f.readline()
        linestr = '' + line
        linestr = linestr.strip()
        g = linestr.split(" ")
        glen = len(g)
        for i in range(0, glen):
            if(g[i].strip() == ""):
                continue
            if(g[i]!='999.0000'):
                geoid[str(la) + "_" + str(lo)] = float(g[i])
            lo +=1
            if (lo == nlo):
                lo = 0
                la+=1
    
    f.close()

    fw = open('geoidData.py', 'w') # 書き込みモードで開く
    fw.writelines('def setGeoid():\n')
    #geoid = [[999] * 1201 for i in range(1801)]
    fw.writelines('\tgeoid = {}\n')
    for la in range(0, nla):
        for lo in range(0, nlo):
            if(str(la) + "_" + str(lo) in geoid.keys()):
                fw.writelines('\tgeoid["' + str(la) + '_' + str(lo) + '"] = ' + str(geoid[str(la) + "_" + str(lo)]) + '\n')
    fw.writelines('\treturn geoid\n')
    fw.writelines('def setMiscData():\n')
    fw.writelines('\tmisc = {}\n')
    fw.writelines('\tmisc["glamn"] = ' + str(glamn) + '\n')
    fw.writelines('\tmisc["glomn"] = ' + str(glomn) + '\n')
    fw.writelines('\tmisc["dgla"] = ' + str(dgla) + '\n')
    fw.writelines('\tmisc["dglo"] = ' + str(dglo) + '\n')
    fw.writelines('\tmisc["nla"] = ' + str(nla) + '\n')
    fw.writelines('\tmisc["nlo"] = ' + str(nlo) + '\n')
    fw.writelines('\treturn misc\n')

    fw.close()
    
#緯度経度からジオイド値を求める
def getGeoidValue(lat, lon):
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    #囲う矩形を求める
    j = int(math.floor((lon - glomn) / dglo))
    i = int(math.floor((lat - glamn) / dgla))
    if( i < 0 or i >= nla or j < 0 or j >= nlo):
        #print('エラー：緯度経度が範囲外です')
        return 999.00

    if ((not (str(i)+"_"+str(j) in geoid.keys())) or (not (str(i)+"_"+str(j+1) in geoid.keys())) or (not (str(i+1)+"_"+str(j) in geoid.keys())) or (not (str(i+1)+"_"+str(j+1) in geoid.keys()))):
        return 999.00
    wlon = glomn + j * dglo
    elon = glomn + (j+1) * dglo
    slat = glamn + i * dgla
    nlat = glamn + (i+1) * dgla

    t = (lat - slat) / (nlat - slat)
    u = (lon - wlon) / (elon - wlon)

    Z = (1 - t) * (1 - u) * geoid[str(i)+"_"+str(j)] + (1 - t) * u * geoid[str(i)+"_"+str(j+1)] + t * (1 - u) * geoid[str(i+1)+"_"+str(j)] + t * u * geoid[str(i+1)+"_"+str(j+1)]
    Z = Z * 100000
    Z = math.floor(Z + 0.5)
    Z = Z / 100000
    return Z

#CSVファイル中の高さ(楕円体高)カラムを標高値に置き換えて出力します
def convertCSV(infile, outfile):
    global geoid
    #header check
    f = open(infile, 'r')
    header = f.readline().lower()
    if((('latitude' in header) and ('longitude' in header) and ('altitude' in header)) or (('lat' in header) and (('long' in header) or ('lon' in header) or ('lng' in header)) and ('alt' in header))):
        startRow=1
    else:
        #read one more line
        header = f.readline()
        startRow=2
    header = header.strip()
    f.close()

    #区切り文字の推測
    delimChar = ''
    if(delimChar==''):
        headers = header.split(",")
        if(len(headers)>2):
            delimChar = ','
    if(delimChar==''):
        headers = header.split("\t")
        if(len(headers)>2):
            delimChar = '\t'
    if(delimChar==''):
        headers = header.split(" ")
        if(len(headers)>2):
            delimChar = ' '
    if(delimChar==''):
        print('区切り文字が不明です。処理できません。')

    #高さカラムの特定
    altCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='z'):
            altCol = col
        elif(colstr=='alt'):
            altCol = col
        elif(colstr=='altitude'):
            altCol = col
        elif(colstr=='z/altitude'):
            altCol = col
        elif(('altitude' in colstr) and ('z' in colstr)):
            altCol = col

    #緯度カラムの特定
    latCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='latitude'):
            latCol = col
        elif(colstr=='lat'):
            latCol = col
        elif(('latitude' in colstr) and ('y' in colstr)):
            latCol = col

    #経度カラムの特定
    lonCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='longitude'):
            lonCol = col
        elif(colstr=='lng'):
            lonCol = col
        elif(colstr=='lon'):
            lonCol = col
        elif(colstr=='long'):
            lonCol = col
        elif(('longitude' in colstr) and ('x' in colstr)):
            lonCol = col
    #カラムが特定できない時はエラー
    if(altCol==-1 or lonCol==-1 or latCol==-1):
        print('列が不明です。処理できません。')
        exit()

    #CSV処理
    hasInvalid = False
    with open(infile, 'r') as fin, open(outfile, 'w') as fout:
        #CSV Reader
        reader = csv.reader(fin, delimiter=delimChar)
        
        #ヘッダをそのままコピー
        for row in range(0,startRow):
            fout.writelines(delimChar.join(next(reader))+'\n')
        
        #各行の処理
        for row in reader:
            EllapsoidHeight = float(row[altCol])
            lat = float(row[latCol])
            lon = float(row[lonCol])
            geoidval = getGeoidValue(lat,lon)
            elevation = EllapsoidHeight - geoidval  #標高＝楕円体高-ジオイド高
            if(geoidval==999.00):
                #ジオイド値が正常に取得できない
                elevation = 999999
                hasInvalid = True 
            row[altCol] = "{0:.3f}".format(elevation)   #高さカラムを差し替え
            fout.writelines(delimChar.join(row)+'\n')   #出力
    if(hasInvalid):
        print('ジオイドの取得に失敗したデータがあります。確認ください。該当するデータは標高を 999999 にしています。')
    else:
        print('処理を正常に終了しました')


#main
def main():
    args = sys.argv

    #引数とファイルの存在チェック
    if(len(args)!=3):
        print('エラー:引数が不正です')
        print('例：EllapsoidToElevation.py 入力CSVファイル 出力CSVファイル')
        return
    filein = args[1]
    fileout = args[2]
    if (os.path.exists(filein) == False):
        print('エラー', '入力ファイルが存在していません。')
        return
    if (os.path.exists(fileout) == True):
        print('エラー:出力先ファイルは存在しています。上書きできません')    
        return

    #ジオイド情報の取得
    getGeoidData()

    #CSVファイルの高さ情報からジオイド高を引いたものを複製する
    convertCSV(filein, fileout)

#実行
main()







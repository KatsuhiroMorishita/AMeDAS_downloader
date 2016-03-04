#! ruby -Ku       # UTF-8の使用を宣言
#########################################################
=begin
気象庁のWEBサイトへアクセスして、prec番号の一覧を取得するスクリプトです。
元ネタ：http://www32.atwiki.jp/bioeos/m/pages/132.html
改造： K. Morishita @ 2012-11-16
history: 2015-08-19 Ruby2.2.0で動かなくなっていたので改造した。動作がなんだか遅い・・・。
=end
#########################################################
#require "kconv"   # UTF-8に関して: http://www.rubylife.jp/ini/japan/index5.html
require 'open-uri'

out_file = "csv_all.txt"
out = open(out_file, "w:UTF-8")

v = []                                            # 配列の初期化
file = "prec_no.txt"
open(file, "r:UTF-8").each do |liner|
  #p liner
  #printf(Kconv.tosjis("\n\n" + liner.strip() + "\n"))
  field = liner.strip().split(",")
  department = field[0]
  proc_no = field[1]
  p proc_no
  open("http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no=" + proc_no.to_s, "r:UTF-8") {|f|
    f.each_line {|line|
      #p line.encode("UTF-8")
      if %r|'.','\d+','.+','.+','-?\d\d','\d\d.\d','\d\d\d','\d\d.\d','\d+'| =~ line
        line.scan(%r|'.','\d+','.+','.+','-?\d\d','\d\d.\d','\d\d\d','\d\d.\d','\d+'|){|matche|
          matching = matche.delete("'")
          v = matching.chop.split(",")
          #printf(Kconv.tosjis(matching + "\n"))
          a = (v[7].to_f / 60).to_f
          degree_lon = (v[6].to_f + a)
          b = (v[5].to_f / 60).to_f
          degree_lat = (v[4].to_f + b)
          out.printf "%s,%s,%s,%.5f,%.5f\n", department, proc_no, matching, degree_lon, degree_lat
        }
      elsif %r|'.','\d+','.+','.+','-?\d\d','\d\d.\d','\d\d\d','\d\d.\d','\d+.\d+'| =~ line
        line.scan(%r|'.','\d+','.+','.+','-?\d\d','\d\d.\d','\d\d\d','\d\d.\d','\d+.\d'|){|matche|
          matching = matche.delete("'")
          v = matching.chop.split(",")
          #printf(Kconv.tosjis(matching + "\n"))
          a = (v[7].to_f / 60).to_f
          degree_lon = (v[6].to_f + a)
          b = (v[5].to_f / 60).to_f
          degree_lat = (v[4].to_f + b)
          out.printf "%s,%s,%s,%.5f,%.5f\n", department, proc_no, matching, degree_lon, degree_lat
        }
      end
    }
  }
end
###################################################################
=begin
v[0] = a or s
v[1] = block_no
v[2] = 漢字名
v[3] = カナ名
v[4] = 緯度(度)
v[5] = 緯度(分)
v[6] = 経度(度)
v[7] = 経度(分)
v[8] = 標高
=end
################################################################################
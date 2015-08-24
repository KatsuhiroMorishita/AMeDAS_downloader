# http://www32.atwiki.jp/bioeos/m/pages/132.html?guid=on
out_file = "prec_no.txt"
out = open(out_file,"w")
require 'open-uri'                      #"open-uri"はHPのソースを読み込むもの
open("http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture00.php?prec_no=&prec_ch=&block_no=&block_ch=&year=&month=&day=&elm=&view=") {|f|
  f.each_line {|line|
    if line.scan(/prec_no=\d+/){|matche|
      matching = matche.delete('prec_no=')
      puts matching
      out.printf "%s\n",matching
    }
    end
  }
}
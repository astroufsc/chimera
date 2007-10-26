
set title "Periodic Error for LNA's Meade 16\""
set xlabel "RA Worm Phase (s)"

set grid

set term png medium color
set ylabel "Accumulated Offset (arcsec)"
set output "lna-pec-accum.png"
plot "pec.ra" using 2:5 title "RA" w lines

set term postscript
set output "lna-pec-accum.ps"
replot

set term png medium color
set output "lna-pec-raw.png"
set ylabel "Offset (arcsec)"
plot "pec.ra" using 2:4 title "RA" w lines

set term postscript
set output "lna-pec-raw.ps"
replot

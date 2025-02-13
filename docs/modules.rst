#  for i in chimera*; do echo $i":" $(tokei -C -t python $i | grep Python | awk '{print $3}'); done | pbcopy

# core

- chimera: 21719

# controllers

- chimera-autoalign: 682
- chimera-autofocus: 557
- chimera-autoguider: 229
- chimera-autopierchange: 85
- chimera-domeflat: 274
- chimera-domesync: 865
- chimera-eventscript: 65
- chimera-filterfocus: 65
- chimera-headers-cefca: 213
- chimera-headers: 213
- chimera-pverify: 311
- chimera-qc: 282
- chimera-skyflat: 554
- chimera-supervisor: 8145
- chimera-too: 6020

# drivers

- chimera-aagcloudwatcher: 227
- chimera-apogee: 454
- chimera-ascom: 919
- chimera-astelco: 3181
- chimera-avt: 28
- chimera-bisque: 635
- chimera-commandersk: 764
- chimera-ctioenviroment: 625
- chimera-energenieswitch: 76
- chimera-fakepolarimeter: 103
- chimera-fli: 421
- chimera-jmismart232: 236
- chimera-lna: 715
- chimera-meade: 1119
- chimera-optec: 353
- chimera-sbig: 2632
- chimera-schneiderotb: 85
- chimera-sonoff: 68
- chimera-t80cam: 2354
- chimera-vaisala: 167

# ui

- chimera-gui: 1536
- chimera-stellarium: 159
- chimera-t80stelops: 377
- chimera-webadmin: 132
- chimera-xephem: 135

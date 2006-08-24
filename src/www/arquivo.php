<?php

// UTS-www - Interface web para o UTS
// Copyright (C) 2003-2005 P. Henrique Silva <ph.silva@gmail.com>
//
// This file is part of UTS-www.
// UTS-www is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or
// (at your option) any later version.
//
// UTS-www is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software
// Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
//

?><?php

session_start();

if(!$_SESSION['user']) {
        session_destroy();
        Header("Location: index.php");
}

clearstatcache();

require_once("root.php");

require_once(UTS."lib/utils.php");

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: Arquivo</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
</head>
<body>
<div align="center">
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<p>&nbsp;</p>
<div class="ajuda">
<p>As imagens tamb&eacute;m podem ser otidas <a style=
"color: black; text-decoration: underline" href=
"data/<?=$_SESSION['user']?>/<?=$_SESSION['inicio']?>">aqui</a>.</p>
</div>
<br>
<br>
<!--
<div class="ajuda" style="padding: 5px">
<p><b>Visualização</b><br>Para melhor visualização <a style="color: black; text-decoration: underline" href="doc/ajuste_monitor.php">ajuste seu monitor</a>, e escolha o tipo de visualização mais adequado ao objeto que foi observado. Se, mesmo assim a visualização não for convincente, use o <a style="color: black; text-decoration: underline" href="http://www.astro.ufsc.br/~henrique/bip">BIP</a> ou o <a style="color: black; text-decoration: underline" href="http://hea-www.harvard.edu/RD/ds9/">DS9</a>.</p>
</div>
-->
<table width="70%" border="0" class="tabela-home">
<tr bgcolor="#666666" class="tabelaH">
<td>Arquivo</td>
<td>Tamanho</td>
<td>Visualizar</td>
<td>Download</td>
</tr>
<?php

$dir = $_SESSION['bf_fullpath'];

if (file_exists($dir)) {
  $dh  = opendir($dir);

  while (false !== ($filename = readdir($dh))) {
    if(is_file($_SESSION['bf_fullpath']."/".$filename) && is_readable($_SESSION['bf_fullpath']."/".$filename))
      $files[] = $filename;
  }
}

if(!count($files)) {

?>
<tr class="tabelaOn">
<td colspan="5" align="center">Nenhum objeto na lista</td>
</tr>
<?php

} else {

   for ($i = 0; $i < count($files); $i++) {
     $stat = stat($_SESSION['bf_fullpath'] . "/" . $files[$i]);

        if($i % 2) {

?>
<tr class="tabelaOn"><?php
        } else {
?></tr>
<tr class="tabelaOff"><?php
        }
?>
<td><?=$files[$i]?>
</td>
<td><?=byte_format($stat['size'])?>
</td>
<td align="center"><a class="arquivo" href=
"display.php?filename=<?=$files[$i]?>">:: visualizar
::</a></td>
<td align="center"><a class="arquivo" href=
"download.php?filename=<?=$files[$i]?>">:: download ::</a></td>
</tr>
<?php
  }
}
?></table>
<p>&nbsp;</p>
<p align="center"><a href="home.php">::: voltar :::</a></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
</div>
</body>
</html>

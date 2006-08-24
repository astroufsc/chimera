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

require_once("root.php");

require_once(UTS."lib/utils.php");
require_once(UTS."lib/erro.php");

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: P&aacute;gina
principal</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
</head>
<body>
<div align="center">
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<p><?=strftime("%d/%m/%Y %H:%M:%S", time())?>
</p>
<br>
<p><a href="formApontar.php">::: apontar e integrar :::</a></p>
<p><a href="status.php">::: estado da observa&ccedil;&atilde;o
:::</a></p>
<p><a href="sky.php">::: ver o c&eacute;u :::</a></p>
<p><a href="arquivo.php">::: arquivo :::</a></p>
<?php if($_SESSION['root']) { ?>
<p><a href="formOpcoes.php">::: op&ccedil;&otilde;es :::</a></p>
<?php } ?><br>
<?= dumpError(); ?>
<table width="70%" border="0" class="tabela-home">
<tr class="tabelaH">
<td>#</td>
<td>Objeto</td>
<td>RA</td>
<td>DEC</td>
<td>Tempo de exposi&ccedil;&atilde;o</td>
<td>N&uacute;mero de exposi&ccedil;&otilde;es</td>
<td>Filtro</td>
</tr>
<?php

if(!count($_SESSION['log'])) {

?>
<tr class="tabelaOn">
<td colspan="7" align="center">Nenhum objeto na lista</td>
</tr>
<?php

} else {

   for ($i = 0; $i < count($_SESSION['log']); $i++) {
        if($i % 2) {

?>
<tr class="tabelaOn"><?php
        } else {
?></tr>
<tr class="tabelaOff"><?php
        }

        $qs  = "formApontar.php?obj=" . $_SESSION['obj'][$i] . "&epoca=J2000" . "&ra=" . $_SESSION['ra'][$i];
        $qs .= "&dec=" . $_SESSION['dec'][$i] . "&num_exp=" . $_SESSION['num_exp'][$i] . "&exp_time=";
        $qs .= $_SESSION['exp_time'][$i] . "&filtro=" . $_SESSION['filter'][$i];


?>
<td><a title="Repetir observa&ccedil;&atilde;o" style=
"color: red; text-decoration: underline" href="<?=$qs?>">
<?=$i+1?>
</a></td>
<td><?=$_SESSION['obj'][$i]?>
</td>
<td><?=$_SESSION['ra'][$i]?>
</td>
<td><?=$_SESSION['dec'][$i]?>
</td>
<td><?=$_SESSION['exp_time'][$i]?>
</td>
<td><?=$_SESSION['num_exp'][$i]?>
</td>
<td><?=$_SESSION['filter'][$i]?>
</td>
</tr>
<?php
  }
}
?></table>
<p>&nbsp;</p>
<p><a href="logout.php">:: sair :::</a></p>
<p>&nbsp;</p>
<p>&nbsp;</p>
</div>
<?php

  if ($_GET['debug']) {
    dumpSession();
  }

?>
</body>
</html>

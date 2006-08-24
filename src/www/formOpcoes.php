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
require_once(UTS."lib/erro.php");

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola :::
Op&ccedil;&otilde;es</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
</head>
<body>
<center>
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<h3>Op&ccedil;&otilde;es</h3>
</center>
<div class="ajuda">
<p>O nome &eacute; formado da seguinte forma:
<b>[nome_da_imagem]-[data]</b>. Os campos cercados por [ e ] podem
ser alterados pelo formul&aacute;rio abaixo.</p>
</div>
<form name="opcoes" action="opcoes.php" method="get" id="opcoes">
<input type="hidden" name="back" value=
"<?=$_SERVER['HTTP_REFERER']?>"> &gt;
<table align="center">
<tr>
<td class="tabelaH" colspan="2">Imagens e diret&oacute;rios</td>
</tr>
<?php
if($_GET['debug']) {
?>
<tr>
<td>Diret&oacute;rio padr&atilde;o:</td>
<td><input type="text" name="dir" maxlenght="256" size="50" class=
"txt" tabindex="1" value="<?=$_SESSION['bf_dir']?>"></td>
</tr>
<?php
}
?>
<tr>
<td>Nome da imagem:</td>
<td><input type="text" name="name" maxlenght="256" size="50" class=
"txt" tabindex="2" value="<?=$_SESSION['bf_name']?>"></td>
</tr>
<tr>
<td><a href="http://www.php.net/strftime">Formato da data</a>:</td>
<td><input type="text" name="index" maxlenght="256" size="50"
class="txt" tabindex="3" value=
"<?=$_SESSION['bf_index']?>"></td>
</tr>
<tr>
<td colspan="2">&nbsp;</td>
</tr>
<tr>
<td align="center">
<div align="left"></div>
</td>
<td align="center">
<div align="left"><input type="submit" name="get_now" value=
"Salvar" tabindex="4"></div>
</td>
</tr>
</table>
<p align="center"><a href="home.php">::: voltar :::</a></p>
</form>
</body>
</html>

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

require_once("root.php");
require_once(UTS."lib/erro.php");

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Observat&oacute;rios Virtuais ::: Entrar</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
<script src="js/jsval.js" type="text/javascript" language=
"javascript">
</script>
<script src="js/uts.js" type="text/javascript" language=
"javascript">
</script>
<script type="text/javascript" language="javascript">
        
        function initValidation() {

                var form = document.forms['instalacao'];
                
                form.uts_admin.required = 1;
                form.uts_admin.regexp = /^\w*$/;
                form.uts_admin.minlength = 6;
                form.uts_admin.maxlength = 40;
                form.uts_admin.realname = "administrador"

        }               

</script>
</head>
<body onload="initValidation();">
<p align="center"><img src="imagens/ovlogo.jpg" width="145" alt=
""><br>
<br></p>
<div class="ajuda"><big>Instala&ccedil;&atilde;o</big>
<p>Para instalar a interface, preencha os campos abaixo.
<b>TODOS</b> os campos s&atilde;o obrigat&oacute;rios.</p>
</div>
<br>
<?php

  if(!is_writable("config/uts.inc.php")) {
    $writable = 0;
?>
<div class="ajuda">
<p>Verifique a permis&atilde;o do diret&oacute;rio "<b>config</b>"!
&Eacute; necess&aacute;rio permiss&atilde;o para escrita neste
diret&oacute;rio.</p>
</div>
<?php
  } else {
    $writable = 1;
  }
?><?php dumpError(); ?>
<form name="instalacao" action="instalacao-action.php" method=
"post" onsubmit="return validateStandard(this, 'error');" id=
"instalacao">
<h2 style="text-align: center">UTS</h2>
<table align="center">
<tr>
<td>administrador</td>
<td><input type="text" name="uts_admin" maxlength="40" value=
"administrador"></td>
</tr>
<tr>
<td>senha</td>
<td><input type="password" name="uts_pass" maxlength="40"></td>
</tr>
</table>
<h2 style="text-align: center">MySQL</h2>
<table align="center">
<tr>
<td>servidor</td>
<td><input type="text" name="mysql_server" maxlength="40" value=
"localhost"></td>
</tr>
<tr>
<td>administrador</td>
<td><input type="text" name="mysql_admin" maxlength="40" value=
"root"></td>
</tr>
<tr>
<td>senha</td>
<td><input type="password" name="mysql_admin_pass" maxlength=
"40"></td>
</tr>
<!--
    <tr> 
      <td>banco de dados</td>
      <td> 
        <input type="text" name="mysql_db" maxlength="40" value="uts">
      </td>
    </tr>
    <tr> 
      <td>usuario</td>
      <td> 
        <input type="text" name="mysql_newuser" maxlength="40" value="uts">
      </td>
    </tr>
    <tr> 
      <td>senha</td>
      <td> 
        <input type="password" name="mysql_newuser_pass" maxlength="40">
      </td>
    </tr>
-->
<tr>
<td>&nbsp;</td>
<td><?php if ($writable) { ?><input type="submit" value="Instalar"
name="submit"> <?php } else { ?> Erro. Verifique as mensagens
acima. <?php } ?></td>
</tr>
</table>
</form>
<br>
<br>
<table width="770" border="0" cellspacing="10" cellpadding="0"
align="center">
<tr>
<td width="109">
<div align="center"><a href="http://www.inpe.br"><img src=
"imagens/inpelogo.jpg" width="50" border="0" alt="INPE"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">INPE</font></div>
</td>
<td width="121">
<div align="center"><a href="http://www.ufrgs.br"><img src=
"imagens/ufrgslogo.jpg" width="50" border="0" alt="UFRGS"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRGS</font></div>
</td>
<td width="125">
<div align="center"><a href="http://www.ufrj.br"><img src=
"imagens/ufrjlogo.jpg" width="50" border="0" alt="UFRJ"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRJ</font></div>
</td>
<td width="107">
<div align="center"><a href="http://www.ufrn.br"><img src=
"imagens/ufrnlogo.jpg" width="60" border="0" alt="UFRN"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRN</font></div>
</td>
<td width="122">
<div align="center"><a href="http://www.ufsc.br"><img src=
"imagens/ufsclogo.jpg" width="45" border="0" alt="UFSC"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFSC</font></div>
</td>
<td width="116">
<div align="center"><a href="http://www.usp.br"><img src=
"imagens/usplogo.jpg" width="60" border="0" alt="USP"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">USP</font></div>
</td>
</tr>
</table>
<table width="770" border="0" cellspacing="8" align="center">
<tr>
<td>
<div align="center"><font face=
"Verdana, Arial, Helvetica, sans-serif" size="2"><br>
<font size="3"><b>APOIO</b></font>:</font></div>
</td>
</tr>
</table>
<table width="770" border="0" cellspacing="8" align="center">
<tr>
<td width="23">
<div align="right"></div>
</td>
<td width="201">&nbsp;</td>
<td width="131">
<div align="center"><a href="http://www.vitae.org.br"><img src=
"imagens/vitaelogo.jpg" alt="VITAE" border="0"></a></div>
</td>
<td width="141">
<div align="center"><a href="http://www.cnpq.br"><img src=
"imagens/cnpqlogo.jpg" alt="CNPQ" border="0"></a></div>
</td>
<td width="177">&nbsp;</td>
<td width="29">&nbsp;</td>
</tr>
</table>
</body>
</html>

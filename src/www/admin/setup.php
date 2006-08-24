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
require_once(UTS."lib/db.php");

// checa se o administrador jah foi definido.

$sql = "SELECT * FROM setup";
$res =& $db->query($sql);

//echo $res->numRows();

if($res->numRows()) {

        Header("Location: index.php");

}

if($_GET['action'] == "setup") {

        extract($_POST);

        $sql = "INSERT INTO setup VALUES('" . trim($admin) . "', '" . md5(trim($admin_pass)) . "')";
        $res =& $db->query($sql);
        
        Header("Location: index.php");
}

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&#243;pios na Escola ::: Administra&#231;&#227;o :::
Setup</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="../css/uts.css" rel="stylesheet" type="text/css">
<script src="../js/jsval.js" type="text/javascript" language=
"javascript">
</script>
<script src="../js/uts.js" type="text/javascript" language=
"javascript">
</script>
<script type="text/javascript" language="javascript">
        
        function initValidation() {

                var form = document.forms['setup'];
                
                form.admin.required = 1;
                form.admin.regexp = /^\w*$/;
                form.admin.minlength = 6;
                form.admin.maxlength = 40;
                form.admin.realname = "usuário";
                form.admin.err = "Você deve digitar um nome de usuário válido.";

                form.admin_pass.required = 1;
                form.admin_pass.regexp = /^\w*$/;
                form.admin_pass.minlength = 6;
                form.admin_pass.maxlength = 40;
                form.admin_pass.realname = "senha";
                form.admin_pass.err = "Você deve digitar uma senha válida.";
        }               

</script>
</head>
<body onload="initValidation();">
<div id="titulo">Telesc&#243;pios na Escola</div>
<br>
<br>
<div style="text-align: center">
<h2>Instrucoes:</h2>
Digite abaixo o nome do usu&#225;rio que ir&#225; administrar o
sistema de agendamento. Este nome dever&#225; ter no m&#237;nicio 6
e no m&#225;ximo 40 caracteres. Nenhum caractere "estranho" &#233;
aceito (@#$%&amp;*), apenas letras (mai&#250;sculas e
min&#250;sculas s&#227;o tratadas de forma diferente) e
n&#250;meros. N&#227;o use acentua&#231;&#227;o. O mesmo vale para
a senha.</div>
<form name="setup" action="setup.php?action=setup" method="post"
onsubmit="return validateStandard(this, 'error');">
<table align="center">
<tr>
<td>usu&#225;rio</td>
<td><input type="text" name="admin" maxlenght="40"></td>
</tr>
<tr>
<td>senha</td>
<td><input type="password" name="admin_pass" maxlenght="40"></td>
</tr>
<tr>
<td>&nbsp;</td>
<td align="center"><input type="submit" value="Cadastrar" name=
"submit"></td>
</tr>
</table>
</form>
<br>
<br>
<br>
<table width="770" border="0" cellspacing="10" cellpadding="0"
align="center">
<tr>
<td width="109">
<div align="center"><a href="http://www.inpe.br"><img src=
"../imagens/inpelogo.jpg" width="50" height="63" border="0" alt=
"INPE"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">INPE</font></div>
</td>
<td width="121">
<div align="center"><a href="http://www.ufrgs.br"><img src=
"../imagens/ufrgslogo.jpg" width="50" height="63" border="0" alt=
"UFRGS"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRGS</font></div>
</td>
<td width="125">
<div align="center"><a href="http://www.ufrj.br"><img src=
"../imagens/ufrjlogo.jpg" width="50" height="63" border="0" alt=
"UFRJ"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRJ</font></div>
</td>
<td width="107">
<div align="center"><a href="http://www.ufrn.br"><img src=
"../imagens/ufrnlogo.jpg" width="60" height="63" border="0" alt=
"UFRN"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFRN</font></div>
</td>
<td width="122">
<div align="center"><a href="http://www.ufsc.br"><img src=
"../imagens/ufsclogo.jpg" width="45" height="63" border="0" alt=
"UFSC"></a><br>
<font face="Verdana, Arial, Helvetica, sans-serif" size=
"2">UFSC</font></div>
</td>
<td width="116">
<div align="center"><a href="http://www.usp.br"><img src=
"../imagens/usplogo.jpg" width="60" height="63" border="0" alt=
"USP"></a><br>
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
<table width="770" border="0" cellspacing="8" height="62" align=
"center">
<tr>
<td width="23">
<div align="right"></div>
</td>
<td width="201">&nbsp;</td>
<td width="131">
<div align="center"><a href="http://www.vitae.org.br"><img src=
"../imagens/vitaelogo.jpg" alt="VITAE" border="0"></a></div>
</td>
<td width="141">
<div align="center"><a href="http://www.cnpq.br"><img src=
"../imagens/cnpqlogo.jpg" alt="CNPQ" border="0"></a></div>
</td>
<td width="177">&nbsp;</td>
<td width="29">&nbsp;</td>
</tr>
</table>
</body>
</html>

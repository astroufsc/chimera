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

if(!$_SESSION['admin']) {
        session_destroy();
        Header("Location: index.php");
        exit(0);
}

require_once("root.php");
require_once(UTS."lib/db.php");
require_once(UTS."lib/erro.php");

if(isset($_GET['id'])) {

        $res =& $db->query("SELECT * FROM users WHERE id = " . intval($_GET['id']));

        if ( (!DB::isError($res)) && ($res->numRows()) )
                $res->fetchInto($data, DB_FETCHMODE_ASSOC);

}

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: Administra&ccedil;&atilde;o
::: Usu&aacute;rios</title>
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

                var form = document.forms['user'];

                form.nome.required = 1;
                form.nome.minlength = 1;
                form.nome.maxlength = 255;              
                form.nome.err = "Você deve digitar um nome (real) para o usuário.";

                form.username.required = 1;
                form.username.regexp = /^\w*$/;
                form.username.minlength = 6;
                form.username.maxlength = 40;
                form.username.realname = "usuário";
                form.username.err = "Você deve digitar um nome de usuário válido.";

                form.passwd.required = <?=$data ? 0: 1?>;
                form.passwd.regexp = /^\w*$/;
                form.passwd.minlength = 6;
                form.passwd.maxlength = 40;
                form.passwd.realname = "senha";
                form.passwd.err = "Você deve digitar uma senha válida.";
        }               

</script>
</head>
<body onload="initValidation();">
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<br>
<br>
<?php dumpError(); ?>
<form name="user" action="user-add.php" method="post" onsubmit="return validateStandard(this, 'error');" id="user">
<input type="hidden" name="id" value="<?=$data['id']?>">

<table class="formUser" align="center">
<tr>
<td>Nome</td>
<td><input type="text" name="nome" value="<?=$data['nome']?>"></td>
</tr>
<tr>
<td>Usuario</td>
<td><input type="text" name="username" value="<?=$data['username']?>"></td>
</tr>
<tr>
<td>Senha</td>
<td><input type="password" name="passwd"></td></tr>
<tr>
<td>Super-usu&aacute;rio?</td>
<td><input type="checkbox" name="root" value="1" <?php if($data['root'] == 1) { echo "checked"; } ?>></td>
</tr>
<tr>
<td colspan="2" align="center"><input type="submit" value="Enviar"></td>
</tr>
</table>
</form>

<?php if($data) { ?>
<hr noshade width="500">
<h2 align="center">Tempo alocado</h2>
<form name="addTime" action="time-add.php" method="post" id="addTime">
<input type="hidden" name="id" value="<?=$data['id']?>">

<table align="center">
<tr>
<td style="color: white;">In&iacute;cio</td>
<td>
<select name="inicio_dia">
<?php
for($i = 1; $i <= 31; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>
<select name="inicio_mes">
<?php

for($i = 1; $i <= 12; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>
<select name="inicio_ano">
<?php

for($i = 2005; $i <= 2007; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>

<select name="inicio_hora">
<?php

for($i = 0; $i <= 23; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>

<select name="inicio_min">
<?php

for($i = 0; $i <= 59; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>

</select>
</td>

<td rowspan="2"><input type="submit" value="Adicionar"</input></td>

</tr>

<tr>

<td style="color: white;">Fim</td>

<td>
<select name="fim_dia">
<?php

for($i = 1; $i <= 31; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>
<select name="fim_mes">
<?php

for($i = 1; $i <= 12; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>
<select name="fim_ano">
<?php

for($i = 2005; $i <= 2007; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>

<select name="fim_hora">
<?php

for($i = 0; $i <= 23; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>
</select>

<select name="fim_min">
<?php

for($i = 0; $i <= 60; $i++) {
?>
<option value="<?php printf("%02d", $i);?>"><?php printf("%02d", $i);?></option>
<?php
}
?>

</select>
</td>
</tr>
</table>
</form>
<hr noshade width="500">
<table class="listaTempo" align="center">
<tr>
<td></td>
</tr>
<tr class="tabelaH">
<td width="40%">Inicio</td>
<td width="40%">Fim</td>
<td>Opcoes</td>
</tr>
<?php


$res =& $db->query("SELECT * FROM user_sched WHERE user_id = " . $_GET['id'] . " ORDER BY inicio DESC");

if (DB::isError($res)) {
    die($res->getMessage());
}

if($res->numRows()) {

        $i = 0;
        while($res->fetchInto($row, DB_FETCHMODE_ASSOC)) {

                if($i % 2) {

?>
<tr class="tabelaOn"><?php
                } else {
?></tr>
<tr class="tabelaOff"><?php
                }
?>
<td><?=strftime("%d/%m/%Y %H:%M", $row['inicio'])?>
</td>
<td><?=strftime("%d/%m/%Y %H:%M", $row['fim'])?>
</td>
<td><a class="comando" href="time-del.php?id=<?=$row['id']?>&amp;user_id=<?=$row['user_id']?>"
onclick="return confirma('Deseja realmente remover?')">Remover</a></td>
</tr>
<?php

   $i++;

   }

} else {

?>
<tr class="tabelaOn">
<td colspan="3" align="center">Nenhum tempo alocado</td>
</tr>
<?php

}

$db->disconnect();

?></table>
<?php
// fim tempo alocado
}
?>

<div id="footer" style="text-align: center"><a href="home.php">Voltar</a> | <a href="logout.php">Sair</a></div>

</body>
</html>

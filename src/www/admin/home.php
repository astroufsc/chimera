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

$sql = "SELECT * FROM users";
$res =& $db->query($sql);

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: Administra&ccedil;&atilde;o
::: P&aacute;gina principal</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="../css/uts.css" rel="stylesheet" type="text/css">
<script src="../js/uts.js" type="text/javascript" language=
"javascript">
</script>
</head>
<body>
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<br>
<br>
<?php dumpError(); ?>
<div id="header" style="text-align: center;"><a href=
"user.php">Adicionar usu&aacute;rio</a> | <a href=
"change-pass.php">Alterar senha do Administrador</a></div>
<table width="50%" border="0" class="tabela-home" align="center">
<tr class="tabelaH">
<td>Nome</td>
<td>Usu&aacute;rio</td>
<td>Op&ccedil;&otilde;es</td>
</tr>
<?php

if($res->numRows()) {

        $i = 0;
        while($res->fetchInto($data, DB_FETCHMODE_ASSOC)) {

                if($i % 2) {

?>
<tr class="tabelaOn"><?php
                } else {
?></tr>
<tr class="tabelaOff"><?php
                }

?>
<td><?=$data['nome']?>
</td>
<td><?=$data['username']?>
</td>
<td><a class="comando" href=
"user.php?id=<?=$data['id']?>">Editar</a> | <a class="comando"
href="user-del.php?id=<?=$data['id']?>" onclick=
"return confirma('Deseja realmente remover o usu&aacute;rio `<?=$data['nome']?>`');">
Remover</a></td>
</tr>
<?php
        $i++;

        }

} else {

?>
<tr class="tabelaOn">
<td colspan="3" align="center">Nenhum usu&aacute;rio
cadastrado.</td>
</tr>
<?php

}
?></table>
<div id="footer" style="text-align: center;"><a href=
"logout.php">Sair</a></div>
</body>
</html>

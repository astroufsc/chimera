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
}

require_once("root.php");

require_once(UTS."lib/erro.php");
require_once(UTS."lib/db.php");

if($_GET['action'] == "setup") {

        $sql = "UPDATE setup SET admin_pass = '" . md5($_POST['admin_pass']) . "'";
        $res =& $db->query($sql);
        
        Header("Location: " . getMsg("home.php", "Senha alterada com sucesso."));

}

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
<link href="../css/uts.css" rel="stylesheet" type="text/css">
<script src="../js/jsval.js" type="text/javascript" language=
"javascript">
</script>
<script src="../js/uts.js" type="text/javascript" language=
"javascript">
</script>
<script type="text/javascript" language="javascript">
        
        function initValidation() {

                var form = document.forms['changePass'];
                
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
<p align="center"><img src="../imagens/ovlogo.jpg" width="145"
height="105"><br>
<br>
<br></p>
<form name="changePass" action="change-pass.php?action=setup"
method="post" onsubmit="return validateStandard(this, 'error');"
id="changePass"><input type="hidden" name="id" value=
"<?=$data['id']?>">
<table class="formUser" align="center">
<tr>
<td>Nova senha</td>
<td><input type="password" name="admin_pass" maxlenght="20"></td>
</tr>
<tr>
<td colspan="2" align="center"><input type="submit" value=
"Enviar"></td>
</tr>
</table>
</form>
<div id="footer" style="text-align: center"><a href=
"home.php">Voltar</a> | <a href="logout.php">Sair</a></div>
</body>
</html>

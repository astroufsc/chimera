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
require_once(UTS."lib/erro.php");

$sql = "SELECT * FROM setup";
$res =& $db->query($sql);

if(PEAR::isError($res)) {
        Header("Location: " .   getError("index.php", "Erro ao tentar acessar o banco de dados."));
        exit(0);
}

if(!$res->numRows()) {
        Header("Location: " . getError("index.php", "Usuário ou senha inválidos."));
        exit(0);
}

$res->fetchInto($data, DB_FETCHMODE_ASSOC);

if( ($_POST['admin'] == trim($data['admin'])) && (md5(trim($_POST['admin_pass'])) == $data['admin_pass']) ) {

        session_start();

        $_SESSION['admin'] = 1;
        $_SESSION['inicio'] = strftime("%Y%m%d-%H%M%Z", time());

        Header("Location: home.php");
        exit(0);

} else {

        Header("Location: " . getError("index.php", "Usuário ou senha inválidos."));
        exit(0);

}

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title></title>
</head>
<body>
</body>
</html>

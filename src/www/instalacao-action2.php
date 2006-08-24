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

error_reporting(E_ALL);

require_once("root.php");
require_once(UTS."lib/erro.php");
require_once(UTS."lib/pear/DB.php");

// make dsn
extract($_POST);
  
$dsn = "mysql://$mysql_admin:$mysql_admin_pass@$mysql_server";

function dbErr($res) {

  $err  = "<br>" . $res->getMessage() . " (" . $res->getCode() . "))<br>";
  $err .= nl2br($res->getUserInfo()) . "<br>";
  //  $err .= $res->getDebugInfo() . "";

  return $err;

}


$db =& DB::connect($dsn);

if(DB::isError($db)) {
  $err  = "Erro ao tentar conectar ao MySQL.<br>";
  $err .= "Verifique o nome do administrador e a senha.<br>";
  $err .= dbErr($db);

  Header("Location: " . getError("instalacao.php", $err));
  exit(0);
}

function back() {

//   global $db;

//   extract($_POST);

//   $sql  = "REVOKE ALL PRIVILEGES ON $mysql_db . * FROM $mysql_newuser@$mysql_server;";
//   $sql .= "DROP DATABASE $mysql_db;";
//   $sql .= "DELETE FROM `columns_priv` WHERE User = $mysql_newuser AND Host = $mysql_server;";
//   $sql .= "DELETE FROM `user` WHERE User = $mysql_newuser AND Host = $mysql_server;";
//   $sql .= "DELETE FROM `db` WHERE User = $mysql_newuser AND Host = $mysql_server;";
//   $sql .= "DELETE FROM `tables_priv` WHERE User = $mysql_newuser AND Host = $mysql_server;";
//   $sql .= "FLUSH PRIVILEGES;";

//   $db->query($sql);

}

// OK, we have a connection

dbsource("db/db-schema.sql", array($mysql_newuser,$mysql_newuser_pass@$mysql_server/$mysql_db";

$sql = file_get_contents("db/db-schema.sql");

$result = $db->query(mysql_real_escape_string($sql));

if(DB::isError($result)) {
  $err = "Erro ao tentar criar o banco de dados.<br>";
  $err .= dbErr($result);

  back();
  Header("Location: " . getError("instalacao.php", $err));
  exit(0);

}

// write configuration file


Header("Location: admin");

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

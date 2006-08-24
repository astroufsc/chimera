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
require_once(UTS."lib/utils.php");
require_once(UTS."lib/pear/DB.php");

// make dsn
extract($_POST);

// default values
$uts_mysql_db = "uts";
$uts_mysql_user = "uts";
$uts_mysql_user_pass = "utspass";
  
$dsn = "mysql://$mysql_admin:$mysql_admin_pass@$mysql_server";

function dbErr($res) {

  //$err  = "<br>" . $res->getMessage() . " (" . $res->getCode() . "))<br>";
  //  $err .= nl2br($res->getUserInfo()) . "<br>";
  //  $err .= $res->getDebugInfo() . "";

  //return $err;

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

// // create user
// $sql = "GRANT USAGE ON * . * TO '$mysql_newuser'@'localhost' IDENTIFIED BY '$mysql_newuser_pass' WITH MAX_QUERIES_PER_HOUR 0 MAX_CONNECTIONS_PER_HOUR 0 MAX_UPDATES_PER_HOUR 0";

// $result = $db->query($sql);

// if(DB::isError($result)) {
//   $err = "Erro ao tentar criar o usu√rio.<br>";
//   $err .= dbErr($result);

//   $err .= "(" . $result->getMessage() . " (" . $db->getCode() . "))<br>";
//   $err .= "(" . $result->getUserInfo() . ")<br>";

//   back();
//   Header("Location: " . getError("instalacao.php", $err));
//   exit(0);

// }

// create database
$sql = "CREATE DATABASE $uts_mysql_db";
$result = $db->query($sql);

if(DB::isError($result)) {
  $err = "Erro ao tentar criar o banco de dados.<br>";
  $err .= dbErr($result);

  back();
  Header("Location: " . getError("instalacao.php", $err));
  exit(0);

}

// // grant user privileges
// $sql = "GRANT SELECT , INSERT , UPDATE , DELETE , CREATE , DROP , INDEX , ALTER ON `$mysql_db` . * TO '$mysql_newuser'@'$mysql_server'";

// $result = $db->query($sql);

// if(DB::isError($result)) {
//   $err = "Erro ao tentar criar o usu√rio.<br>";
//   $err .= dbErr($result);

//   back();
//   Header("Location: " . getError("instalacao.php", $err));
//   exit(0);

// }

// // flush privileges
// $sql = "FLUSH PRIVILEGES";
// $result = $db->query($sql);

// // use the newly create database
// $sql = "USE '$mysql_db'";
// $result = $db->query($sql);

// if(DB::isError($result)) {
//   $err = "Erro ao tentar criar o banco de dados.<br>";
//   $err .= dbErr($result);

//   back();
//   Header("Location: " . getError("instalacao.php", $err));
//   exit(0);

// }

// connect as the newly create user
// $dsn = "mysql://$mysql_newuser:$mysql_newuser_pass@$mysql_server/$mysql_db";

$db->disconnect();
$dsn = "mysql://$mysql_admin:$mysql_admin_pass@$mysql_server/$uts_mysql_db";
$db =& DB::connect($dsn);

// if(DB::isError($db)) {
//   $err = "Erro ao tentar conectar ao MySQL.<br>";
//   $err .= "Verifique o nome do administrador e a senha.<br>";
//   $err .= dbErr($result);

//   Header("Location: " . getError("instalacao.php", $err));
//   exit(0);
// }


// fill-in the newly create database
dbsource("db/db-schema.sql", array("uts_mysql_user" => $uts_mysql_user,
                                   "uts_mysql_user_pass" => $uts_mysql_user_pass,
                                   "uts_mysql_server" => $mysql_server,
                                   "uts_mysql_db" => $uts_mysql_db));

dbsource("db/db-user.sql",  array("uts_mysql_user" => $uts_mysql_user,
                                   "uts_mysql_user_pass" => $uts_mysql_user_pass,
                                   "uts_mysql_server" => $mysql_server,
                                   "uts_mysql_db" => $uts_mysql_db));

// write configuration file
// --

if (strtoupper(substr(PHP_OS, 0, 3)) == "WIN") {
  $os = "windows";
} else if(strtoupper(substr(PHP_OS, 0, 5)) == "LINUX") {
  $os = "linux";
}

$server_name = $_SERVER['SERVER_NAME'];

$config = <<<CONFIG
<?php

define("UTS_PLATFORM", "$os");

define("UTS_DEFAULT_SERVER", "$server_name");
define("UTS_DB_DSN", "mysql://$uts_mysql_user:$uts_mysql_user@$mysql_server/$uts_mysql_db");

define("UTS_SPMTABLE_PATH", "/usr/bin/spmtable");

define("UTS_POINTING_TIME", 70);
define("UTS_CCD_READ_TIME", 25);
define("UTS_STATUS_UPDATE_RATE", 5);

define("UTS_USER_SEQ", "jdfkajdfkasfu"); // random 
define("UTS_TIME_SEQ", "jpoopwoemfif"); // random 

define("UTS_ERR_SEED", "Tsiolkovsky");

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title></title>
</head>
<body>
CONFIG; // -- $fp = fopen("config/uts.inc.php", "w+"); fwrite($fp,
$config); fclose($fp); Header("Location: index.php"); ?>
</body>
</html>

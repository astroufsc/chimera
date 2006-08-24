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
require_once(UTS."lib/utils.php");
require_once(UTS."config/uts.inc.php");

updateFilename();

// gera arquivo

// touch HANDSHAKE file
@touch(UTS_WIN_SCRIPTS_DIR . "\\HANDSHAKE");

$str = "SlewToRaDec    , " . $_GET['ra'] . " " . $_GET['dec'] . "           , \r\n";

// guarda o log
$i = count($_SESSION['log']);
$filename = sprintf("%08d.txt", $i);

$fp = fopen(UTS_WIN_SCRIPTS_DIR . "\\$filename", "w+");
fwrite($fp, $str);
fclose($fp);

// log

$_SESSION['log'][$i] = "fila";
$_SESSION['ra'][$i] = $_GET['ra'];
$_SESSION['dec'][$i] = $_GET['dec'];
$_SESSION['num_exp'][$i] = $_GET['num_exp'];
$_SESSION['exp_time'][$i] = $_GET['exp_time'];
$_SESSION['filter'][$i] = $_GET['filtro'];
$_SESSION['start_time'][$i] = time();

Header("Location: home.php");

?>
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Observat&oacute;rios Virtuais ::: Apontar e Integrar</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="Paulo Henrique S. de Santana">
<link href="uts.css" rel="stylesheet" type="text/css">
</head>
<body>
<p align="center"><a href="home.php">::: voltar :::</a></p>
</body>
</html>

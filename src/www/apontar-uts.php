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

require_once(UTS."lib/db.php");
require_once(UTS."lib/erro.php");
require_once(UTS."lib/utils.php");
require_once(UTS."lib/Sec.php");

require_once(UTS."config/uts.inc.php");

if( (!$_SESSION['root']) && (!userAllowed($_SESSION['user_id'], $db)) ) {
        Header("Location: " . getMsg("home.php", "Voc&ecirc; n&atilde;o possu&iacute; tempo de observa&ccdeil;&atilde;o alocado, você poder&aacute; navegar por estas p&aacute;ginas, mas n&atilde;o poder&aacute; controlar o observat&oacute;rio."));
        exit(0);
}

// checa se as secretarias estao up
$servers = getServers(UTS_DEFAULT_SERVER);

if(!$servers) {
  Header("Location: " . getError("formApontar.php?" . $_SERVER['QUERY_STRING'], "O Observat&oacute;rio n&atilde;o est&aacute; dispon&iacute;vel. Consulte o respons&aacute;vel."));
  exit(0);
}

// checa se nao ha nenhuma exposicao em curso, caso haja volta para pagina anterior
$ccd = new CCD('status');
$ccd->setInteractive(FALSE);

if(!$ccd->connect()) {;
  Header("Location: " . getError("formApontar.php?" . $_SERVER['QUERY_STRING'], "O Observat&oacute;rio n&atilde;o est&aacute; dispon&iacute;vel. Consulte o respons&aacute;vel. (SERVER_FULL)"));
  exit(0);
}

$tel = new Tel('status');
$tel->setInteractive(FALSE);

if(!$tel->connect()) {
  Header("Location: " . getError("formApontar.php?" . $_SERVER['QUERY_STRING'], "O Observat&oacute;rio n&atilde;o est&aacute; dispon&iacute;vel. Consulte o respons&aacute;vel. (SERVER_FULL)"));
  exit(0);
}

$stat0 = $ccd->isBusy();
$stat1 = $tel->isBusy();

if($stat0 || $stat1) {
  $ccd->disconnect();
  $tel->disconnect();
  Header("Location: " . getError("formApontar.php?" . $_SERVER['QUERY_STRING'], "H&aacute; uma observa&ccdeil;&atilde;o em andamento.<br>Aguarde alguns instantes e tente novamente.<br>Para saber o quanto esperar, v&aacute; a p&aacute;gina <a style='color: black; text-decoration: underline' href='status.php'>Estado da Observação</a>"));
  exit(0);
}



$sync = new Sync();
$sync->setInteractive(FALSE);

if(!$sync->connect()) {
  Header("Location: " . getError("formApontar.php?" . $_SERVER['QUERY_STRING'], "O Observat&oacute;rio n&atilde;o est&aacute; dispon&iacute;vel. Consulte o respons&aacute;vel. (SERVER_FULL)"));
  exit(0);
}

// to serialize the process
$ccd = new CCD('status');
$ccd->setInteractive(FALSE);
$ccd->connect();

$tel = new Tel('status');
$tel->setInteractive(FALSE);
$tel->connect();


$ra = $_GET['ra_h'] . ":" . $_GET['ra_m'] . ":" . $_GET['ra_s'];
$dec = $_GET['dec_g'] . ":" . $_GET['dec_m'] . ":" . $_GET['dec_s'];

updateFilename(getcwd() . "/data", $_GET['obj'] ? $_GET['obj'] : "imagem", "%Y%m%d%H%M%S");

//$sync->setStatus("OBJECT", $_GET['obj']); FIXME
$sync->setStatus("RA", $ra);
$sync->setStatus("DEC", $dec);
$sync->setStatus("EPOCH", $_GET['epoca']);
$sync->setStatus("FILTER", $_GET['filtro']);
$sync->setStatus("EXPTIME", $_GET['exp_time']);
$sync->setStatus("NEXP", $_GET['num_exp']);
$sync->setStatus("BFNAME", $_SESSION['bf_fullname']);

// first slew
$sync->setStatus("TELSTART", "NOW");

// now wait for telescope to go offline

while($tel->isBusy()) {
  sleep(1);
}

// ok, now take a image
$sync->setStatus("CAMSTART", "NOW");


// ok
$ccd->disconnect();
$tel->disconnect();
$sync->disconnect();

// guarda o log
$i = count($_SESSION['log']);

$_SESSION['log'][$i] = "fila";
$_SESSION['obj'][$i] = $_GET['obj'];
$_SESSION['ra'][$i] = $ra;
$_SESSION['dec'][$i] = $dec;
$_SESSION['num_exp'][$i] = $_GET['num_exp'];
$_SESSION['exp_time'][$i] = $_GET['exp_time'];
$_SESSION['filter'][$i] = $_GET['filtro'];
$_SESSION['start_time'][$i] = time();

Header("Location: status.php");

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
</head>
<body>
<p align="center"><a href="home.php">::: voltar :::</a></p>
</body>
</html>

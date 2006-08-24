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

require_once(UTS."lib/utils.php");
require_once(UTS."lib/Sec.php");
require_once(UTS."lib/erro.php");

require_once(UTS."config/uts.inc.php");

// checa se as secretarias estao up
$servers = getServers(UTS_DEFAULT_SERVER);

if(!$servers) {
  Header("Location: " . getError("home.php", "O Observatório não está disponível. Consulte o responsável."));
  exit(-1);
}

$ccd = new CCD('status');
$ccd->setInteractive(0);
$ccd->connect();

$tel = new Tel('status');
$tel->setInteractive(0);
$tel->connect();

$stat0 = $tel->isBusy();
$stat1 = $ccd->isBusy();

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
<script type="text/javascript" src="js/uts.js">
</script><?php

if(!$stat0 && !$stat1) {

?>
<script type="text/javascript">
<!--

 showMessage("Observação conluída.\nAs imagens estão disponíveis na página 'Arquivo'.");

// -->
</script><?php
} else {
?>
<meta http-equiv="Refresh" content=
"<?=UTS_STATUS_UPDATE_RATE?>; <?=$_SERVER['REQUEST_URI']?>">
<?php
}

$tel->disconnect();
$ccd->disconnect();

?>
</head>
<body>
</body>
</html>

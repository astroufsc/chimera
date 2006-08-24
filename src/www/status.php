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
  Header("Location: " . getError("home.php?" . $_SERVER['QUERY_STRING'], "O Observatório não está disponível. Consulte o responsável."));
  exit(-1);
}

$ccd = new CCD('status');
$ccd->setInteractive(0);
$ccd->connect();

$tel = new Tel('status');
$tel->setInteractive(0);
$tel->connect();

$sync = new Sync('status');
$sync->setInteractive(0);
$sync->connect();

// primeira vez?
if(!count($_SESSION['log'])) {
  $primeiraVez = 1;
} else {
  $primeiraVez = 0;
}


// estima o tempo da observacao
// tempo = apontamento + num_exp(tempo_leitura + tempo_exposicao)
// so perde tempo com isso, se houver observacao em andamento
$stat0 = $tel->isBusy();
$stat1 = $ccd->isBusy();

if($stat0 || $stat1) {

  $nexp = intval($sync->getStatus("NEXP"));
  $exp_time = intval($sync->getStatus("EXPTIME"));

  $cte_ap = UTS_POINTING_TIME;
  $tempo_leitura = UTS_CCD_READ_TIME;

  $tempo = $cte_ap + (($tempo_leitura * $nexp) + ($nexp * $exp_time));

  $ocupado = 1;

} else {

  $tempo = 0;
  $ocupado = 0;

}

$format = "parseInt('%Y'),parseInt('%m'),parseInt('%d'),parseInt('%H'),parseInt('%M'),parseInt('%S')";
$agora = time();
$curr = count($_SESSION['log']) - 1;
$countdown = strftime($format, ($agora + $tempo) - ($agora - $_SESSION['start_time'][$curr]));


$sync->disconnect();
$tel->disconnect();
$ccd->disconnect()

?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<meta name="generator" content=
"HTML Tidy for Linux/x86 (vers 12 April 2005), see www.w3.org">
<title>Telesc&oacute;pios na Escola ::: Estado da
observa&ccedil;&atilde;o</title>
<meta http-equiv="Content-Type" content=
"text/html; charset=us-ascii">
<meta name="author" content="P. Henrique Silva">
<link href="css/uts.css" rel="stylesheet" type="text/css">
<script type="text/javascript" src="js/jscountdown.js">
</script>
<script type="text/javascript" src="js/uts.js">
</script>
<script type="text/javascript">
<!--

var count = new Countdown();

with (count) {
  tagID = "counter";
  setEventDate(<?=$countdown?>);
  onevent = afterevent = "Observação conluída. As imagens estão disponíveis na página 'Arquivo'";
}
addCountdown(count);

-->
</script>
</head>
<body onload="doCountdown()">
<div id="titulo">Telesc&oacute;pios na Escola</div>
<br>
<br>
<?php
if($primeiraVez || !$ocupado) {
?>
<div class="ajuda" id="first">
<p>N&atilde;o h&aacute; observa&ccedil;&otilde;es em andamento.</p>
</div>
<?php
}
?>
<div class="ajuda" id="warning"><big>A T E N &Ccedil; &Atilde;
O</big>
<p>Aguarde, a observa&ccedil;&atilde;o est&aacute; sendo
efetuada.</p>
</div>
<p><!--
<div class="ajuda" id="contador">
<p>Tempo estimado para o término: <span id="counter">00:00:00</span></p>
</div>
-->
<?php
if($ocupado) {
?> <iframe frameborder="0" src="getStatus.php" width="0" height="0"
scrolling="no"></iframe> <?php
}
?></p>
<div class="ajuda" id="status">
<p style="color: white">A seguinte observa&ccedil;&atilde;o
est&aacute; sendo efetuada:</p>
<p align="center"><?php

$i = count($_SESSION['log']) - 1;

?></p>
<table width="40%" class="tabela-home">
<tr class="tabelaH" align="center">
<td colspan="2" width="20%">Pedido #<?=$i+1?>
</td>
</tr>
<tr class="tabelaOn">
<td width="40%">RA</td>
<td><?=$_SESSION['ra'][$i]?>
</td>
</tr>
<tr class="tabelaOff">
<td>DEC</td>
<td><?=$_SESSION['dec'][$i]?>
</td>
</tr>
<tr class="tabelaOn">
<td>N&uacute;mero de exposi&ccedil;&otilde;es</td>
<td><?=$_SESSION['num_exp'][$i]?>
</td>
</tr>
<tr class="tabelaOff">
<td>Tempo de exposi&ccedil;&atilde;o</td>
<td><?=$_SESSION['exp_time'][$i]?>
</td>
</tr>
<tr class="tabelaOn">
<td>Filtro</td>
<td><?=$_SESSION['filter'][$i]?>
</td>
</tr>
</table>
</div>
<div style="text-align: center"><a href="arquivo.php">::: Arquivo
:::</a></div>
<p align="center"><a href="home.php">::: voltar :::</a></p>
<?php

if($ocupado) {

?><script type="text/javascript">
<!--
   showDiv('warning');
   showDiv('contador'); 
-->
</script><?php

}

?>
</body>
</html>
